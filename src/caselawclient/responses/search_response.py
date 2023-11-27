from typing import List

from lxml import etree

from caselawclient.responses.search_result import SearchResult


class SearchResponse:
    """
    Represents a search response obtained from XML data.
    """

    NAMESPACES = {"search": "http://marklogic.com/appservices/search"}
    """ Namespaces used in XPath expressions."""

    def __init__(self, node: etree._Element) -> None:
        """
        Initializes a SearchResponse instance from an xml node.

        :param node: The XML data as an etree element
        """
        self.node = node

    @property
    def total(self) -> str:
        """
        The total number of search results.

        :return: The total number of search results
        """
        return str(
            self.node.xpath("//search:response/@total", namespaces=self.NAMESPACES)[0]
        )

    @property
    def results(self) -> List[SearchResult]:
        """
        Converts the SearchResponse to a list of SearchResult objects.

        :return: The list of search results
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
