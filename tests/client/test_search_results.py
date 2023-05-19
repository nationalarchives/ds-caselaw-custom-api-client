from lxml import etree

from caselawclient.models.search_results import SearchResults


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

    def test_init_fails(self):
        xml_without_namespace = (
            '<search:response xmlns:search="http://marklogic.com/appservices/adasf" total="2">'  # noqa: E501
            "<search:result>Result 1</search:result>"
            "<search:result>Result 2</search:result>"
            "</search:response>"
        )
        SearchResults(xml_without_namespace)
