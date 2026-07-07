import datetime
from functools import cached_property

from caselawclient.models.documents.metadata.base import SingleMetadata


class DateMetadata(SingleMetadata[datetime.date | None]):
    key = "date"
    title = "Date"
    description = "The date of the document."

    @cached_property
    def value(self) -> datetime.date | None:
        return self.document.body.document_date_as_date
