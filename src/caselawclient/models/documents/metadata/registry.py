from typing import TYPE_CHECKING, Literal, get_type_hints

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
    """Typed registry of metadata objects for a document.

    Annotated attributes are the single source of registered metadata types;
    instances are built by iterating those annotations.
    """

    name: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata

    def __init__(self, document: "Document") -> None:
        for key, metadata_cls in type(self).metadata_types().items():
            setattr(self, key, metadata_cls(document))

    @classmethod
    def metadata_types(cls) -> dict[str, type[Metadata]]:
        """Return attribute name → metadata class for registered fields."""
        return {
            key: metadata_cls
            for key, metadata_cls in get_type_hints(cls).items()
            if isinstance(metadata_cls, type) and issubclass(metadata_cls, Metadata)
        }
