from typing import cast

from lxml import etree

from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataFieldValue
from caselawclient.models.documents.metadata.fields.unpack_helpers import stripped_element_text
from caselawclient.types import DocumentCategory
from caselawclient.xml_helpers import Element


def document_categories_from_field_values(values: list[MetadataFieldValue]) -> list[DocumentCategory]:
    """Build a ``DocumentCategory`` tree from flat category metadata claim values.

    Duplicate category names (e.g. the same category claimed by multiple sources)
    are de-duplicated with first-seen order winning.
    """
    category_values = [value for value in values if isinstance(value, MetadataCategoryValue)]

    categories: dict[str, DocumentCategory] = {}
    children_map: dict[str, list[DocumentCategory]] = {}
    top_level_order: list[str] = []

    for category_value in category_values:
        if category_value.name in categories:
            continue

        category = DocumentCategory(name=category_value.name)
        categories[category_value.name] = category

        if category_value.parent:
            children_map.setdefault(category_value.parent, []).append(category)
        else:
            top_level_order.append(category_value.name)

    for parent, subcategories in children_map.items():
        if parent in categories:
            categories[parent].subcategories.extend(subcategories)

    return [categories[name] for name in top_level_order]


def category_claim_values_from_document_categories(
    categories: list[DocumentCategory],
    parent: str | None = None,
) -> list[MetadataCategoryValue]:
    """Flatten a category tree into claim values suitable for DOCUMENT materialisation."""
    values: list[MetadataCategoryValue] = []
    for category in categories:
        child_parent: str | None
        if category.name.strip():
            values.append(MetadataCategoryValue(name=category.name, parent=parent))
            child_parent = category.name
        else:
            child_parent = parent
        values.extend(category_claim_values_from_document_categories(category.subcategories, parent=child_parent))
    return values


class CategoriesMetadata(MultipleMetadata[DocumentCategory]):
    key = "categories"
    title = "Categories"
    description = "The categories assigned to the document."

    @property
    def values(self) -> list[DocumentCategory]:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.categories
        return document_categories_from_field_values(resolved.values)

    def materialise_body_claims(self) -> None:
        self._materialise_document_values(category_claim_values_from_document_categories(self.document.body.categories))

    @classmethod
    def validate_value(cls, value: MetadataFieldValue) -> None:
        if not isinstance(value, MetadataCategoryValue):
            raise TypeError(f"Expected MetadataCategoryValue for '{cls.key}', got {type(value).__name__}")

    @classmethod
    def pack_value(cls, value: MetadataFieldValue, into: Element) -> None:
        cls.validate_value(value)
        category = cast(MetadataCategoryValue, value)
        name_element = etree.SubElement(into, "name")
        name_element.text = category.name
        parent_element = etree.SubElement(into, "parent")
        if category.parent is not None:
            parent_element.text = category.parent

    @classmethod
    def unpack_value(cls, metadata_xml: Element, pack_version: int) -> MetadataFieldValue:
        name_child = metadata_xml.find("name")
        if name_child is None:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: category name element not present"
            )
        category_name = stripped_element_text(name_child)
        if not category_name:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: category name not present or empty"
            )
        parent_child = metadata_xml.find("parent")
        parent_text = stripped_element_text(parent_child)
        parent = parent_text or None
        return MetadataCategoryValue(name=category_name, parent=parent)
