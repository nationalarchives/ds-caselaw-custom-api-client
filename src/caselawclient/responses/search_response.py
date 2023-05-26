from typing import List

from lxml import etree

from caselawclient.responses.search_result import SearchResult


class SearchResponse:
    """
    Represents a search response obtained from XML data.

    Attributes:
        NAMESPACES (dict): Namespaces used in XPath expressions.
    """

    NAMESPACES = {"search": "http://marklogic.com/appservices/search"}

    def __init__(self, node: etree._Element):
        """
        Initializes a SearchResponse instance from an xml node.

        Args:
            node (etree._Element): The XML data as an etree element.
        """
        self.node = node

    @staticmethod
    def from_response_string(xml: str) -> "SearchResponse":
        """
        Constructs a SearchResponse instance from an xml response string.

        Args:
            xml (str): The XML data as a string.
        """
        return SearchResponse(etree.fromstring(xml))

    def to_search_results(self) -> List[SearchResult]:
        """
        Converts the SearchResponse to a list of SearchResult objects.

        Returns:
            List[SearchResult]: The list of search results.
        """
        results = self.node.xpath(
            "//search:response/search:result", namespaces=self.NAMESPACES
        )
        return [
            SearchResult(
                result,
            )
            for result in results
        ]
