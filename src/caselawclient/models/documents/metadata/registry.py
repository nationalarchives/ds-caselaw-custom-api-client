from typing import TYPE_CHECKING, ClassVar, Literal

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
        seen_keys: set[str] = set()
        for metadata_cls in type(self).METADATA_TYPES:
            key = metadata_cls.key
            if key in seen_keys:
                msg = f"Duplicate metadata key {key!r} registered on {type(self).__name__}"
                raise ValueError(msg)
            seen_keys.add(key)
            setattr(self, key, metadata_cls(document))
