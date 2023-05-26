import pytest
from lxml import etree

from caselawclient.responses.search_response import SearchResponse


class TestSearchResponse:
    def test_to_search_results(
        self,
        valid_search_result_xml,
        generate_search_response_xml,
    ):
        """
        Given a SearchResponse instance with n results
        When calling 'to_search_results' on it
        Then it should return a list of n SearchResult elements
        And each element's node attribute should be as expected
        """
        search_response = SearchResponse.from_response_string(
            generate_search_response_xml(2 * valid_search_result_xml)
        )

        results = search_response.to_search_results()

        assert len(results) == 2
        assert etree.tostring(results[0].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml)
        )
        assert etree.tostring(results[1].node) == etree.tostring(
            etree.fromstring(valid_search_result_xml)
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
            '<search:response xmlns:foo="http://marklogic.com/appservices/search" total="2">'  # noqa: E501
            "<search:result>Result 1</search:result>"
            "<search:result>Result 2</search:result>"
            "</search:response>"
        )
        with pytest.raises(
            etree.XMLSyntaxError,
            match="Namespace prefix search on response is not defined",
        ):
            SearchResponse.from_response_string(xml_without_namespace)
