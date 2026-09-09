from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Self, Union
from uuid import uuid4

from lxml import etree

from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import Element

MetadataFieldValue = Union["MetadataStringValue", "MetadataDateValue", "MetadataCategoryValue"]


@dataclass(frozen=True)
class MetadataStringValue:
    """Plain-text claim value (title, court, judges, etc)."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self.value.strip())

    def normalised(self) -> Self | None:
        """Return self, or ``None`` when empty after stripping."""
        return self if self.value else None


@dataclass(frozen=True)
class MetadataDateValue:
    """Calendar-date claim value (not a timestamp)."""

    value: date

    def __post_init__(self) -> None:
        if isinstance(self.value, datetime):
            raise TypeError("Expected datetime.date for MetadataDateValue, got datetime")

    def normalised(self) -> Self | None:
        return self


@dataclass(frozen=True)
class MetadataCategoryValue:
    """Structured value for a ``categories`` metadata claim."""

    name: str
    parent: str | None = None

    def __post_init__(self) -> None:
        name = self.name.strip()
        parent = self.parent.strip() if self.parent else None
        if parent == "":
            parent = None
        if not name:
            raise ValueError("category name must be non-empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "parent", parent)

    def normalised(self) -> Self | None:
        return self


class MetadataField:
    """A single metadata claim stored in the MarkLogic ``metadata_fields`` property.

    There is no in-place update API. To change an editor-sourced value, remove the
    existing claim and add a new one (new id and timestamp).
    """

    def __init__(
        self,
        name: str,
        value: MetadataFieldValue,
        source: MetadataSource,
        *,
        id: str | None = None,
        timestamp: datetime | None = None,
        rejected: bool = False,
    ) -> None:
        self.id = id or str(uuid4())
        self.name = name
        self.value = value
        self.source = source
        self.timestamp = timestamp if timestamp is not None else datetime.now(UTC)
        self.rejected = rejected

    def reject(self) -> None:
        """Soft-delete this claim; retained for provenance but excluded from resolution."""
        self.rejected = True

    def restore(self) -> None:
        """Undo a soft-delete so this claim can participate in resolution again."""
        self.rejected = False

    @property
    def as_etree(self) -> Element:
        """Pack this claim into a ``<metadata>`` element for MarkLogic storage."""
        # Lazy import avoids a cycle: field → registry → types → base → field.
        from caselawclient.models.documents.metadata.registry import metadata_class_for_key

        metadata_cls = metadata_class_for_key(self.name)
        if metadata_cls is None:
            raise InvalidMetadataFieldXMLRepresentationException(
                f"Cannot pack metadata field with unknown name '{self.name}'"
            )

        metadata_element = etree.Element(
            "metadata",
            id=self.id,
            name=self.name,
            source=self.source.value,
            timestamp=self.timestamp.isoformat(),
            rejected=str(self.rejected).lower(),
            pack_version=str(metadata_cls.PACK_VERSION),
        )
        metadata_cls.pack_value(self.value, metadata_element)
        return metadata_element

    def __repr__(self) -> str:
        rejected = " (rejected)" if self.rejected else ""
        return f"<MetadataField {self.name}={self.value!r} source={self.source.value}{rejected}>"
