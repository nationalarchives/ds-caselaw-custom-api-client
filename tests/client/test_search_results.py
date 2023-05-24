import pytest
from lxml import etree

from caselawclient.models.search_results import SearchMatches, SearchResults


class TestSearchResults:
    def test_total(self, valid_search_response_xml):
        """
        Given a SearchResults instance
        When accessing the 'total' property
        Then it should return the total number of search results as a string
        """
        search_results = SearchResults(valid_search_response_xml)
        total = search_results.total

        assert total == "2"

    def test_results(self, valid_search_response_xml):
        """
        Given a SearchResults instance
        When accessing the 'results' property
        Then it should return a list of search result elements
        And the list should contain the expected number of etree._Element objects
        And each element's text should match the expected value
        """
        search_results = SearchResults(valid_search_response_xml)

        results = search_results.results

        assert len(results) == 2
        assert isinstance(results[0], etree._Element)
        assert results[0].text == "Result 1"
        assert results[1].text == "Result 2"

    def test_when_search_namespace_prefix_not_defined_on_response_xml_syntax_error_raised(
        self,
    ):
        """
        Given an XML response without the 'search' namespace prefix defined
        When creating SearchResults instance with the XML
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
            SearchResults(xml_without_namespace)


class TestSearchMatches:
    def test_transform_to_html(self):
        """
        Given a SearchMatch instantiated with a `search:result` xml node
        When transform_to_html is called on the SearchMatch instance
        Then it returns html representation of all its matches
        """
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search">'
            "<search:snippet>"
            "<search:match path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "text from the document that matched the search"
            "</search:match>"
            "<search:match path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "some more text from the document that matched the search"
            "</search:match>"
            "</search:snippet>"
            "</search:result>"
        )
        search_match = SearchMatches(xml)
        assert search_match.transform_to_html() == (
            "<p data-path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "text from the document that matched the search"
            "</p>"
            "<p data-path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "some more text from the document that matched the search"
            "</p>\n"
        )
