from unittest.mock import patch

from caselawclient.Client import api_client
from caselawclient.models.search_results import SearchResults
from caselawclient.search_parameters import SearchParameters


@patch("caselawclient.Client.api_client.advanced_search")
def test_search_judgments_and_parse_results(
    mock_advanced_search, mock_search_results_response
):
    """
    Given the search parameters for search_judgments_and_parse_results are valid
    And a mocked api_client response with 2 search results
    When search_judgments_and_parse_results function is called with the mocked API client
        and input parameters
    Then the API client's advanced_search method should be called once with the
        appropriate parameters
    And the search_judgments_and_parse_results function should return an instance of
        SearchResults with the 2 search results
    """
    mock_advanced_search.return_value = mock_search_results_response

    search_results = api_client.search_judgments_and_parse_results(
        SearchParameters(
            q="test query",
            court="test court",
            judge="test judge",
            party="test party",
            neutral_citation="test citation",
            specific_keyword="test keyword",
            date_from="2022-01-01",
            date_to="2022-01-31",
            page=1,
            page_size=10,
        )
    )

    mock_advanced_search.assert_called_once_with(
        SearchParameters(
            q="test query",
            court="test court",
            judge="test judge",
            party="test party",
            neutral_citation="test citation",
            specific_keyword="test keyword",
            order=None,
            date_from="2022-01-01",
            date_to="2022-01-31",
            page=1,
            page_size=10,
            show_unpublished=False,
            only_unpublished=False,
            collections=["judgment"],
        )
    )

    assert isinstance(search_results, SearchResults)
    assert search_results.total == "2"
    assert [result.text for result in search_results.results] == [
        "Result 1",
        "Result 2",
    ]
