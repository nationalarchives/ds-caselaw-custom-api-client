from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Literal, TypedDict, overload

from caselawclient.models.documents.metadata.types.case_number import CaseNumberMetadata
from caselawclient.models.documents.metadata.types.categories import CategoriesMetadata
from caselawclient.models.documents.metadata.types.court import CourtMetadata
from caselawclient.models.documents.metadata.types.date import DateMetadata
from caselawclient.models.documents.metadata.types.judges import JudgesMetadata
from caselawclient.models.documents.metadata.types.jurisdiction import JurisdictionMetadata
from caselawclient.models.documents.metadata.types.name import NameMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.metadata.base import Metadata

MetadataAttributeKey = Literal["title", "court", "jurisdiction", "date", "case_number", "categories", "judges"]

METADATA_KEY_ALIASES: dict[str, MetadataAttributeKey] = {
    "name": "title",
    "judge": "judges",
}


class DocumentMetadataRegistry(TypedDict):
    title: NameMetadata
    court: CourtMetadata
    jurisdiction: JurisdictionMetadata
    date: DateMetadata
    case_number: CaseNumberMetadata
    categories: CategoriesMetadata
    judges: JudgesMetadata


class DocumentMetadata(dict[str, "Metadata"]):
    """Document metadata keyed by schema-aligned claim names.

    Legacy facade keys ``name`` and ``judge`` are proxied to ``title`` and
    ``judges`` respectively.
    """

    def _canonical_key(self, key: str) -> str:
        if key in METADATA_KEY_ALIASES:
            canonical = METADATA_KEY_ALIASES[key]
            warnings.warn(
                f'metadata["{key}"] is deprecated; use metadata["{canonical}"]',
                DeprecationWarning,
                stacklevel=3,
            )
            return canonical
        return key

    @overload
    def __getitem__(self, key: Literal["title", "name"]) -> NameMetadata: ...

    @overload
    def __getitem__(self, key: Literal["court"]) -> CourtMetadata: ...

    @overload
    def __getitem__(self, key: Literal["jurisdiction"]) -> JurisdictionMetadata: ...

    @overload
    def __getitem__(self, key: Literal["date"]) -> DateMetadata: ...

    @overload
    def __getitem__(self, key: Literal["case_number"]) -> CaseNumberMetadata: ...

    @overload
    def __getitem__(self, key: Literal["categories"]) -> CategoriesMetadata: ...

    @overload
    def __getitem__(self, key: Literal["judges", "judge"]) -> JudgesMetadata: ...

    @overload
    def __getitem__(self, key: str) -> Metadata: ...

    def __getitem__(self, key: str) -> Metadata:
        return super().__getitem__(self._canonical_key(key))

    def get(self, key: str, default: Metadata | None = None) -> Metadata | None:  # type: ignore[override]
        try:
            return self[key]
        except KeyError:
            return default

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, str):
            return False
        return super().__contains__(METADATA_KEY_ALIASES.get(key, key))
