import pytest
from caselawclient.Client import MarklogicApiClient
from caselawclient.responses.search_response import SearchResponse
from lxml import etree


class TestSearchResponse:
    def setup_method(self):
        self.client = MarklogicApiClient(
            host="",
            username="",
            password="",
            use_https=False,
            user_agent="marklogic-api-client-test",
        )

    def test_total(
        self,
    ):
        """
        Given a SearchResponse instance
        When calling 'total' on it
        Then it should return a string representing the total number of results
        """
        search_response = SearchResponse(
            etree.fromstring(
                '<search:response xmlns:search="http://marklogic.com/appservices/search" total="5">'
                "foo"
                "</search:response>",
            ),
            self.client,
        )

        assert search_response.total == "5"

    def test_results(
        self,
        valid_search_result_xml,
        generate_search_response_xml,
    ):
        """
        Given a SearchResponse instance with n results
        When calling 'results' on it
        Then it should return a list of n SearchResult elements
        And each element's node attribute should be as expected
        """
        search_response = SearchResponse(
            etree.fromstring(generate_search_response_xml(2 * valid_search_result_xml)),
            self.client,
        )

        results = search_response.results

        assert len(results) == 2
        assert etree.tostring(results[0].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml),
        )
        assert etree.tostring(results[1].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml),
        )

    def test_when_search_namespace_prefix_not_defined_on_response_xml_syntax_error_raised(
        self,
    ):
        """
        Given an XML response without the 'search' namespace prefix defined
        When creating SearchResponse instance with the XML
        Then a XMLSyntaxError with the expected message should be raised
        """
        xml_without_namespace = (
            '<search:response xmlns:foo="http://marklogic.com/appservices/search" total="2">'
            "<search:result>Result 1</search:result>"
            "<search:result>Result 2</search:result>"
            "</search:response>"
        )
        with pytest.raises(
            etree.XMLSyntaxError,
            match="Namespace prefix search on response is not defined",
        ):
            SearchResponse(etree.fromstring(xml_without_namespace), self.client)

    def test_facets(
        self,
        valid_search_result_xml,
        valid_facets_fixture_xml,
        generate_search_response_xml,
    ):
        """
        Given a SearchResponse instance with n facets
        When calling 'facets' on it
        Then it should return a list of n elements
        And each element's node attribute should be as expected
        """
        search_response = SearchResponse(
            etree.fromstring(
                generate_search_response_xml(
                    valid_search_result_xml,
                    valid_facets_fixture_xml,
                ),
            ),
            self.client,
        )

        results = search_response.facets

        assert len(results) == 4
        assert results[""] == "14"
        assert results[" UKUT-AAC"] == "1"
        assert results["EAT"] == "649"
        assert results["EWCA-Civil"] == "5768"
