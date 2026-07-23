from lxml import etree

from caselawclient.models.documents.metadata.fields.exceptions import (
    MetadataFieldRemovalNotAllowedException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataField
from caselawclient.models.documents.metadata.fields.resolution import ResolvedMetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.types import SuccessFailureMessageTuple
from caselawclient.xml_helpers import Element


class MetadataFieldsCollection(dict[str, MetadataField]):
    """Collection of metadata claims keyed by claim id."""

    def add(self, field: MetadataField) -> None:
        self[field.id] = field

    def by_name(self, name: str) -> list[MetadataField]:
        return [field for field in self.values() if field.name == name]

    def resolve(self, name: str) -> ResolvedMetadataField:
        return ResolvedMetadataField(name=name, claims=self.by_name(name))

    def reject(self, field_id: str) -> None:
        """Soft-delete a claim by id."""
        self[field_id].reject()

    def remove(self, field_id: str) -> None:
        """Hard-remove a claim. Only allowed for editor-sourced claims.

        To change an editor-sourced value, remove the existing claim and add a
        new one with a fresh id and timestamp.
        """
        field = self[field_id]
        if field.source is not MetadataSource.EDITOR:
            raise MetadataFieldRemovalNotAllowedException(
                f"Cannot hard-remove metadata claim {field_id} with source "
                f"'{field.source.value}'; use reject() to soft-delete document or external claims."
            )
        del self[field_id]

    @property
    def as_etree(self) -> Element:
        """Return an etree representation of all metadata claims."""
        root = etree.Element("metadata_fields")
        for field in self.values():
            root.append(field.as_etree)
        return root

    def validate_ids_match_keys(self) -> SuccessFailureMessageTuple:
        for key, field in self.items():
            if key != field.id:
                return SuccessFailureMessageTuple(
                    False,
                    [f"Key of {field} in MetadataFieldsCollection is {key} not {field.id}"],
                )
        return SuccessFailureMessageTuple(True, [])
