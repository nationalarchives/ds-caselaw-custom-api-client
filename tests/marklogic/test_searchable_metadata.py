import pytest

from caselawclient.models.documents.metadata.searchable import SEARCHABLE_METADATA_PROPERTY
from caselawclient.types import DocumentURIString

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

DISPOSABLE_URI = DocumentURIString("test/searchable_metadata_write")


@pytest.fixture
def disposable_uri(marklogic_api_client, metadata_writes_uri):
    if marklogic_api_client.document_exists(DISPOSABLE_URI):
        marklogic_api_client.delete_judgment(DISPOSABLE_URI)
    marklogic_api_client.copy_document(metadata_writes_uri, DISPOSABLE_URI)
    yield DISPOSABLE_URI
    if marklogic_api_client.document_exists(DISPOSABLE_URI):
        marklogic_api_client.delete_judgment(DISPOSABLE_URI)


def test_saving_judge_claims_stores_them_in_searchable_metadata(marklogic_api_client, disposable_uri):
    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    with document.editing_session():
        document.metadata.judges.add_editor_judge("Searchable Judge")
        document.save_metadata_fields()

    stored = marklogic_api_client.get_property_as_node(disposable_uri, SEARCHABLE_METADATA_PROPERTY)

    assert stored is not None
    assert [judge.text for judge in stored] == ["Searchable Judge"]
