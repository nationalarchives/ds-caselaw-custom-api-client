import json

import pytest

from caselawclient.Client import get_multipart_strings_from_marklogic_response
from caselawclient.models.utilities import extract_version
from caselawclient.types import DocumentURIString
from marklogic_harness.corpus import TEST_METADATA_WRITES_URI
from tests.marklogic.xml_assertions import (
    judgment_court,
    judgment_frbr_name,
    judgment_work_expression_date,
)

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

ORIGINAL_NAME = "cats v dogs"
ORIGINAL_COURT = "EWHC-Chancellery"
ORIGINAL_DATE = "1001-02-03"


@pytest.fixture
def reset_metadata_writes(marklogic_api_client, metadata_writes_uri):
    yield
    marklogic_api_client.set_document_court(metadata_writes_uri, ORIGINAL_COURT)
    marklogic_api_client.set_document_name(metadata_writes_uri, ORIGINAL_NAME)
    marklogic_api_client.set_document_work_expression_date(metadata_writes_uri, ORIGINAL_DATE)


def test_set_document_metadata_persists_in_marklogic(
    marklogic_api_client,
    metadata_writes_uri,
    reset_metadata_writes,
):
    new_court = "UKSC"
    new_name = "api client harness metadata write"
    new_date = "2002-03-04"

    marklogic_api_client.set_document_court(metadata_writes_uri, new_court)
    marklogic_api_client.set_document_name(metadata_writes_uri, new_name)
    marklogic_api_client.set_document_work_expression_date(metadata_writes_uri, new_date)

    assert judgment_court(marklogic_api_client, metadata_writes_uri) == new_court
    assert judgment_frbr_name(marklogic_api_client, metadata_writes_uri) == new_name
    assert judgment_work_expression_date(marklogic_api_client, metadata_writes_uri) == new_date


def test_get_version_annotation(marklogic_api_client):
    response = marklogic_api_client.list_judgment_versions(TEST_METADATA_WRITES_URI)
    version_uris = get_multipart_strings_from_marklogic_response(response)
    first_version_uri = DocumentURIString(
        min(version_uris, key=lambda uri: extract_version(uri) or 10**9).strip("/").removesuffix(".xml")
    )
    annotation = json.loads(marklogic_api_client.get_version_annotation(first_version_uri))
    assert annotation["message"] == "metadata write fixture annotation"
