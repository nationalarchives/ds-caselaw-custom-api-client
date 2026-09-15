import pytest

from caselawclient.errors import DocumentNotFoundError
from marklogic_harness.corpus import (
    TEST_MATCHING_SCHEMA_URI,
    TEST_NOT_MATCHING_SCHEMA_URI,
    TEST_PRESS_SUMMARY_PARENT_URI,
    TEST_PRESS_SUMMARY_URI,
)

pytestmark = pytest.mark.marklogic


def test_get_document_type_returns_404(marklogic_api_client):
    with pytest.raises(DocumentNotFoundError) as exc_info:
        marklogic_api_client.get_document_type_from_uri("/not/a/real/url")
    assert exc_info.value.status_code == 404


def test_get_press_summaries_for_document_uri(marklogic_api_client):
    result = marklogic_api_client.get_press_summaries_for_document_uri(TEST_PRESS_SUMMARY_PARENT_URI)
    assert len(result) == 1
    assert result[0].uri == TEST_PRESS_SUMMARY_URI


@pytest.mark.parametrize(
    ("document_uri", "validates_against_schema"),
    [
        (TEST_NOT_MATCHING_SCHEMA_URI, False),
        (TEST_MATCHING_SCHEMA_URI, True),
    ],
)
def test_document_schema_validation(marklogic_api_client, document_uri, validates_against_schema):
    assert marklogic_api_client.validate_document(document_uri) is validates_against_schema
