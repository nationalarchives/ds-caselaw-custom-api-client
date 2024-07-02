from unittest.mock import Mock

from caselawclient.client_helpers.search_helpers import (
    search_judgments_and_parse_response,
)
from caselawclient.search_parameters import SearchParameters
from lxml import etree


def test_search_judgments_and_parse_results(
    generate_search_response_xml,
    valid_search_result_xml,
):
    """
    Given the search parameters for search_judgments_and_parse_response are valid
    And a mocked api_client.search_judgments_and_decode_response return mocked with a
        xml string
    When search_judgments_and_parse_response function is called with the mocked API client
        and input parameters
    Then the API client's search_judgments_and_decode_response method should be called once with the
        same parameters
    And the search_judgments_and_parse_response function should return an instance of
        SearchResponse with a node made up of the same xml string
    """
    mock_api_client = Mock()
    search_response_xml = generate_search_response_xml(2 * valid_search_result_xml)
    mock_api_client.search_judgments_and_decode_response.return_value = search_response_xml

    search_parameters = SearchParameters(
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

    search_response = search_judgments_and_parse_response(
        mock_api_client,
        search_parameters,
    )

    mock_api_client.search_judgments_and_decode_response.assert_called_once_with(
        search_parameters,
    )

    assert etree.tostring(search_response.node) == etree.tostring(
        etree.fromstring(search_response_xml),
    )
