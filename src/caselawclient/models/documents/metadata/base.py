from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import date
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar, cast

from caselawclient.models.documents.metadata.fields.field import (
    MetadataDateValue,
    MetadataField,
    MetadataFieldValue,
    MetadataStringValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.fields.unpack_helpers import stripped_element_text
from caselawclient.xml_helpers import Element

if TYPE_CHECKING:
    from caselawclient.models.documents import Document
    from caselawclient.models.documents.metadata.fields.resolution import ResolvedMetadataField

T = TypeVar("T")


class Metadata(ABC):
    key: ClassVar[str]
    title: ClassVar[str]
    description: ClassVar[str]

    editable: ClassVar[bool] = False
    """Should editors be allowed to manually edit this metadata field?"""

    LOGIC_VERSION: ClassVar[int] = 2
    """Bump when this field's body-extraction / materialisation rules change."""

    PACK_VERSION: ClassVar[int] = 1
    """Bump when this field's packed XML value shape changes."""

    def __init__(self, document: "Document") -> None:
        self.document = document

    def _resolve_claims(self) -> "ResolvedMetadataField":
        return self.document.metadata_fields.resolve(self.key)

    @classmethod
    def validate_value(cls, value: MetadataFieldValue) -> None:
        """Raise ``TypeError`` if ``value`` is not valid for this claim key."""
        if not isinstance(value, MetadataStringValue):
            raise TypeError(f"Expected MetadataStringValue for '{cls.key}', got {type(value).__name__}")

    @classmethod
    def pack_value(cls, value: MetadataFieldValue, into: Element) -> None:
        """Write ``value`` into a ``<metadata>`` element (text or child elements)."""
        cls.validate_value(value)
        into.text = cast(MetadataStringValue, value).value

    @classmethod
    def unpack_value(cls, metadata_xml: Element, pack_version: int) -> MetadataFieldValue:
        """Read the Python claim value from a ``<metadata>`` element.

        Implementations must only raise
        ``InvalidMetadataFieldXMLRepresentationException`` for invalid wire
        data (wrapping other ``ValueError``s). Strip text nodes before parse.
        """
        return MetadataStringValue(stripped_element_text(metadata_xml))

    def _materialise_document_values(self, values: Iterable[MetadataFieldValue]) -> None:
        """Add DOCUMENT claims for each resolving value that is not already present."""
        for value in values:
            normalised = value.normalised()
            if normalised is None:
                continue
            if self.document.metadata_fields.has_claim(self.key, normalised, MetadataSource.DOCUMENT):
                continue
            self.document.metadata_fields.add(
                MetadataField(
                    name=self.key,
                    value=normalised,
                    source=MetadataSource.DOCUMENT,
                )
            )

    def materialise_body_claims(self) -> None:
        """Yank body-derived values into DOCUMENT claims (in-memory, additive)."""
        raise NotImplementedError(f"{type(self).__name__} does not implement materialise_body_claims")


class SingleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def value(self) -> T: ...

    def _string_value(self, body: str, *, when_suppressed: str = "") -> str:
        """Resolve a string claim, falling back to ``body`` when none exist."""
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return body
        if resolved.value is None:
            return when_suppressed
        self.validate_value(resolved.value)
        return cast(MetadataStringValue, resolved.value).value

    def _optional_string_value(self, body: str | None) -> str | None:
        """Like ``_string_value``, but suppressed/empty claims resolve to ``None``."""
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return body
        if resolved.value is None:
            return None
        self.validate_value(resolved.value)
        return cast(MetadataStringValue, resolved.value).value or None

    def _date_value(self, body: date | None) -> date | None:
        """Resolve a date claim, falling back to ``body`` when none exist."""
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return body
        if resolved.value is None:
            return None
        self.validate_value(resolved.value)
        return cast(MetadataDateValue, resolved.value).value


class MultipleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def values(self) -> list[T]: ...
