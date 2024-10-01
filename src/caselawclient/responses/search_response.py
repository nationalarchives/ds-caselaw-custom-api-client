from typing import List

from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.responses.search_result import SearchResult


class SearchResponse:
    """
    Represents a search response obtained from XML data.
    """

    NAMESPACES = {"search": "http://marklogic.com/appservices/search"}
    """ Namespaces used in XPath expressions."""

    def __init__(self, node: etree._Element, client: MarklogicApiClient) -> None:
        """
        Initializes a SearchResponse instance from an xml node.

        :param node: The XML data as an etree element
        """
        self.node = node
        self.client = client

    @property
    def total(self) -> int:
        """
        The total number of search results.

        :return: The total number of search results
        """
        return int(
            self.node.xpath("//search:response/@total", namespaces=self.NAMESPACES)[0],
        )

    @property
    def results(self) -> List[SearchResult]:
        """
        Converts the SearchResponse to a list of SearchResult objects.

        :return: The list of search results
        """
        results = self.node.xpath(
            "//search:response/search:result",
            namespaces=self.NAMESPACES,
        )
        return [SearchResult(result, self.client) for result in results]

    @property
    def facets(self) -> dict[str, str]:
        """
        Returns search facets from the SearchResponse as a dictionary

        :return: A flattened dictionary of search facet values
        """
        # TODO: preserve the name of the facet (e.g. "court", "year")
        results = self.node.xpath(
            "//search:response/search:facet/search:facet-value",
            namespaces={"search": "http://marklogic.com/appservices/search"},
        )
        facets_dictionary = {result.attrib["name"]: result.attrib["count"] for result in results}
        return facets_dictionary
