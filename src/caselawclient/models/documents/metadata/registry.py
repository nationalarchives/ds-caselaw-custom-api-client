from typing import TYPE_CHECKING, ClassVar, Iterator, Literal

from caselawclient.models.documents.metadata.base import Metadata
from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
from caselawclient.models.documents.metadata.types.court import CourtMetadata
from caselawclient.models.documents.metadata.types.date import DateMetadata
from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
from caselawclient.models.documents.metadata.types.name import NameMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

MetadataAttributeKey = Literal["name", "court", "jurisdiction", "date", "case_number", "categories"]


class DocumentMetadataRegistry:
    """Typed registry of metadata objects for a document."""

    METADATA_TYPES: ClassVar[tuple[type[Metadata], ...]] = (
        NameMetadata,
        CourtMetadata,
        JurisdictionMetadata,
        DateMetadata,
        CaseNumberMetadata,
        CategoriesMetadata,
    )

    name: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata

    def __init__(self, document: "Document") -> None:
        self._by_key: dict[str, Metadata] = {}
        for metadata_cls in type(self).METADATA_TYPES:
            key = metadata_cls.key
            if key in self._by_key:
                msg = f"Duplicate metadata key {key!r} registered on {type(self).__name__}"
                raise ValueError(msg)
            metadata = metadata_cls(document)
            self._by_key[key] = metadata
            setattr(self, key, metadata)

    def __getitem__(self, key: str) -> Metadata:
        return self._by_key[key]

    def get(self, key: str, default: Metadata | None = None) -> Metadata | None:
        return self._by_key.get(key, default)

    def keys(self) -> set[str]:
        return set(self._by_key.keys())

    def values(self) -> list[Metadata]:
        return list(self._by_key.values())

    def items(self) -> list[tuple[str, Metadata]]:
        return list(self._by_key.items())

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_key)

    def __len__(self) -> int:
        return len(self._by_key)

    def __contains__(self, key: object) -> bool:
        return key in self._by_key
