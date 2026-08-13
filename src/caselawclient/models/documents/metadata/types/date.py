import datetime
from typing import cast

from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.exceptions import (
    InvalidMetadataFieldXMLRepresentationException,
)
from caselawclient.models.documents.metadata.fields.field import MetadataDateValue, MetadataFieldValue
from caselawclient.models.documents.metadata.fields.unpack_helpers import stripped_element_text
from caselawclient.xml_helpers import Element


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
        return self._date_value(self.document.body.document_date_as_date)

    @property
    def as_string(self) -> str:
        return date_as_string_from_value(self.value)

    def materialise_body_claims(self) -> None:
        document_date = self.document.body.document_date_as_date
        if document_date is None:
            return
        self._materialise_document_values([MetadataDateValue(document_date)])

    @classmethod
    def validate_value(cls, value: MetadataFieldValue) -> None:
        if not isinstance(value, MetadataDateValue):
            raise TypeError(f"Expected MetadataDateValue for '{cls.key}', got {type(value).__name__}")

    @classmethod
    def pack_value(cls, value: MetadataFieldValue, into: Element) -> None:
        cls.validate_value(value)
        into.text = cast(MetadataDateValue, value).value.isoformat()

    @classmethod
    def unpack_value(cls, metadata_xml: Element, pack_version: int) -> MetadataFieldValue:
        text = stripped_element_text(metadata_xml)
        if not text:
            raise InvalidMetadataFieldXMLRepresentationException(
                "Metadata field XML representation is not valid: date value not present or empty"
            )
        try:
            return MetadataDateValue(datetime.date.fromisoformat(text))
        except ValueError as exc:
            raise InvalidMetadataFieldXMLRepresentationException(
                f"Metadata field XML representation is not valid: unparsable date '{text}'"
            ) from exc

    def __str__(self) -> str:
        return self.as_string
