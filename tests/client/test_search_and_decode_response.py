from unittest.mock import patch

from caselawclient.Client import api_client
from caselawclient.search_parameters import SearchParameters


@patch("caselawclient.Client.api_client.advanced_search")
def test_search_judgments_and_decode_response(
    mock_advanced_search,
    valid_search_response_xml,
    generate_mock_search_response,
):
    """
    Given the search parameters for search_judgments_and_decode_response are valid
    And a mocked api_client response with search results
    When search_judgments_and_decode_response function is called with the mocked API client
        and input parameters
    Then the API client's advanced_search method should be called once with the
        appropriate parameters
    And the search_judgments_and_decode_response function should return the response
        xml string with all the search results
    """
    mock_advanced_search.return_value = generate_mock_search_response(
        valid_search_response_xml
    )

    search_response = api_client.search_judgments_and_decode_response(
        SearchParameters(
            query="test query",
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
            query="test query",
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

    assert search_response == valid_search_response_xml
