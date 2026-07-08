from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.base import SingleMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

COURT_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court/text()"


def read_court(body: "DocumentBody") -> str:
    return body.get_xpath_match_string(COURT_XPATH)


class CourtMetadata(SingleMetadata[str]):
    key = "court"
    title = "Court"
    description = "The court that issued the document."

    @cached_property
    def value(self) -> str:
        return read_court(self.document.body)
