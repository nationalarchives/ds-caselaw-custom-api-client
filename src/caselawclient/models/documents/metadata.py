from dataclasses import dataclass
from typing import Any, Optional

from caselawclient.models.identifiers.collection import IdentifiersCollection


@dataclass(frozen=True)
class DocumentMetadata:
    name: Optional[str] = None
    ncn: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    categories: Optional[list[Any]] = None
    case_number: Optional[str] = None
    date: Optional[str] = None
    parties: Optional[list[str]] = None
    judges: Optional[list[str]] = None
    uri: Optional[str] = None
    source_name: Optional[str] = None
    source_email: Optional[str] = None
    consignment_reference: Optional[str] = None
    identifiers: Optional[IdentifiersCollection] = None
    version_annotation: Optional[str] = None

    def as_dict(self, exclude_empty: bool = False) -> dict[str, Any]:
        data = {
            "name": self.name,
            "ncn": self.ncn,
            "court": self.court,
            "jurisdiction": self.jurisdiction,
            "categories": self.categories,
            "case_number": self.case_number,
            "date": self.date,
            "parties": self.parties,
            "judges": self.judges,
            "uri": self.uri,
            "source_name": self.source_name,
            "source_email": self.source_email,
            "consignment_reference": self.consignment_reference,
            "identifiers": self.identifiers,
            "version_annotation": self.version_annotation,
        }

        if exclude_empty:
            return {key: value for key, value in data.items() if value not in (None, "", [], {}, ())}

        return data
