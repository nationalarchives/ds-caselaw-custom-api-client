from typing import cast

from lxml import etree

from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataFieldValue, MetadataPartyValue
from caselawclient.models.documents.metadata.fields.unpack_helpers import stripped_element_text
from caselawclient.xml_helpers import Element


def party_values_from_field_values(values: list[MetadataFieldValue]) -> list[MetadataPartyValue]:
    """Extract party claim values, de-duplicating with first-seen order winning.

    Non-party claim values are ignored. The same party claimed by multiple
    sources appears once in the facade list; claims themselves are unchanged.
    """
    parties: list[MetadataPartyValue] = []
    for value in values:
        if not isinstance(value, MetadataPartyValue):
            continue
        if value in parties:
            continue
        parties.append(value)
    return parties


class PartiesMetadata(MultipleMetadata[MetadataPartyValue]):
    key = "parties"
    title = "Parties"
    description = "The parties involved in the case, each with an optional role."
    editable = True
    LOGIC_VERSION = 1

    @property
    def values(self) -> list[MetadataPartyValue]:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.parties
        return party_values_from_field_values(resolved.values)

    def materialise_body_claims(self) -> None:
        """Yank body ``uk:party`` nodes into DOCUMENT claims (additive, idempotent)."""
        self._materialise_document_values(self.document.body.parties)

    @classmethod
    def validate_value(cls, value: MetadataFieldValue) -> None:
        if not isinstance(value, MetadataPartyValue):
            raise TypeError(f"Expected MetadataPartyValue for '{cls.key}', got {type(value).__name__}")

    @classmethod
    def pack_value(cls, value: MetadataFieldValue, into: Element) -> None:
        cls.validate_value(value)
        party = cast(MetadataPartyValue, value)
        name_element = etree.SubElement(into, "name")
        name_element.text = party.name
        if party.role is not None:
            role_element = etree.SubElement(into, "role")
            role_element.text = party.role

    @classmethod
    def unpack_value(cls, metadata_xml: Element, pack_version: int) -> MetadataFieldValue:
        name_child = metadata_xml.find("name")
        if name_child is None:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: party name element not present"
            )
        party_name = stripped_element_text(name_child)
        if not party_name:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: party name not present or empty"
            )
        role_child = metadata_xml.find("role")
        role_text = stripped_element_text(role_child)
        role = role_text or None
        return MetadataPartyValue(name=party_name, role=role)
