from functools import cached_property
from typing import Any

from ds_caselaw_utils import neutral_url

from caselawclient.xml_helpers import get_xpath_match_string

from .documents import Document


class PressSummary(Document):
    document_noun = "press summary"
    document_noun_plural = "press summaries"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.attributes_to_validate = self.attributes_to_validate + [
            (
                "has_ncn",
                True,
                "This {document_noun} has no neutral citation number",
            ),
            (
                "has_valid_ncn",
                True,
                "The neutral citation number of this {document_noun} is not valid",
            ),
        ]

        super(PressSummary, self).__init__(*args, **kwargs)

    @cached_property
    def neutral_citation(self) -> str:
        return get_xpath_match_string(
            self.content_as_xml_tree,
            "/akn:akomaNtoso/akn:doc/akn:mainBody/akn:p/akn:neutralCitation/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @cached_property
    def has_ncn(self) -> bool:
        if not self.neutral_citation:
            return False

        return True

    @cached_property
    def has_valid_ncn(self) -> bool:
        if not self.has_ncn or not neutral_url(self.neutral_citation):
            return False

        return True
