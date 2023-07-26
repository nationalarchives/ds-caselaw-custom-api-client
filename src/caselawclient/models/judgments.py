from functools import cached_property
from typing import Any

from ds_caselaw_utils import neutral_url

from ..xml_helpers import get_xpath_match_string
from .documents import Document


class Judgment(Document):
    document_noun = "judgment"
    document_noun_plural = "judgments"

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

        super(Judgment, self).__init__(*args, **kwargs)

    @cached_property
    def neutral_citation(self) -> str:
        return get_xpath_match_string(
            self.content_as_xml_tree,
            "/root/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:cite/text()",
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
        # The checks that we can convert an NCN to a URI using the function from utils
        if not self.has_ncn or not neutral_url(self.neutral_citation):
            return False

        return True
