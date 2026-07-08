from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

T = TypeVar("T")


class Metadata(ABC):
    key: ClassVar[str]
    title: ClassVar[str]
    description: ClassVar[str]

    def __init__(self, document: "Document") -> None:
        self.document = document


class SingleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def value(self) -> T: ...


class MultipleMetadata(Metadata, Generic[T]):
    @property
    @abstractmethod
    def values(self) -> list[T]: ...
