from functools import cached_property
from typing import Any

from caselawclient.models.neutral_citation_mixin import NeutralCitationMixin

from ..xml_helpers import get_xpath_match_string
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
        return get_xpath_match_string(
            self.xml.xml_as_tree,
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:cite/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @property
    def best_human_identifier(self) -> str:
        return self.neutral_citation
