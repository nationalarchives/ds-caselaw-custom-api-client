import datetime
import json
import logging
import uuid
from typing import Any, Literal, Optional, TypedDict, overload

import boto3
import botocore.client
import environ
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import CopySourceTypeDef, ObjectIdentifierTypeDef
from mypy_boto3_sns.client import SNSClient
from mypy_boto3_sns.type_defs import MessageAttributeValueTypeDef
from typing_extensions import NotRequired

from caselawclient.types import DocumentURIString

env = environ.Env()


class S3PrefixString(str):
    def __new__(cls, content: str) -> "S3PrefixString":
        if content[-1] != "/":
            raise RuntimeError("S3 Prefixes must end in / so they behave like directories")
        return str.__new__(cls, content)


class ParserInstructionsMetadataDict(TypedDict):
    name: Optional[str]
    cite: Optional[str]
    court: Optional[str]
    date: Optional[str]
    uri: Optional[str]


class ParserInstructionsDict(TypedDict):
    documentType: NotRequired[Optional[str]]
    metadata: NotRequired[ParserInstructionsMetadataDict]


@overload
def create_aws_client(service: Literal["s3"]) -> S3Client: ...


@overload
def create_aws_client(service: Literal["sns"]) -> SNSClient: ...


def create_aws_client(service: Literal["s3", "sns"]) -> Any:
    aws = boto3.session.Session()
    return aws.client(
        service,
        region_name=env("PRIVATE_ASSET_BUCKET_REGION", default=None),
        config=botocore.client.Config(signature_version="s3v4"),
    )


def create_s3_client() -> S3Client:
    return create_aws_client("s3")


def create_sns_client() -> SNSClient:
    return create_aws_client("sns")


def uri_for_s3(uri: DocumentURIString) -> S3PrefixString:
    """An S3 Prefix must end with / to avoid uksc/2004/1 matching uksc/2004/1000"""
    return S3PrefixString(uri + "/")


def generate_signed_asset_url(key: str) -> str:
    # If there isn't a PRIVATE_ASSET_BUCKET, don't try to get the bucket.
    # This helps local environment setup where we don't use S3.
    bucket = env("PRIVATE_ASSET_BUCKET", None)
    if not bucket:
        return ""

    client = create_s3_client()

    return str(
        client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
        ),
    )


def check_docx_exists(uri: DocumentURIString) -> bool:
    """Does the docx for a document URI actually exist?"""
    bucket = env("PRIVATE_ASSET_BUCKET", None)
    s3_key = generate_docx_key(uri)
    client = create_s3_client()
    try:
        client.head_object(Bucket=bucket, Key=s3_key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def generate_docx_key(uri: DocumentURIString) -> str:
    """from a canonical caselaw URI (eat/2022/1) return the S3 key of the associated docx"""
    return f"{uri}/{uri.replace('/', '_')}.docx"


def generate_docx_url(uri: DocumentURIString) -> str:
    """from a canonical caselaw URI (eat/2022/1) return a signed S3 link for the front end"""
    return generate_signed_asset_url(generate_docx_key(uri))


def generate_pdf_url(uri: DocumentURIString) -> str:
    key = f"{uri}/{uri.replace('/', '_')}.pdf"

    return generate_signed_asset_url(key)


def delete_from_bucket(uri: DocumentURIString, bucket: str) -> None:
    client = create_s3_client()
    response = client.list_objects(Bucket=bucket, Prefix=uri_for_s3(uri))

    if response.get("Contents"):
        objects_to_delete: list[ObjectIdentifierTypeDef] = [{"Key": obj["Key"]} for obj in response.get("Contents", [])]
        client.delete_objects(
            Bucket=bucket,
            Delete={
                "Objects": objects_to_delete,
            },
        )


def publish_documents(uri: DocumentURIString) -> None:
    """
    Copy assets from the unpublished bucket to the published one.
    Don't copy parser logs and package tar gz.
    TODO: consider refactoring with copy_assets
    """
    client = create_s3_client()

    public_bucket = env("PUBLIC_ASSET_BUCKET")
    private_bucket = env("PRIVATE_ASSET_BUCKET")

    response = client.list_objects(Bucket=private_bucket, Prefix=uri_for_s3(uri))

    for result in response.get("Contents", []):
        print(f"Contemplating copying {result!r}")
        key = str(result["Key"])

        if not key.endswith("parser.log") and not key.endswith(".tar.gz"):
            source: CopySourceTypeDef = {"Bucket": private_bucket, "Key": key}
            extra_args: dict[str, str] = {}
            try:
                print(f"Copying {key!r} from {private_bucket!r} to {public_bucket!r}")
                client.copy(source, public_bucket, key, extra_args)
            except botocore.client.ClientError as e:
                logging.warning(
                    f"Unable to copy file {key} to new location {public_bucket}, error: {e}",
                )


def unpublish_documents(uri: DocumentURIString) -> None:
    delete_from_bucket(uri, env("PUBLIC_ASSET_BUCKET"))


def delete_documents_from_private_bucket(uri: DocumentURIString) -> None:
    delete_from_bucket(uri, env("PRIVATE_ASSET_BUCKET"))


def announce_document_event(uri: DocumentURIString, status: str, enrich: bool = False) -> None:
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
        TopicArn=env("SNS_TOPIC"),  # this is the ANNOUNCE SNS topic
        Message=json.dumps({"uri_reference": uri, "status": status}),
        Subject=f"Updated: {uri} {status}",
        MessageAttributes=message_attributes,
    )


def copy_assets(old_uri: DocumentURIString, new_uri: DocumentURIString) -> None:
    """
    Copy *unpublished* assets from one path to another,
    renaming DOCX and PDF files as appropriate.
    """
    client = create_s3_client()
    bucket = env("PRIVATE_ASSET_BUCKET")
    response = client.list_objects(Bucket=bucket, Prefix=uri_for_s3(old_uri))

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
                f"Unable to copy file {old_key} to new location {new_key}, error: {e}",
            )


def build_new_key(old_key: str, new_uri: DocumentURIString) -> str:
    """Ensure that DOCX and PDF filenames are modified to reflect their new home
    as we get the name of the new S3 path"""
    old_filename = old_key.rsplit("/", 1)[-1]

    if old_filename.endswith(".docx") or old_filename.endswith(".pdf"):
        new_filename = new_uri.replace("/", "_")
        return f"{new_uri}/{new_filename}.{old_filename.split('.')[-1]}"
    return f"{new_uri}/{old_filename}"


def request_parse(
    uri: DocumentURIString,
    reference: Optional[str],
    parser_instructions: Optional[ParserInstructionsDict] = None,
) -> None:
    client = create_sns_client()

    if parser_instructions is None:
        parser_instructions = ParserInstructionsDict({})

    message_to_send = {
        "properties": {
            "messageType": "uk.gov.nationalarchives.da.messages.request.courtdocument.parse.RequestCourtDocumentParse",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "function": "fcl-judgment-parse-request",
            "producer": "FCL",
            "executionId": str(uuid.uuid4()),
            "parentExecutionId": None,
        },
        "parameters": {
            "s3Bucket": env("PRIVATE_ASSET_BUCKET"),
            "s3Key": generate_docx_key(uri),
            "reference": reference or f"FCL-{str(uuid.uuid4())[:-13]}",  # uuid truncated at request of TRE
            "originator": "FCL",
            "parserInstructions": parser_instructions,
        },
    }

    client.publish(
        TopicArn=env("REPARSE_SNS_TOPIC"),
        Message=json.dumps(message_to_send),
        Subject=f"Reparse request: {uri}",
    )
