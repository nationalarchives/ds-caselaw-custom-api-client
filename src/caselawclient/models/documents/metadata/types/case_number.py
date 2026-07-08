from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.base import SingleMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

CASE_NUMBER_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:caseNumber/text()"


def read_case_number(body: "DocumentBody") -> str | None:
    return body.get_xpath_match_string(CASE_NUMBER_XPATH)


class CaseNumberMetadata(SingleMetadata[str | None]):
    key = "case_number"
    title = "Case Number"
    description = "The case number of the document."

    @cached_property
    def value(self) -> str | None:
        return read_case_number(self.document.body)
