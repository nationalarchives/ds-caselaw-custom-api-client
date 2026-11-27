"""Acceptance tests: judge search follows the judges in the metadata store, not just the body."""

import pytest

from caselawclient.client_helpers.search_helpers import search_and_parse_response
from caselawclient.search_parameters import SearchParameters
from marklogic_harness.corpus import (
    SEARCH_ACCEPTANCE_BODY_JUDGE,
    SEARCH_ACCEPTANCE_DOCUMENT,
    SEARCH_ACCEPTANCE_EDITOR_JUDGE,
    SEARCH_ACCEPTANCE_KEYWORD,
    SEARCH_ACCEPTANCE_URI,
    reload_corpus_documents,
)

pytestmark = [pytest.mark.marklogic, pytest.mark.write]

search_reads_searchable_metadata = pytest.mark.xfail(
    raises=AssertionError,
    strict=True,
    reason="The pinned ds-caselaw-marklogic predates search reading searchable-metadata (ds-caselaw-marklogic#986)",
)


@pytest.fixture
def acceptance_document(marklogic_api_client):
    reload_corpus_documents(marklogic_api_client, (SEARCH_ACCEPTANCE_DOCUMENT,))
    yield marklogic_api_client.get_document_by_uri(SEARCH_ACCEPTANCE_URI)
    marklogic_api_client.delete_judgment(SEARCH_ACCEPTANCE_URI)


def _documents_found_for_judge(client, judge: str) -> set[str]:
    response = search_and_parse_response(
        client,
        SearchParameters(
            specific_keyword=SEARCH_ACCEPTANCE_KEYWORD,
            judge=judge,
            show_unpublished=True,
            page_size=50,
        ),
    )
    return {result.uri for result in response.results}


def test_body_judge_is_found_before_any_metadata_has_been_saved(marklogic_api_client, acceptance_document):
    assert _documents_found_for_judge(marklogic_api_client, SEARCH_ACCEPTANCE_BODY_JUDGE) == {SEARCH_ACCEPTANCE_URI}


def test_body_judge_is_still_found_after_an_editor_adds_another_judge(marklogic_api_client, acceptance_document):
    with acceptance_document.editing_session():
        acceptance_document.metadata.judges.add_editor_judge(SEARCH_ACCEPTANCE_EDITOR_JUDGE)
        acceptance_document.save_metadata_fields()

    assert _documents_found_for_judge(marklogic_api_client, SEARCH_ACCEPTANCE_BODY_JUDGE) == {SEARCH_ACCEPTANCE_URI}


@search_reads_searchable_metadata
def test_judge_added_by_an_editor_is_found(marklogic_api_client, acceptance_document):
    with acceptance_document.editing_session():
        acceptance_document.metadata.judges.add_editor_judge(SEARCH_ACCEPTANCE_EDITOR_JUDGE)
        acceptance_document.save_metadata_fields()

    assert _documents_found_for_judge(marklogic_api_client, SEARCH_ACCEPTANCE_EDITOR_JUDGE) == {SEARCH_ACCEPTANCE_URI}


@search_reads_searchable_metadata
def test_judge_suppressed_by_an_editor_is_no_longer_found(marklogic_api_client, acceptance_document):
    with acceptance_document.editing_session():
        acceptance_document.metadata.judges.suppress_body_value(SEARCH_ACCEPTANCE_BODY_JUDGE)
        acceptance_document.save_metadata_fields()

    assert _documents_found_for_judge(marklogic_api_client, SEARCH_ACCEPTANCE_BODY_JUDGE) == set()
