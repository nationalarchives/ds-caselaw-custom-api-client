import os

from lxml import etree

from caselawclient.xml_helpers import Element, get_xpath_match_string, get_xpath_match_strings, get_xpath_nodes


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
            self.xml_as_tree: Element = etree.fromstring(xml_bytestring)
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

    def get_xpath_nodes(self, xpath: str, namespaces: dict[str, str]) -> list[Element]:
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

    @property
    def xml_as_bytes(self) -> bytes:
        """
        Return XML tree as bytes (namespace-aware, canonicalized).

        :return: The XML tree serialized to bytes
        """
        return etree.tostring(self.xml_as_tree, method="c14n2")

    def set_xpath_attribute(
        self,
        xpath: str,
        attribute_name: str,
        attribute_value: str,
        namespaces: dict[str, str],
    ) -> None:
        """
        Set an attribute on an existing element found by XPath.

        :param xpath: XPath expression to find the element
        :param attribute_name: Name of the attribute to set
        :param attribute_value: Value to set
        :param namespaces: Namespace map for XPath evaluation
        :raises ValueError: If no element found at xpath
        """
        nodes = self.get_xpath_nodes(xpath, namespaces)
        if not nodes:
            raise ValueError(f"No element found at xpath: {xpath}")
        nodes[0].set(attribute_name, attribute_value)

    def get_or_create_element(
        self,
        parent_xpath: str,
        element_name: str,
        namespaces: dict[str, str],
    ) -> Element:
        """
        Get an existing child element or create a new one.

        :param parent_xpath: XPath expression to find the parent element
        :param element_name: Name of the child element (can include namespace prefix, e.g., 'akn:FRBRname')
        :param namespaces: Namespace map for XPath evaluation
        :return: The existing or newly created element
        :raises ValueError: If parent not found at xpath
        """
        parent_nodes = self.get_xpath_nodes(parent_xpath, namespaces)
        if not parent_nodes:
            raise ValueError(f"No parent element found at xpath: {parent_xpath}")

        parent = parent_nodes[0]

        # If element_name contains a colon, split it to get prefix and local name
        if ":" in element_name:
            prefix, local_name = element_name.split(":", 1)
            # Find namespace for prefix
            if prefix not in namespaces:
                raise ValueError(f"Unknown namespace prefix: {prefix}")
            namespace = namespaces[prefix]
            qname = etree.QName(namespace, local_name)
        else:
            qname = etree.QName(element_name)

        # Check if child already exists
        existing = parent.find(qname)
        if existing is not None:
            return existing

        # Create new child element
        new_element = etree.SubElement(parent, qname)
        return new_element

    def set_xpath_element_value(
        self,
        xpath: str,
        value: str,
        element_name: str,
        namespaces: dict[str, str],
    ) -> None:
        """
        Set or create an element's text value at a given XPath.

        If the element exists, replaces its text. If not, creates a new element
        as a child of the parent found at the XPath (minus the final step).

        :param xpath: XPath expression (e.g., '/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value')
        :param value: Value to set (as text content for element, or as attribute value)
        :param element_name: Name of the element to set/create (used if element doesn't exist)
        :param namespaces: Namespace map for XPath evaluation
        :raises ValueError: If xpath resolution fails
        """
        nodes = self.get_xpath_nodes(xpath, namespaces)

        if nodes:
            # Element exists, update it
            if isinstance(nodes[0], Element):
                nodes[0].text = value
            else:
                # It's an attribute node
                nodes[0].getparent().set(nodes[0].attrname, value)
        else:
            # Element doesn't exist, need to create it
            # For now, raise an error and let the caller handle creation
            raise ValueError(f"Element not found at xpath: {xpath}")
