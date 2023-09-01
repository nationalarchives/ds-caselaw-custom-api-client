import json
import logging
from typing import Any, Literal, Union, overload

import boto3
import botocore.client
import environ
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import CopySourceTypeDef, ObjectIdentifierTypeDef
from mypy_boto3_sns.client import SNSClient
from mypy_boto3_sns.type_defs import MessageAttributeValueTypeDef

env = environ.Env()


@overload
def create_aws_client(service: Literal["s3"]) -> S3Client:
    ...


@overload
def create_aws_client(service: Literal["sns"]) -> SNSClient:
    ...


def create_aws_client(service: Union[Literal["s3"], Literal["sns"]]) -> Any:
    aws = boto3.session.Session(
        aws_access_key_id=env("AWS_ACCESS_KEY_ID", default=None),
        aws_secret_access_key=env("AWS_SECRET_KEY", default=None),
    )
    return aws.client(
        service,
        endpoint_url=env("AWS_ENDPOINT_URL", default=None),
        region_name=env("PRIVATE_ASSET_BUCKET_REGION", default=None),
        config=botocore.client.Config(signature_version="s3v4"),
    )


def create_s3_client() -> S3Client:
    return create_aws_client("s3")


def create_sns_client() -> SNSClient:
    return create_aws_client("sns")


def uri_for_s3(uri: str) -> str:
    return uri.lstrip("/")


def generate_signed_asset_url(key: str) -> str:
    # If there isn't a PRIVATE_ASSET_BUCKET, don't try to get the bucket.
    # This helps local environment setup where we don't use S3.
    bucket = env("PRIVATE_ASSET_BUCKET", None)
    if not bucket:
        return ""

    client = create_s3_client()

    return str(
        client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": key}
        )
    )


def generate_docx_url(uri: str) -> str:
    key = f'{uri}/{uri.replace("/", "_")}.docx'

    return generate_signed_asset_url(key)


def generate_pdf_url(uri: str) -> str:
    key = f'{uri}/{uri.replace("/", "_")}.pdf'

    return generate_signed_asset_url(key)


def delete_from_bucket(uri: str, bucket: str) -> None:
    client = create_s3_client()
    response = client.list_objects(Bucket=bucket, Prefix=uri)

    if response.get("Contents"):
        objects_to_delete: list[ObjectIdentifierTypeDef] = [
            {"Key": obj["Key"]} for obj in response.get("Contents", [])
        ]
        client.delete_objects(
            Bucket=bucket,
            Delete={
                "Objects": objects_to_delete,
            },
        )


def publish_documents(uri: str) -> None:
    """
    Copy assets from the unpublished bucket to the published one.
    Don't copy parser logs and package tar gz.
    TODO: consider refactoring with copy_assets
    """
    client = create_s3_client()

    public_bucket = env("PUBLIC_ASSET_BUCKET")
    private_bucket = env("PRIVATE_ASSET_BUCKET")

    response = client.list_objects(Bucket=private_bucket, Prefix=uri)

    for result in response.get("Contents", []):
        key = str(result["Key"])

        if not key.endswith("parser.log") and not key.endswith(".tar.gz"):
            source: CopySourceTypeDef = {"Bucket": private_bucket, "Key": key}
            extra_args = {"ACL": "public-read"}
            try:
                client.copy(source, public_bucket, key, extra_args)
            except botocore.client.ClientError as e:
                logging.warning(
                    f"Unable to copy file {key} to new location {public_bucket}, error: {e}"
                )


def unpublish_documents(uri: str) -> None:
    delete_from_bucket(uri, env("PUBLIC_ASSET_BUCKET"))


def delete_documents_from_private_bucket(uri: str) -> None:
    delete_from_bucket(uri, env("PRIVATE_ASSET_BUCKET"))


def notify_changed(uri: str, status: str, enrich: bool = False) -> None:
    client = create_sns_client()

    message_attributes: dict[str, MessageAttributeValueTypeDef] = {}
    message_attributes["update_type"] = {
        "DataType": "String",
        "StringValue": status,
    }
    message_attributes["uri_reference"] = {
        "DataType": "String",
        "StringValue": uri,
    }
    if enrich:
        message_attributes["trigger_enrichment"] = {
            "DataType": "String",
            "StringValue": "1",
        }

    client.publish(
        TopicArn=env("SNS_TOPIC"),
        Message=json.dumps({"uri_reference": uri, "status": status}),
        Subject=f"Updated: {uri} {status}",
        MessageAttributes=message_attributes,
    )


def copy_assets(old_uri: str, new_uri: str) -> None:
    """
    Copy *unpublished* assets from one path to another,
    renaming DOCX and PDF files as appropriate.
    """
    client = create_s3_client()
    bucket = env("PRIVATE_ASSET_BUCKET")
    old_uri = uri_for_s3(old_uri)
    new_uri = uri_for_s3(new_uri)

    response = client.list_objects(Bucket=bucket, Prefix=old_uri)

    for result in response.get("Contents", []):
        old_key = str(result["Key"])
        new_key = build_new_key(old_key, new_uri)
        if new_key is None:
            continue
        try:
            source: CopySourceTypeDef = {"Bucket": bucket, "Key": old_key}
            client.copy(source, bucket, new_key)
        except botocore.client.ClientError as e:
            logging.warning(
                f"Unable to copy file {old_key} to new location {new_key}, error: {e}"
            )


def build_new_key(old_key: str, new_uri: str) -> str:
    """Ensure that DOCX and PDF filenames are modified to reflect their new home
    as we get the name of the new S3 path"""
    old_filename = old_key.rsplit("/", 1)[-1]

    if old_filename.endswith(".docx") or old_filename.endswith(".pdf"):
        new_filename = new_uri.replace("/", "_")
        return f"{new_uri}/{new_filename}.{old_filename.split('.')[-1]}"
    else:
        return f"{new_uri}/{old_filename}"
