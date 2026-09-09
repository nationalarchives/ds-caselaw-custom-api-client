"""Shared helpers for metadata claim XML unpacking.

``unpack_value`` implementations and the claim envelope parser should surface
invalid wire data as ``InvalidMetadataFieldXMLRepresentationException`` only —
never leak raw ``ValueError`` from constructors or parsers.
"""

from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.xml_helpers import Element


def stripped_element_text(element: Element | None) -> str:
    """Return ``element.text`` stripped, or ``""`` when missing/empty."""
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_pack_version(pack_version_attr: str | None) -> int:
    """Parse a ``pack_version`` attribute; missing means version 1."""
    if pack_version_attr is None:
        return 1
    try:
        pack_version = int(pack_version_attr)
    except ValueError as exc:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: unparsable pack_version '{pack_version_attr}'"
        ) from exc
    if pack_version < 1:
        raise InvalidMetadataFieldXMLRepresentationException(
            f"Metadata field XML representation is not valid: pack_version must be >= 1, got {pack_version}"
        )
    return pack_version
