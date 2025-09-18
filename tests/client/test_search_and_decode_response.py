from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient
from caselawclient.search_parameters import SearchParameters


class TestSearchAndDecodeResponse:
    def setup_method(self):
        self.client = MarklogicApiClient(
            host="",
            username="",
            password="",
            use_https=False,
            user_agent="marklogic-api-client-test",
        )

    def test_search_judgments_and_decode_response(
        self,
        valid_search_response_xml,
        generate_mock_search_response,
    ):
        """
        Given the search parameters for search_judgments_and_decode_response are valid
        And a mocked MarklogicApiClient.advanced_search response with search results
        When search_judgments_and_decode_response function is called with the mocked API client
            and input parameters
        Then the API client's advanced_search method should be called once with the
            appropriate parameters
        And the search_judgments_and_decode_response function should return the response
            xml string with all the search results
        """
        with patch.object(self.client, "advanced_search") as mock_advanced_search:
            mock_advanced_search.return_value = generate_mock_search_response(
                valid_search_response_xml,
            )

            search_response = self.client.search_judgments_and_decode_response(
                SearchParameters(
                    query="test query",
                    court="test court",
                    judge="test judge",
                    party="test party",
                    neutral_citation="test citation",
                    name="test name",
                    consignment_number="test consignment number",
                    specific_keyword="test keyword",
                    date_from="2022-01-01",
                    date_to="2022-01-31",
                    page=1,
                    page_size=10,
                ),
            )

            mock_advanced_search.assert_called_once_with(
                SearchParameters(
                    query="test query",
                    court="test court",
                    judge="test judge",
                    party="test party",
                    neutral_citation="test citation",
                    name="test name",
                    consignment_number="test consignment number",
                    specific_keyword="test keyword",
                    order=None,
                    date_from="2022-01-01",
                    date_to="2022-01-31",
                    page=1,
                    page_size=10,
                    show_unpublished=False,
                    only_unpublished=False,
                    collections=["judgment"],
                ),
            )

            assert search_response == valid_search_response_xml
