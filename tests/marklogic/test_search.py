import pytest

from caselawclient.client_helpers.search_helpers import search_and_parse_response
from caselawclient.search_parameters import SearchParameters
from marklogic_harness.corpus import (
    SEARCH_DATE_FIXTURE_KEYWORD,
    SEARCH_FIXTURE_KEYWORD,
    SEARCH_FIXTURE_URIS,
    SEARCH_JUDGE_ALPHA,
    SEARCH_JUDGE_BETA,
    SEARCH_JUDGE_PROSE,
    SEARCH_JUDGE_PROSE_URI,
    SEARCH_JUDGE_TAGGED_URI,
    SEARCH_JUDGES_ALPHA_URI,
    SEARCH_JUDGES_BOTH_URI,
    SEARCH_JUDGES_GAMMA_URI,
    SEARCH_PUBLISHED_URI,
)

pytestmark = pytest.mark.marklogic


def _result_uris(client, *, keyword: str = SEARCH_FIXTURE_KEYWORD, **filters) -> set[str]:
    response = search_and_parse_response(
        client,
        SearchParameters(specific_keyword=keyword, page_size=50, **filters),
    )
    return {result.uri for result in response.results}


def test_judge_search_matches_header_judge_elements(marklogic_api_client):
    client = marklogic_api_client

    assert _result_uris(client, judge=SEARCH_JUDGE_BETA, show_unpublished=True) == {SEARCH_JUDGES_BOTH_URI}
    assert _result_uris(client, judge=f"{SEARCH_JUDGE_ALPHA},{SEARCH_JUDGE_BETA}", show_unpublished=True) == {
        SEARCH_JUDGES_BOTH_URI,
        SEARCH_JUDGES_ALPHA_URI,
    }
    assert SEARCH_JUDGES_GAMMA_URI not in _result_uris(client, judge=SEARCH_JUDGE_ALPHA, show_unpublished=True)


def test_judge_search_ignores_the_same_string_in_body_prose(marklogic_api_client):
    found = _result_uris(marklogic_api_client, judge=SEARCH_JUDGE_PROSE, show_unpublished=True)

    assert found == {SEARCH_JUDGE_TAGGED_URI}
    assert SEARCH_JUDGE_PROSE_URI not in found
    assert SEARCH_JUDGE_PROSE_URI in _result_uris(marklogic_api_client, show_unpublished=True)


def test_date_range_uses_frbr_work_date(marklogic_api_client):
    client = marklogic_api_client

    assert _result_uris(client, keyword=SEARCH_DATE_FIXTURE_KEYWORD, date_from="2099-06-01", show_unpublished=True) == {
        SEARCH_JUDGES_BOTH_URI,
        SEARCH_JUDGES_GAMMA_URI,
    }
    assert _result_uris(client, keyword=SEARCH_DATE_FIXTURE_KEYWORD, date_to="2099-06-30", show_unpublished=True) == {
        SEARCH_JUDGES_ALPHA_URI,
        SEARCH_JUDGES_BOTH_URI,
    }
    assert _result_uris(
        client,
        keyword=SEARCH_DATE_FIXTURE_KEYWORD,
        date_from="2099-06-01",
        date_to="2099-06-30",
        show_unpublished=True,
    ) == {SEARCH_JUDGES_BOTH_URI}


def test_unpublished_documents_are_omitted_unless_requested(marklogic_api_client):
    client = marklogic_api_client

    assert _result_uris(client) == {SEARCH_PUBLISHED_URI}
    assert _result_uris(client, show_unpublished=True) == set(SEARCH_FIXTURE_URIS)
