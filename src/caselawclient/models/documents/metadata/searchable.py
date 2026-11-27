"""Denormalised metadata that MarkLogic search reads from the ``searchable-metadata`` property."""

from lxml import etree

from caselawclient.xml_helpers import Element

SEARCHABLE_METADATA_PROPERTY = "searchable-metadata"


def build_searchable_metadata_etree(judges: list[str]) -> Element:
    root = etree.Element(SEARCHABLE_METADATA_PROPERTY)
    for judge in judges:
        etree.SubElement(root, "judge").text = judge
    return root
