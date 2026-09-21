import os

from lxml import etree

from caselawclient.xml_helpers import (
    DEFAULT_NAMESPACES,
    Element,
    get_xpath_match_string,
    get_xpath_match_strings,
    get_xpath_nodes,
)


def _xslt_path(xslt_file_name: str) -> str:
    from caselawclient.Client import ROOT_DIR

    return os.path.join(ROOT_DIR, "xslt", xslt_file_name)


AKN_META_CHILDREN_ORDER = (
    "identification",
    "publication",
    "classification",
    "lifecycle",
    "workflow",
    "analysis",
    "temporalData",
    "references",
    "notes",
    "proprietary",
    "presentation",
)


def _local_name_in_namespace(element: Element, namespace: str) -> str | None:
    tag = element.tag
    if not isinstance(tag, str) or not tag.startswith("{"):
        return None
    ns_uri, local_name = tag[1:].split("}", 1)
    if ns_uri != namespace:
        return None
    return local_name


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

    def get_xpath_match_string(self, xpath: str) -> str:
        return get_xpath_match_string(self.xml_as_tree, xpath, DEFAULT_NAMESPACES)

    def get_xpath_match_strings(self, xpath: str) -> list[str]:
        return get_xpath_match_strings(self.xml_as_tree, xpath, DEFAULT_NAMESPACES)

    def get_xpath_nodes(self, xpath: str) -> list[Element]:
        return get_xpath_nodes(self.xml_as_tree, xpath, DEFAULT_NAMESPACES)

    def get_single_xpath_node(self, xpath: str) -> Element:
        """Return exactly one xpath node, and raise an exception if either it doesn't exist or exists multiple times."""

        nodes = self.get_xpath_nodes(xpath)

        if not nodes:
            raise ValueError(f"No element found at xpath: {xpath}")
        if len(nodes) > 1:
            raise ValueError(f"XPath expression matches {len(nodes)} elements, expected exactly 1: {xpath}")

        return nodes[0]

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

    def get_or_create_element(self, parent_xpath: str, element_name: str, namespace: str | None = None) -> Element:
        """
        Get an existing child element or create a new one.

        :param parent_xpath: XPath expression to find the parent element
        :param element_name: Name of the child element (local name without prefix)
        :param namespace: Optional namespace URI. Must exist in DEFAULT_NAMESPACES values if provided.
        :return: The existing or newly created element
        :raises ValueError: If parent not found at xpath, if multiple parents found, or if namespace not in DEFAULT_NAMESPACES
        """
        parent = self.get_single_xpath_node(parent_xpath)

        # Validate namespace if provided
        if namespace is not None:
            valid_namespaces = set(DEFAULT_NAMESPACES.values())
            if namespace not in valid_namespaces:
                raise ValueError(f"Namespace not in DEFAULT_NAMESPACES: {namespace}")
            qname = etree.QName(namespace, element_name)
        else:
            qname = etree.QName(element_name)

        # Safety check: ensure no duplicate children exist
        existing_children = parent.findall(qname)
        if len(existing_children) > 1:
            raise ValueError(
                f"Multiple child elements with name {element_name} already exist in parent at {parent_xpath}"
            )

        # Check if child already exists
        existing = existing_children[0] if existing_children else None
        if existing is not None:
            return existing

        # Create new child element
        new_element = etree.SubElement(parent, qname)
        return new_element

    def get_or_create_element_in_child_order(
        self,
        parent_xpath: str,
        element_name: str,
        namespace: str,
        child_order: tuple[str, ...],
    ) -> Element:
        """Like ``get_or_create_element``, but insert new children at the schema position in ``child_order``."""
        if namespace not in set(DEFAULT_NAMESPACES.values()):
            raise ValueError(f"Namespace not in DEFAULT_NAMESPACES: {namespace}")
        if element_name not in child_order:
            raise ValueError(f"Element {element_name!r} is not listed in child_order")

        parent = self.get_single_xpath_node(parent_xpath)
        qname = etree.QName(namespace, element_name)
        existing_children = parent.findall(qname)
        if len(existing_children) > 1:
            raise ValueError(
                f"Multiple child elements with name {element_name} already exist in parent at {parent_xpath}"
            )
        if existing_children:
            return existing_children[0]

        return self.insert_element_in_child_order(parent_xpath, element_name, namespace, child_order)

    def insert_element_in_child_order(
        self,
        parent_xpath: str,
        element_name: str,
        namespace: str,
        child_order: tuple[str, ...],
    ) -> Element:
        """Insert a new child at the schema position in ``child_order`` (repeatable elements allowed)."""
        if namespace not in set(DEFAULT_NAMESPACES.values()):
            raise ValueError(f"Namespace not in DEFAULT_NAMESPACES: {namespace}")
        if element_name not in child_order:
            raise ValueError(f"Element {element_name!r} is not listed in child_order")

        parent = self.get_single_xpath_node(parent_xpath)
        qname = etree.QName(namespace, element_name)
        target_index = child_order.index(element_name)
        insert_at = len(parent)
        for index, child in enumerate(parent):
            local_name = _local_name_in_namespace(child, namespace)
            if local_name is None or local_name not in child_order:
                continue
            if child_order.index(local_name) > target_index:
                insert_at = index
                break

        new_element = etree.Element(qname)
        parent.insert(insert_at, new_element)
        return new_element

    def set_element_attribute(self, element: Element, attribute_name: str, attribute_value: str) -> None:
        """
        Set an attribute on an element.

        :param element: The element to modify
        :param attribute_name: Name of the attribute to set
        :param attribute_value: Value to set
        """
        element.set(attribute_name, attribute_value)

    def set_element_value(
        self,
        element: Element,
        value: str,
    ) -> None:
        """
        Set an element's text value.

        :param element: The element to modify
        :param value: Value to set as text content
        """
        element.text = value

    def replace_child_elements(
        self,
        parent_xpath: str,
        child_local_name: str,
        namespace: str,
        new_elements: list[Element],
    ) -> None:
        """Remove all namespaced children with ``child_local_name``, then append ``new_elements``."""
        if namespace not in set(DEFAULT_NAMESPACES.values()):
            raise ValueError(f"Namespace not in DEFAULT_NAMESPACES: {namespace}")
        parent = self.get_single_xpath_node(parent_xpath)
        qname = etree.QName(namespace, child_local_name)
        for child in list(parent.findall(qname)):
            parent.remove(child)
        for element in new_elements:
            parent.append(element)
