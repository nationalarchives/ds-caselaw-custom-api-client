import json

import pytest

from caselawclient.Client import get_multipart_strings_from_marklogic_response
from caselawclient.errors import DocumentNotFoundError
from caselawclient.models.documents import Document
from caselawclient.models.utilities import extract_version
from caselawclient.types import DocumentURIString
from marklogic_harness.corpus import SMOKETEST_URI

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

ORIGINAL_COURT = "EWHC-Chancellery"
ORIGINAL_NAME = "cats v dogs"
ORIGINAL_DATE = "1001-02-03"


@pytest.fixture
def reset_smoketest_metadata(marklogic_api_client, smoketest_uri):
    yield
    marklogic_api_client.set_document_court(smoketest_uri, ORIGINAL_COURT)
    marklogic_api_client.set_document_name(smoketest_uri, ORIGINAL_NAME)
    marklogic_api_client.set_document_work_expression_date(smoketest_uri, ORIGINAL_DATE)


def test_get_document_type_returns_404(marklogic_api_client):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        marklogic_api_client.get_document_type_from_uri("/not/a/real/url")
    assert exc_info.value.status_code == 404


def test_set_metadata(marklogic_api_client, smoketest_uri, reset_smoketest_metadata):
    new_court = "UKSC"
    new_name = "smoketest harness metadata write"
    new_date = "2002-03-04"

    marklogic_api_client.set_document_court(smoketest_uri, new_court)
    marklogic_api_client.set_document_name(smoketest_uri, new_name)
    marklogic_api_client.set_document_work_expression_date(smoketest_uri, new_date)

    document = marklogic_api_client.get_document_by_uri(smoketest_uri)
    assert document.court == new_court
    assert document.name == new_name
    assert document.document_date_as_string == new_date


def test_get_version_annotation(marklogic_api_client):
    response = marklogic_api_client.list_judgment_versions(SMOKETEST_URI)
    version_uris = get_multipart_strings_from_marklogic_response(response)
    first_version_uri = DocumentURIString(
        min(version_uris, key=lambda uri: extract_version(uri) or 10**9).strip("/").removesuffix(".xml")
    )
    annotation = json.loads(marklogic_api_client.get_version_annotation(first_version_uri))
    assert annotation["message"] == "this is an annotation"
    assert (
        json.loads(Document(first_version_uri, marklogic_api_client).annotation)["message"] == "this is an annotation"
    )
