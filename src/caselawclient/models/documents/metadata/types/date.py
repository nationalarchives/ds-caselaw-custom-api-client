import datetime

from caselawclient.models.documents.metadata.base import SingleMetadata


def date_as_string_from_value(value: datetime.date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


class DateMetadata(SingleMetadata[datetime.date | None]):
    key = "date"
    title = "Date"
    description = "The date of the document."

    @property
    def value(self) -> datetime.date | None:
        return self.document.body.document_date_as_date

    @property
    def as_string(self) -> str:
        return date_as_string_from_value(self.value)

    def __str__(self) -> str:
        return self.as_string
