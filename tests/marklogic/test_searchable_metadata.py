import pytest

from caselawclient.models.documents.metadata.searchable import SEARCHABLE_METADATA_PROPERTY
from caselawclient.types import DocumentURIString
from marklogic_harness.corpus import SEARCH_JUDGE_ALPHA, SEARCH_JUDGE_BETA, SEARCH_JUDGES_BOTH_URI

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

DISPOSABLE_URI = DocumentURIString("test/searchable_metadata_write")
EDITOR_JUDGE = "Searchable Editor Judge"


@pytest.fixture
def disposable_uri(marklogic_api_client):
    """A throwaway copy of a document whose body names two judges, alpha and beta."""
    if marklogic_api_client.document_exists(DISPOSABLE_URI):
        marklogic_api_client.delete_judgment(DISPOSABLE_URI)
    marklogic_api_client.copy_document(SEARCH_JUDGES_BOTH_URI, DISPOSABLE_URI)
    yield DISPOSABLE_URI
    if marklogic_api_client.document_exists(DISPOSABLE_URI):
        marklogic_api_client.delete_judgment(DISPOSABLE_URI)


def _stored_judges(marklogic_api_client, uri) -> list[str]:
    stored = marklogic_api_client.get_property_as_node(uri, SEARCHABLE_METADATA_PROPERTY)
    assert stored is not None, f"{SEARCHABLE_METADATA_PROPERTY} was not written"
    return [judge.text for judge in stored]


def test_nothing_is_stored_until_metadata_is_saved(marklogic_api_client, disposable_uri):
    assert marklogic_api_client.get_property_as_node(disposable_uri, SEARCHABLE_METADATA_PROPERTY) is None


def test_saving_without_edits_stores_the_body_judges(marklogic_api_client, disposable_uri):
    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    with document.editing_session():
        document.save_metadata_fields()

    assert _stored_judges(marklogic_api_client, disposable_uri) == [SEARCH_JUDGE_ALPHA, SEARCH_JUDGE_BETA]


def test_an_editor_added_judge_is_stored_alongside_the_body_judges(marklogic_api_client, disposable_uri):
    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    with document.editing_session():
        document.metadata.judges.add_editor_judge(EDITOR_JUDGE)
        document.save_metadata_fields()

    assert _stored_judges(marklogic_api_client, disposable_uri) == [SEARCH_JUDGE_ALPHA, SEARCH_JUDGE_BETA, EDITOR_JUDGE]


def test_a_suppressed_body_judge_is_not_stored(marklogic_api_client, disposable_uri):
    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    with document.editing_session():
        document.metadata.judges.suppress_body_value(SEARCH_JUDGE_ALPHA)
        document.save_metadata_fields()

    assert _stored_judges(marklogic_api_client, disposable_uri) == [SEARCH_JUDGE_BETA]


def test_saving_again_replaces_what_was_stored_before(marklogic_api_client, disposable_uri):
    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    with document.editing_session():
        document.metadata.judges.add_editor_judge(EDITOR_JUDGE)
        document.save_metadata_fields()

    document = marklogic_api_client.get_document_by_uri(disposable_uri)
    editor_claim = next(
        claim for claim in document.metadata_fields.by_name("judges") if claim.value.value == EDITOR_JUDGE
    )
    with document.editing_session():
        document.metadata.judges.suppress_claim(editor_claim.id)
        document.save_metadata_fields()

    assert _stored_judges(marklogic_api_client, disposable_uri) == [SEARCH_JUDGE_ALPHA, SEARCH_JUDGE_BETA]
