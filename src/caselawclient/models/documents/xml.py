import os

from lxml import etree

from caselawclient.xml_helpers import get_xpath_match_string, get_xpath_match_strings, get_xpath_nodes


def _xslt_path(xslt_file_name: str) -> str:
    from caselawclient.Client import ROOT_DIR

    return os.path.join(ROOT_DIR, "xslt", xslt_file_name)


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

    def get_xpath_nodes(self, xpath: str, namespaces: dict[str, str]) -> list[etree._Element]:
        return get_xpath_nodes(self.xml_as_tree, xpath, namespaces)

    def _modified(
        self,
        xslt: str,
        **values: str,
    ) -> bytes:
        """XSLT transform this XML, given a stylesheet"""
        passable_values = {k: etree.XSLT.strparam(v) for k, v in values.items()}
        xslt_transform = etree.XSLT(etree.fromstring(xslt))
        noncanonical_xml = xslt_transform(self.xml_as_tree, profile_run=False, **passable_values)
        return etree.tostring(noncanonical_xml, method="c14n2")

    def apply_xslt(self, xslt_filename: str, **values: str) -> bytes:
        """XSLT transform this XML, given a path to a stylesheet"""
        full_xslt_filename = _xslt_path(xslt_filename)
        with open(full_xslt_filename) as f:
            xslt = f.read()
        return self._modified(xslt, **values)
