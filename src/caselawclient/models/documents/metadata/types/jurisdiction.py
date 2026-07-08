from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.base import SingleMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

JURISDICTION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:jurisdiction/text()"


def read_jurisdiction(body: "DocumentBody") -> str:
    return body.get_xpath_match_string(JURISDICTION_XPATH)


class JurisdictionMetadata(SingleMetadata[str]):
    key = "jurisdiction"
    title = "Jurisdiction"
    description = "The jurisdiction of the document."

    @cached_property
    def value(self) -> str:
        return read_jurisdiction(self.document.body)
