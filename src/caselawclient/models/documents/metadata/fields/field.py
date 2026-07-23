from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional, Union
from uuid import uuid4

from lxml import etree

from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import Element

MetadataFieldValue = Union[str, "MetadataCategoryValue"]


@dataclass(frozen=True)
class MetadataCategoryValue:
    """Structured value for a ``category`` metadata claim."""

    name: str
    parent: str | None = None


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
        id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
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

    @property
    def as_etree(self) -> Element:
        """Pack this claim into a ``<metadata>`` element for MarkLogic storage."""
        metadata_element = etree.Element(
            "metadata",
            id=self.id,
            name=self.name,
            source=self.source.value,
            timestamp=self.timestamp.isoformat(),
            rejected=str(self.rejected).lower(),
        )

        if isinstance(self.value, MetadataCategoryValue):
            name_element = etree.SubElement(metadata_element, "name")
            name_element.text = self.value.name
            parent_element = etree.SubElement(metadata_element, "parent")
            if self.value.parent is not None:
                parent_element.text = self.value.parent
        else:
            metadata_element.text = self.value

        return metadata_element

    def __repr__(self) -> str:
        rejected = " (rejected)" if self.rejected else ""
        return f"<MetadataField {self.name}={self.value!r} source={self.source.value}{rejected}>"
