import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

RESULTS_PER_PAGE = 10
QUOTED_PHRASE_REGEX = '"([^"]*)"'


@dataclass
class SearchParameters:
    """Represents search parameters for a case law search."""

    query: Optional[str] = None
    court: Optional[str] = None
    judge: Optional[str] = None
    party: Optional[str] = None
    neutral_citation: Optional[str] = None
    specific_keyword: Optional[str] = None
    order: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = 1
    page_size: int = RESULTS_PER_PAGE
    show_unpublished: bool = False
    only_unpublished: bool = False
    collections: Optional[List[str]] = None

    def as_marklogic_payload(self) -> Dict[str, Any]:
        """
        Converts the search parameters to a dictionary payload suitable
        fo MarkLogic.
        """
        return {
            "court": self._marklogic_courts,
            "judge": str(self.judge or ""),
            "page": max(1, int(self.page)),
            "page-size": int(self.page_size),
            "q": str(self.query or ""),
            "party": str(self.party or ""),
            "neutral_citation": str(self.neutral_citation or ""),
            "specific_keyword": str(self.specific_keyword or ""),
            "order": str(self.order or ""),
            "from": str(self.date_from or ""),
            "to": str(self.date_to or ""),
            "show_unpublished": str(self.show_unpublished).lower(),
            "only_unpublished": str(self.only_unpublished).lower(),
            "collections": self._marklogic_collections,
            "quoted_phrases": self._quoted_phrases,
        }

    @property
    def _marklogic_collections(self) -> str:
        return ",".join(self.collections or []).replace(" ", "").replace(",,", ",")

    @property
    def _marklogic_courts(self) -> Optional[List[str]]:
        court_text = self._join_court_text(self.court or "")
        if not (court_text).strip():
            return None
        courts = self._court_list_splitter(court_text)
        alternative_court_names = self._get_alternative_court_names(courts)
        return list(courts | alternative_court_names)

    @property
    def _quoted_phrases(self) -> List[str]:
        if self.query is None:
            return []
        return re.findall(QUOTED_PHRASE_REGEX, self.query)

    @staticmethod
    def _join_court_text(court_text: str) -> str:
        return ",".join(court_text) if isinstance(court_text, list) else court_text

    @staticmethod
    def _court_list_splitter(court_text: str) -> Set[str]:
        return set(court_text.lower().replace(" ", "").split(","))

    @staticmethod
    def _get_alternative_court_names(courts: Set[str]) -> Set[str]:
        ALTERNATIVE_COURT_NAMES_MAP = {
            "ewhc/qb": "ewhc/kb",
            "ewhc/kb": "ewhc/qb",
            "ewhc/scco": "ewhc/costs",
            "ewhc/costs": "ewhc/scco",
            "ukait": "ukut/iac",
            "ukut/iac": "ukait",
        }
        alternative_court_names = set()
        for primary_name, secondary_name in ALTERNATIVE_COURT_NAMES_MAP.items():
            if primary_name in courts and secondary_name not in courts:
                alternative_court_names.add(secondary_name)
        return alternative_court_names
