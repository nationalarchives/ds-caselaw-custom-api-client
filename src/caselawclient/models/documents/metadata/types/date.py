import datetime
import warnings

from caselawclient.models.documents.metadata.base import SingleMetadata


def date_as_string_from_value(value: datetime.date | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d")


def date_from_metadata_field_value(value: object) -> datetime.date | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        # Import locally to avoid a circular dependency with DocumentBody.
        from caselawclient.models.documents.body import UnparsableDate

        warnings.warn(
            f"Unparsable date encountered: {value}",
            UnparsableDate,
        )
        return None


class DateMetadata(SingleMetadata[datetime.date | None]):
    key = "date"
    title = "Date"
    description = "The date of the document."

    @property
    def value(self) -> datetime.date | None:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.document_date_as_date
        return date_from_metadata_field_value(resolved.value)

    @property
    def as_string(self) -> str:
        return date_as_string_from_value(self.value)

    def __str__(self) -> str:
        return self.as_string
