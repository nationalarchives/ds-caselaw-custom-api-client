from enum import Enum

from lxml import etree

from caselawclient.models.documents.metadata.fields.exceptions import (
    MetadataFieldEmptyValueException,
    MetadataFieldIdCollisionException,
    MetadataFieldKeyMismatchException,
    MetadataFieldRemovalNotAllowedException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataField, MetadataFieldValue
from caselawclient.models.documents.metadata.fields.resolution import ResolvedMetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import Element


class MetadataFieldAddResult(Enum):
    """Outcome of ``MetadataFieldsCollection.add``."""

    ADDED = "added"
    ALREADY_PRESENT = "already_present"


class MetadataFieldsCollection(dict[str, MetadataField]):
    """Collection of metadata claims keyed by claim id."""

    def add(self, field: MetadataField) -> MetadataFieldAddResult:
        """Insert ``field``, or noop if an equivalent claim already exists.

        Equivalence is ``name`` + ``value`` + ``source`` (``rejected`` is ignored,
        so matching a rejected claim does not revive it). Empty values raise.
        A reused id with a different payload raises
        ``MetadataFieldIdCollisionException``.

        Loading via unpack also goes through ``add``, so duplicate stored claims
        with the same equivalence key are deduped on load.
        """
        if field.value.normalised() is None:
            raise MetadataFieldEmptyValueException(f"Cannot add metadata claim '{field.name}': value is empty")

        existing_by_id = self.get(field.id)
        if existing_by_id is not None:
            if self._same_payload(existing_by_id, field):
                return MetadataFieldAddResult.ALREADY_PRESENT
            raise MetadataFieldIdCollisionException(
                f"Metadata claim id {field.id} already exists with a different payload"
            )

        if self.has_claim(field.name, field.value, field.source):
            return MetadataFieldAddResult.ALREADY_PRESENT

        dict.__setitem__(self, field.id, field)
        return MetadataFieldAddResult.ADDED

    @staticmethod
    def _same_payload(existing: MetadataField, field: MetadataField) -> bool:
        return existing.name == field.name and existing.value == field.value and existing.source is field.source

    def __setitem__(self, key: str, field: MetadataField) -> None:
        if key != field.id:
            raise MetadataFieldKeyMismatchException(f"Collection key {key!r} does not match claim id {field.id!r}")
        self.add(field)

    def by_name(self, name: str) -> list[MetadataField]:
        return [field for field in self.values() if field.name == name]

    def has_claim(self, name: str, value: MetadataFieldValue, source: MetadataSource) -> bool:
        """True if any claim (including rejected) matches name, value, and source."""
        return any(field.value == value and field.source is source for field in self.by_name(name))

    def resolve(self, name: str) -> ResolvedMetadataField:
        return ResolvedMetadataField(name=name, claims=self.by_name(name))

    def reject(self, field_id: str) -> None:
        """Soft-delete a claim by id."""
        self[field_id].reject()

    def restore(self, field_id: str) -> None:
        """Undo soft-delete for a claim by id."""
        self[field_id].restore()

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
