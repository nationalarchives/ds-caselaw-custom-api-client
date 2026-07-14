from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
from caselawclient.models.documents.metadata.types.court import CourtMetadata
from caselawclient.models.documents.metadata.types.date import DateMetadata
from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
from caselawclient.models.documents.metadata.types.name import NameMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents import Document


class DocumentMetadataRegistry:
    """Typed registry of metadata objects for a document."""

    name: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata

    def __init__(self, document: "Document") -> None:
        self.name = NameMetadata(document)
        self.court = CourtMetadata(document)
        self.jurisdiction = JurisdictionMetadata(document)
        self.date = DateMetadata(document)
        self.case_number = CaseNumberMetadata(document)
        self.categories = CategoriesMetadata(document)
