from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.base import SingleMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

NAME_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"


def read_name(body: "DocumentBody") -> str:
    return body.get_xpath_match_string(NAME_XPATH)


class NameMetadata(SingleMetadata[str]):
    key = "name"
    title = "Name"
    description = "The name of the document."

    @cached_property
    def value(self) -> str:
        return read_name(self.document.body)
