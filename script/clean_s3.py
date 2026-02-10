#!/usr/bin/env python3
"""
Bulk process all documents in unpublished bucket and republish to published bucket.
"""

import json
import os
import time
import warnings
from collections import defaultdict
from datetime import datetime
from typing import Any, Iterable

import boto3
from dotenv import load_dotenv

from caselawclient.models.utilities.aws import publish_documents
from caselawclient.types import DocumentURIString

load_dotenv(".env.staging")
# Configuration

UNPUBLISHED_BUCKET = os.environ["UNPUBLISHED_BUCKET"]
PUBLISHED_BUCKET = os.environ["PUBLISHED_BUCKET"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
CHECK_INTERVAL_SECONDS = int(os.environ.get("CHECK_INTERVAL_SECONDS", 30))
MAX_WAIT_MINUTES = int(os.environ.get("MAX_WAIT_MINUTES", 60))
DRY_RUN = bool(os.environ["DRY_RUN"])
MAX_DOCUMENTS: int | None = int(os.environ.get("MAX_DOCUMENTS", default=-1) or -1)
MAX_DOCUMENTS = MAX_DOCUMENTS if MAX_DOCUMENTS != -1 else None

S3_CLIENT = boto3.client("s3", region_name="eu-west-2")
SNS_CLIENT = boto3.client("sns", region_name="eu-west-2")


def paginated_bucket(bucket_name) -> Iterable[str]:
    paginator = S3_CLIENT.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            yield obj["Key"]


def extract_uri_from_key(key: str) -> str | None:
    parts = key.split("/")
    if len(parts) < 2:
        return None

    return "/".join(parts[:-1])


def should_process_file(key: str, has_docx: bool) -> bool:
    extension = key.rpartition(".")[-1].lower()
    if extension in ("pdf",):
        return not has_docx
    # explicitly exclude parser.log and TDR tar.gz files
    if extension in ("gz", "log"):
        return False
    if extension in ("png", "jpeg", "jpg", "docx"):
        return True
    warnings.warn(f"{key} has unexpected extension {extension}, skipping by default")
    return False


def get_document_uris_and_files(bucket_name: str) -> dict[str, dict]:
    print(f"\n=== Analyzing bucket structure: {bucket_name} ===")

    uri_data: dict[str, Any] = defaultdict(lambda: {"has_docx": False, "files": []})
    for key in paginated_bucket(bucket_name):
        uri = extract_uri_from_key(key)

        if uri:
            uri_data[uri]["files"].append(key)
            if key.endswith(".docx"):
                uri_data[uri]["has_docx"] = True

    print(f"  Found {len(uri_data)} document URIs")

    with_docx_count = sum(1 for d in uri_data.values() if d["has_docx"])
    without_docx_count = len(uri_data) - with_docx_count
    print(f"  - {with_docx_count} with DOCX (will process: DOCX, PNG, JPEG)")
    print(f"  - {without_docx_count} without DOCX (will process: PDF, PNG, JPEG)")

    return dict(uri_data)


def get_published_uris_needing_processing(bucket_name: str) -> tuple[set[str], set[str]]:
    all_uris = set()
    uris_needing_processing = set()

    count_entirely_ignored = 0
    counted_twice = 0
    count_already_done = 0
    count_needs_processing = 0

    for key in paginated_bucket(bucket_name):
        uri = extract_uri_from_key(key)

        if not uri or key.endswith(".tar.gz") or key.endswith("parser.log"):
            count_entirely_ignored += 1
            continue

        all_uris.add(uri)

        if uri in uris_needing_processing:
            counted_twice += 1
            continue

        try:
            tag_response = S3_CLIENT.get_object_tagging(Bucket=bucket_name, Key=key)
            tags = {tag["Key"]: tag["Value"] for tag in tag_response.get("TagSet", [])}

            if "DOCUMENT_PROCESSOR_VERSION" not in tags:
                uris_needing_processing.add(uri)
                count_needs_processing += 1
            else:
                count_already_done += 1

        except Exception as e:
            warnings.warn(f"  Warning: Error checking {key}: {e}. Not processed.")

    print(f"  Found {len(all_uris)} published document URIs")
    print(f"  Already processed (skipping): {count_already_done}")
    print(f"  Need processing: {len(uris_needing_processing)}")

    return uris_needing_processing, all_uris


def trigger_processing(bucket_name: str, published_uris: set[str]) -> dict[str, list[str]]:
    print(f"\n=== Step 1: Triggering processing for {bucket_name} ===")

    uri_data = get_document_uris_and_files(bucket_name)

    uri_files_to_process = defaultdict(list)
    total_files = 0
    skipped_files = 0
    skipped_unpublished = 0
    queued_files = 0

    for uri, data in uri_data.items():
        if uri not in published_uris:
            skipped_unpublished += sum(1 for _ in data["files"])
            continue

        has_docx = data["has_docx"]

        for key in data["files"]:
            total_files += 1

            if should_process_file(key, has_docx):
                uri_files_to_process[uri].append(key)
                queued_files += 1

                s3_event = {
                    "Records": [
                        {
                            "eventID": "manual-batch-processing",
                            "s3": {"bucket": {"name": bucket_name}, "object": {"key": key}},
                        }
                    ]
                }

                if not DRY_RUN:
                    SNS_CLIENT.publish(
                        TopicArn=SNS_TOPIC_ARN, Message=json.dumps(s3_event), Subject=f"Batch processing: {key}"
                    )

                if queued_files % 100 == 0:
                    print(f"  Queued {queued_files} files...")
            else:
                skipped_files += 1

    if queued_files > 0 and queued_files % 100 != 0:
        print(f"  Queued {queued_files} files...")

    print("\nProcessing triggered:")
    print(f"  Total files in published documents: {total_files}")
    print(f"  Files queued for processing: {queued_files}")
    print(f"  Files skipped (processing logic): {skipped_files}")
    print(f"  Files skipped (not published): {skipped_unpublished}")
    print(f"  Unique document URIs to republish: {len(uri_files_to_process)}")

    return dict(uri_files_to_process)


def wait_for_processing(bucket_name: str, uri_files: dict[str, list[str]]) -> tuple[list[str], list[str]]:
    print("\n=== Step 2: Waiting for processing to complete ===")

    if DRY_RUN:
        print("DRY RUN: Skipping wait, assuming all would be processed")
        return list(uri_files.keys()), []

    start_time = time.time()
    max_wait_seconds = MAX_WAIT_MINUTES * 60

    processed_uris = set()

    while time.time() - start_time < max_wait_seconds:
        all_processed = True
        unprocessed_count = 0

        for uri, files in uri_files.items():
            if uri in processed_uris:
                continue

            uri_complete = True
            for key in files:
                try:
                    tag_response = S3_CLIENT.get_object_tagging(Bucket=bucket_name, Key=key)
                    tags = {tag["Key"]: tag["Value"] for tag in tag_response.get("TagSet", [])}

                    if "DOCUMENT_PROCESSOR_VERSION" not in tags:
                        uri_complete = False
                        unprocessed_count += 1
                        all_processed = False
                        break
                except Exception as e:
                    print(f"  Warning: Error checking {key}: {e}")
                    uri_complete = False
                    all_processed = False
                    break

            if uri_complete:
                processed_uris.add(uri)

        elapsed = int(time.time() - start_time)
        print(
            f"  [{elapsed}s] Processed: {len(processed_uris)}/{len(uri_files)} URIs, "
            f"Unprocessed files: {unprocessed_count}"
        )

        if all_processed:
            print(f"\nAll files processed successfully in {elapsed} seconds")
            return list(processed_uris), []

        time.sleep(CHECK_INTERVAL_SECONDS)

    failed_uris = [uri for uri in uri_files if uri not in processed_uris]
    print(f"\nTimeout reached after {MAX_WAIT_MINUTES} minutes")
    print(f"  Processed: {len(processed_uris)} URIs")
    print(f"  Failed/incomplete: {len(failed_uris)} URIs")

    return list(processed_uris), failed_uris


def republish_documents(processed_uris: list[str], all_published_uris: set[str]):
    print("\n=== Step 3: Republishing documents ===")

    if DRY_RUN:
        print(f"DRY RUN: Would republish {len(processed_uris)} documents")
        for i, uri in enumerate(processed_uris[:5], 1):
            print(f"  {i}. {uri}")
        if len(processed_uris) > 5:
            print(f"  ... and {len(processed_uris) - 5} more")
        return

    success_count = 0
    skipped_unpublished = 0
    failed_uris = []

    for i, uri in enumerate(processed_uris, 1):
        if uri not in all_published_uris:
            print(f"  [{i}/{len(processed_uris)}] Skipping {uri} (no longer published)")
            skipped_unpublished += 1
            continue

        try:
            print(f"  [{i}/{len(processed_uris)}] Publishing {uri}")
            publish_documents(DocumentURIString(uri))
            success_count += 1
        except Exception as e:
            print(f"    ✗ Failed to publish {uri}: {e}")
            failed_uris.append(uri)

        if i % 10 == 0:
            print(f"  Progress: {i}/{len(processed_uris)} ({success_count} successful)")

    print("\nPublishing complete:")
    print(f"  Successful: {success_count}")
    print(f"  Skipped (unpublished during processing): {skipped_unpublished}")
    print(f"  Failed: {len(failed_uris)}")

    if failed_uris:
        print("\nFailed URIs:")
        for uri in failed_uris:
            print(f"  - {uri}")


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 60)
    print("Bulk Document Processing and Publishing")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'}")
    print(f"Unpublished Bucket: {UNPUBLISHED_BUCKET}")
    print(f"Published Bucket: {PUBLISHED_BUCKET}")
    print(f"SNS Topic: {SNS_TOPIC_ARN}")

    if DRY_RUN:
        print("DRY RUN MODE: No actual changes will be made")
        print("Set DRY_RUN = False to execute for real")
    else:
        print("\nLIVE MODE: This will process and republish all PUBLISHED documents!")
        print("Only documents currently in the published bucket will be processed.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    uris_to_process, all_published_uris = get_published_uris_needing_processing(PUBLISHED_BUCKET)

    if not uris_to_process:
        print("\nAll published documents are already processed!")
        print("=" * 60)
        return

    if MAX_DOCUMENTS is not None and len(uris_to_process) > MAX_DOCUMENTS:
        print(f"\nLimiting to {MAX_DOCUMENTS} documents (out of {len(uris_to_process)} needing processing)")
        uris_to_process = set(list(uris_to_process)[:MAX_DOCUMENTS])

    uri_files = trigger_processing(UNPUBLISHED_BUCKET, uris_to_process)

    processed_uris, failed_uris = wait_for_processing(UNPUBLISHED_BUCKET, uri_files)

    if failed_uris:
        print(f"\n{len(failed_uris)} URIs failed to process or timed out")
        response = input("Continue with republishing processed documents? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return

    if processed_uris:
        republish_documents(processed_uris, all_published_uris)

        processed_file = f"processed_uris_{timestamp}.txt"
        with open(processed_file, "w") as f:
            for uri in sorted(processed_uris):
                f.write(f"{uri}\n")
        print(f"\nProcessed URIs saved to: {processed_file}")
    else:
        print("\nNo documents to republish")

    print("\n" + "=" * 60)
    print("Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
