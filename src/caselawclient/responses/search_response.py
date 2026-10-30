from copy import deepcopy
from functools import cached_property

from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.responses.search_result import SearchResult, SearchResultMetadata
from caselawclient.xml_helpers import Element


class SearchResponse:
    """
    Represents a search response obtained from XML data.
    """

    NAMESPACES = {"search": "http://marklogic.com/appservices/search"}
    """ Namespaces used in XPath expressions."""

    def __init__(self, node: Element, client: MarklogicApiClient) -> None:
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

    @cached_property
    def results(self) -> list[SearchResult]:
        """
        Converts the SearchResponse to a list of SearchResult objects.

        Loads properties and last-modified timestamps in one request for the page.
        Results are cached so repeated access does not repeat that lookup.

        :return: The list of search results
        """
        results = self.node.xpath(
            "//search:response/search:result",
            namespaces=self.NAMESPACES,
        )
        search_results = [SearchResult(result, self.client) for result in results]
        if not search_results:
            return search_results

        properties = etree.fromstring(
            self.client.get_properties_for_search_results([result.uri for result in search_results]),
            parser=etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True, huge_tree=False),
        )
        properties_by_uri = {node.get("uri"): node for node in properties.findall("property-result")}
        for result in search_results:
            node = properties_by_uri.get(result.node.get("uri"))
            if node is None:
                node = etree.Element("property-result")
            # Metadata XPath expressions use //, so each result needs its own tree.
            result.metadata = SearchResultMetadata(deepcopy(node), node.get("last-modified", ""))
        return search_results

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
