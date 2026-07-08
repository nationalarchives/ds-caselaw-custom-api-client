import datetime

from caselawclient.models.documents.metadata.base import SingleMetadata


class DateMetadata(SingleMetadata[datetime.date | None]):
    key = "date"
    title = "Date"
    description = "The date of the document."

    @property
    def as_string(self) -> str:
        return self.document.body.document_date_as_string

    @property
    def value(self) -> datetime.date | None:
        return self.document.body.document_date_as_date
