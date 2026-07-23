from datetime import datetime
from typing import Optional

from caselawclient.models.documents.metadata.fields.collection import MetadataFieldsCollection
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import Element


def unpack_all_metadata_fields_from_etree(
    metadata_fields_etree: Optional[Element],
) -> MetadataFieldsCollection:
    """Unpack a ``<metadata_fields>`` property element into a collection."""
    collection = MetadataFieldsCollection()
    if metadata_fields_etree is None:
        return collection

    for metadata_element in metadata_fields_etree.findall("metadata"):
        collection.add(unpack_a_metadata_field_from_etree(metadata_element))

    return collection


def unpack_a_metadata_field_from_etree(metadata_xml: Element) -> MetadataField:
    """Unpack a single ``<metadata>`` element into a ``MetadataField``."""
    field_id = metadata_xml.get("id")
    name = metadata_xml.get("name")
    source_value = metadata_xml.get("source")
    timestamp_value = metadata_xml.get("timestamp")

    if not field_id:
        raise InvalidMetadataFieldXMLRepresentationException(
            "Metadata field XML representation is not valid: id not present or empty"
        )
    if not name:
        raise InvalidMetadataFieldXMLRepresentationException(
            "Metadata field XML representation is not valid: name not present or empty"
        )
    if not source_value:
        raise InvalidMetadataFieldXMLRepresentationException(
            "Metadata field XML representation is not valid: source not present or empty"
        )
    if not timestamp_value:
        raise InvalidMetadataFieldXMLRepresentationException(
            "Metadata field XML representation is not valid: timestamp not present or empty"
        )

    try:
        source = MetadataSource(source_value)
    except ValueError as exc:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: unknown source '{source_value}'"
        ) from exc

    try:
        timestamp = datetime.fromisoformat(timestamp_value)
    except ValueError as exc:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: unparsable timestamp '{timestamp_value}'"
        ) from exc

    rejected_attr = metadata_xml.get("rejected")
    rejected = rejected_attr is not None and rejected_attr.lower() == "true"

    name_child = metadata_xml.find("name")
    if name_child is not None:
        category_name = name_child.text
        if not category_name:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: category name not present or empty"
            )
        parent_child = metadata_xml.find("parent")
        parent: str | None
        if parent_child is None or parent_child.text is None or parent_child.text == "":
            parent = None
        else:
            parent = parent_child.text
        value: MetadataCategoryValue | str = MetadataCategoryValue(name=category_name, parent=parent)
    else:
        value = metadata_xml.text or ""

    return MetadataField(
        name=name,
        value=value,
        source=source,
        id=field_id,
        timestamp=timestamp,
        rejected=rejected,
    )
