from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

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

    def __init__(self, document: "Document") -> None:
        self.document = document

    def _resolve_claims(self) -> "ResolvedMetadataField":
        return self.document.metadata_fields.resolve(self.key)


class SingleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def value(self) -> T: ...


class MultipleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def values(self) -> list[T]: ...
