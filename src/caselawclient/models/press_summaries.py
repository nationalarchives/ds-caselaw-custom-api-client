from __future__ import annotations

import importlib
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

from ds_caselaw_utils.types import NeutralCitationString

from caselawclient.errors import DocumentNotFoundError
from caselawclient.models.neutral_citation_mixin import NeutralCitationMixin

from .documents import Document

if TYPE_CHECKING:
    from caselawclient.models.judgments import Judgment


class PressSummary(NeutralCitationMixin, Document):
    """
    Represents a press summary document.
    """

    document_noun = "press summary"
    document_noun_plural = "press summaries"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(self.document_noun, *args, **kwargs)

    @cached_property
    def neutral_citation(self) -> NeutralCitationString:
        return NeutralCitationString(
            self.body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:preface/akn:p/akn:neutralCitation/text()",
                {
                    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
                },
            )
        )

    @property
    def best_human_identifier(self) -> str:
        return self.neutral_citation

    @cached_property
    def linked_document(self) -> Optional[Judgment]:
        """
        Attempt to fetch a linked judgement, and return it, if it exists
        """
        try:
            uri = self.uri.removesuffix("/press-summary/1")
            Judgment = importlib.import_module("caselawclient.models.judgments").Judgment
            return Judgment(uri, self.api_client)  # type: ignore
        except DocumentNotFoundError:
            return None
