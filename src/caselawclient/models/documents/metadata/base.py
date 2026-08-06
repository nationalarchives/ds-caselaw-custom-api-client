from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from caselawclient.models.documents.metadata.fields.field import (
    MetadataCategoryValue,
    MetadataField,
    MetadataFieldValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource

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

    LOGIC_VERSION: ClassVar[int] = 1
    """Bump when this field's body-extraction / materialisation rules change."""

    def __init__(self, document: "Document") -> None:
        self.document = document

    def _resolve_claims(self) -> "ResolvedMetadataField":
        return self.document.metadata_fields.resolve(self.key)

    @staticmethod
    def _value_resolves(value: MetadataFieldValue) -> bool:
        if isinstance(value, str):
            return bool(value)
        if isinstance(value, MetadataCategoryValue):
            return bool(value.name)
        return False

    def _materialise_document_values(self, values: Iterable[MetadataFieldValue]) -> None:
        """Add DOCUMENT claims for each resolving value that is not already present."""
        for value in values:
            if not self._value_resolves(value):
                continue
            if self.document.metadata_fields.has_claim(self.key, value, MetadataSource.DOCUMENT):
                continue
            self.document.metadata_fields.add(
                MetadataField(
                    name=self.key,
                    value=value,
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


class MultipleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def values(self) -> list[T]: ...
