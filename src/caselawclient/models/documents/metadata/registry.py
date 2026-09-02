from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, fields
from typing import Literal

from caselawclient.models.documents.metadata.base import Metadata
from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
from caselawclient.models.documents.metadata.types.court import CourtMetadata
from caselawclient.models.documents.metadata.types.date import DateMetadata
from caselawclient.models.documents.metadata.types.judges import JudgesMetadata
from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
from caselawclient.models.documents.metadata.types.name import NameMetadata

MetadataAttributeKey = Literal["title", "court", "jurisdiction", "date", "case_number", "categories", "judges"]


@dataclass(slots=True)
class DocumentMetadata:
    """Typed facades for document metadata, accessed as attributes.

    Example: ``document.metadata.date``, ``document.metadata.judges``.
    Not a mapping — iterate the instance to walk all facades.
    """

    title: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata
    judges: JudgesMetadata

    def __iter__(self) -> Iterator[Metadata]:
        for field in fields(self):
            yield getattr(self, field.name)

    def __len__(self) -> int:
        return len(fields(self))

    def __contains__(self, item: object) -> bool:
        raise TypeError(
            "DocumentMetadata does not support membership tests; access facades as attributes "
            "(e.g. document.metadata.title)"
        )
