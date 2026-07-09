from typing import Literal, TypedDict

from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
from caselawclient.models.documents.metadata.types.court import CourtMetadata
from caselawclient.models.documents.metadata.types.date import DateMetadata
from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
from caselawclient.models.documents.metadata.types.name import NameMetadata

MetadataAttributeKey = Literal["name", "court", "jurisdiction", "date", "case_number", "categories"]


class DocumentMetadataRegistry(TypedDict):
    name: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata
