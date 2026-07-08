import datetime
import warnings
from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.body import UnparsableDate
from caselawclient.models.documents.metadata.base import SingleMetadata

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

DATE_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date"


def read_date_as_string(body: "DocumentBody") -> str:
    return body.get_xpath_match_string(DATE_XPATH)


def read_date_as_date(body: "DocumentBody") -> datetime.date | None:
    date_as_string = read_date_as_string(body)
    if not date_as_string:
        return None
    try:
        return datetime.datetime.strptime(
            date_as_string,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        warnings.warn(
            f"Unparsable date encountered: {date_as_string}",
            UnparsableDate,
        )
        return None


class DateMetadata(SingleMetadata[datetime.date | None]):
    key = "date"
    title = "Date"
    description = "The date of the document."

    @cached_property
    def value(self) -> datetime.date | None:
        return read_date_as_date(self.document.body)

    @cached_property
    def as_string(self) -> str:
        return read_date_as_string(self.document.body)
