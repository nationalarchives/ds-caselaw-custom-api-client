from lxml import etree

from caselawclient.xml_helpers import get_xpath_match_string, get_xpath_match_strings


class NonXMLDocumentError(Exception):
    """A document cannot be parsed as XML."""


class XML:
    """
    A class for interacting with the raw XML of a document.
    """

    def __init__(self, xml_bytestring: bytes):
        """
        :raises NonXMLDocumentError: This document is not valid XML
        """
        try:
            self.xml_as_tree: etree._Element = etree.fromstring(xml_bytestring)
        except etree.XMLSyntaxError:
            raise NonXMLDocumentError

    @property
    def xml_as_string(self) -> str:
        """
        :return: A string representation of this document's XML tree.
        """
        return str(etree.tostring(self.xml_as_tree).decode(encoding="utf-8"))

    @property
    def root_element(self) -> str:
        return str(self.xml_as_tree.tag)

    def get_xpath_match_string(self, xpath: str, namespaces: dict[str, str]) -> str:
        return get_xpath_match_string(self.xml_as_tree, xpath, namespaces)

    def get_xpath_match_strings(
        self,
        xpath: str,
        namespaces: dict[str, str],
    ) -> list[str]:
        return get_xpath_match_strings(self.xml_as_tree, xpath, namespaces)
