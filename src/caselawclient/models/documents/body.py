import datetime
import warnings
from functools import cached_property
from typing import NewType, Optional

import pytz

from caselawclient.models.utilities.dates import parse_string_date_as_utc

from .xml import XML

CourtIdentifierString = NewType("CourtIdentifierString", str)


class UnparsableDate(Warning):
    pass


class DocumentBody:
    """
    A class for abstracting out interactions with the body of a document.
    """

    def __init__(self, xml_bytestring: bytes):
        self._xml = XML(xml_bytestring=xml_bytestring)
        """ This is an instance of the `Document.XML` class for manipulation of the XML document itself. """

    def get_xpath_match_string(self, xpath: str, namespaces: dict[str, str]) -> str:
        return self._xml.get_xpath_match_string(xpath, namespaces)

    @cached_property
    def name(self) -> str:
        return self._xml.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )

    @cached_property
    def court(self) -> str:
        return self._xml.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @cached_property
    def jurisdiction(self) -> str:
        return self._xml.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:jurisdiction/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @property
    def court_and_jurisdiction_identifier_string(self) -> CourtIdentifierString:
        if self.jurisdiction != "":
            return CourtIdentifierString("/".join((self.court, self.jurisdiction)))
        return CourtIdentifierString(self.court)

    @cached_property
    def document_date_as_string(self) -> str:
        return self._xml.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )

    @cached_property
    def document_date_as_date(self) -> Optional[datetime.date]:
        if not self.document_date_as_string:
            return None
        try:
            return datetime.datetime.strptime(
                self.document_date_as_string,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            warnings.warn(
                f"Unparsable date encountered: {self.document_date_as_string}",
                UnparsableDate,
            )
            return None

    def get_manifestation_datetimes(
        self,
        name: Optional[str] = None,
    ) -> list[datetime.datetime]:
        name_filter = f"[@name='{name}']" if name else ""
        iso_datetimes = self._xml.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRManifestation"
            f"/akn:FRBRdate{name_filter}/@date",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )

        return [parse_string_date_as_utc(event, pytz.UTC) for event in iso_datetimes]

    def get_latest_manifestation_datetime(
        self,
        name: Optional[str] = None,
    ) -> Optional[datetime.datetime]:
        events = self.get_manifestation_datetimes(name)
        if not events:
            return None
        return max(events)

    def get_latest_manifestation_type(self) -> Optional[str]:
        return max(
            (
                (type, time)
                for type in ["transform", "tna-enriched"]
                if (time := self.get_latest_manifestation_datetime(type))
            ),
            key=lambda x: x[1],
        )[0]

    @cached_property
    def transformation_datetime(self) -> Optional[datetime.datetime]:
        """When was this document successfully parsed or reparsed (date from XML)"""
        return self.get_latest_manifestation_datetime("transform")

    @cached_property
    def enrichment_datetime(self) -> Optional[datetime.datetime]:
        """When was this document successfully enriched (date from XML)"""
        return self.get_latest_manifestation_datetime("tna-enriched")

    @cached_property
    def content_as_xml(self) -> str:
        return self._xml.xml_as_string

    @cached_property
    def failed_to_parse(self) -> bool:
        """
        Did this document entirely fail to parse?

        :return: `True` if there was a complete parser failure, otherwise `False`
        """
        return "error" in self._xml.root_element
