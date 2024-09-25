import importlib
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

from caselawclient.errors import DocumentNotFoundError
from caselawclient.models.neutral_citation_mixin import NeutralCitationMixin

if TYPE_CHECKING:
    from caselawclient.models.press_summaries import PressSummary

from .documents import Document


class Judgment(NeutralCitationMixin, Document):
    """
    Represents a judgment document.
    """

    document_noun = "judgment"
    document_noun_plural = "judgments"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(Judgment, self).__init__(self.document_noun, *args, **kwargs)

    @cached_property
    def neutral_citation(self) -> str:
        return self.body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:cite/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @property
    def best_human_identifier(self) -> str:
        return self.neutral_citation

    @cached_property
    def linked_document(self) -> Optional["PressSummary"]:
        """
        Attempt to fetch a linked press summary, and return it, if it exists
        """
        try:
            uri = self.uri + "/press-summary/1"
            PressSummary = importlib.import_module("caselawclient.models.press_summaries").PressSummary
            return PressSummary(uri, self.api_client)  # type: ignore
        except DocumentNotFoundError:
            return None
