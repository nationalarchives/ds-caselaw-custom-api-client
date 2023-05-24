import os
from typing import List

from lxml import etree


class SearchResults:
    """
    Represents search results obtained from XML data.

    Attributes:
        NAMESPACES (dict): Namespaces used in XPath expressions.
    """

    NAMESPACES = {"search": "http://marklogic.com/appservices/search"}

    def __init__(self, xml: str):
        """
        Initializes a SearchResults instance.

        Args:
            xml (str): The XML data as a string.
        """
        self._root = etree.fromstring(xml)

    @property
    def total(self) -> str:
        """
        Retrieves the total number of search results.

        Returns:
            str: The total number of search results as a string.
        """
        return str(
            int(
                self._root.xpath(
                    "number(//search:response/@total)", namespaces=self.NAMESPACES
                )
            )
        )

    @property
    def results(self) -> List[etree._Element]:
        """
        Retrieves the list of search result elements.

        Returns:
            List[etree._Element]: The list of search result elements.
        """
        results = self._root.xpath(
            "//search:response/search:result", namespaces=self.NAMESPACES
        )
        return [element for element in results]


class SearchMatches:
    """
    Represents a collection of search matches obtained from XML data.
    """

    def __init__(self, xml: str):
        """
        Initialize a SearchMatches instance with XML data.

        Args:
            xml (str): XML data as a string.
        """
        self._root = etree.fromstring(xml)

    def transform_to_html(self) -> str:
        """
        Transform the XML data to HTML using XSLT.

        Returns:
            str: The transformed HTML content.
        """
        file_path = os.path.join(os.path.dirname(__file__), "search_match.xsl")
        xslt_transform = etree.XSLT(etree.parse(file_path))
        return str(xslt_transform(self._root))
