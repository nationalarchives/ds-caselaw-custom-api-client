from functools import cached_property
from typing import Any

from caselawclient.models.neutral_citation_mixin import NeutralCitationMixin
from caselawclient.xml_helpers import get_xpath_match_string

from .documents import Document


class PressSummary(NeutralCitationMixin, Document):
    """
    Represents a press summary document.
    """

    document_noun = "press summary"
    document_noun_plural = "press summaries"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super(PressSummary, self).__init__(self.document_noun, *args, **kwargs)

    @cached_property
    def neutral_citation(self) -> str:
        return get_xpath_match_string(
            self.content_as_xml_tree,
            "/akn:akomaNtoso/akn:doc/akn:preface/akn:p/akn:neutralCitation/text()",
            {
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @property
    def best_human_identifier(self) -> str:
        return self.neutral_citation
