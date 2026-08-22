import warnings
from datetime import datetime

from caselawclient.models.documents.metadata.fields.collection import MetadataFieldsCollection
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.fields.unpack_helpers import parse_pack_version
from caselawclient.models.utilities.dates import require_aware_utc
from caselawclient.xml_helpers import Element


def unpack_all_metadata_fields_from_etree(
    metadata_fields_etree: Element | None,
) -> MetadataFieldsCollection:
    """Unpack a ``<metadata_fields>`` property element into a collection."""
    collection = MetadataFieldsCollection()
    if metadata_fields_etree is None:
        return collection

    for metadata_element in metadata_fields_etree.findall("metadata"):
        field = unpack_a_metadata_field_from_etree(metadata_element)
        if field is not None:
            collection.add(field)

    return collection


def unpack_a_metadata_field_from_etree(metadata_xml: Element) -> MetadataField | None:
    """Unpack a single ``<metadata>`` element into a ``MetadataField``.

    Unknown claim ``name`` values warn and return ``None`` so the rest of the
    collection can still load.
    """
    # Lazy import avoids a cycle: unpacker → registry → types → base → field → …
    from caselawclient.models.documents.metadata.registry import metadata_class_for_key

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

    metadata_cls = metadata_class_for_key(name)
    if metadata_cls is None:
        warnings.warn(
            f"Skipping metadata field with unknown name '{name}'",
            stacklevel=2,
        )
        return None

    try:
        source = MetadataSource(source_value)
    except ValueError as exc:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: unknown source '{source_value}'"
        ) from exc

    try:
        timestamp = require_aware_utc(datetime.fromisoformat(timestamp_value), name="timestamp")
    except ValueError as exc:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: unparsable timestamp '{timestamp_value}'"
        ) from exc

    rejected_attr = metadata_xml.get("rejected")
    rejected = rejected_attr is not None and rejected_attr.lower() == "true"

    pack_version = parse_pack_version(metadata_xml.get("pack_version"))

    try:
        value = metadata_cls.unpack_value(metadata_xml, pack_version)
    except InvalidMetadataFieldXMLRepresentationException:
        raise
    except ValueError as exc:
        # Safety net: value constructors / parsers should already raise
        # InvalidMetadataFieldXMLRepresentationException, but wrap leaks.
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: {exc}"
        ) from exc

    return MetadataField(
        name=name,
        value=value,
        source=source,
        id=field_id,
        timestamp=timestamp,
        rejected=rejected,
    )
