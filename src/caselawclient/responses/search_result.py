import logging
import os
from datetime import datetime
from enum import Enum
from functools import cached_property
from typing import Any, Dict, Optional

from dateutil import parser as dateparser
from dateutil.parser import ParserError
from ds_caselaw_utils.courts import Court, CourtNotFoundException, courts
from ds_caselaw_utils.types import CourtCode, JurisdictionCode
from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.identifiers import Identifiers
from caselawclient.models.identifiers.unpacker import unpack_all_identifiers_from_etree
from caselawclient.types import DocumentURIString
from caselawclient.xml_helpers import get_xpath_match_string


class EditorStatus(Enum):
    """
    Enum representing the editor status.
    """

    NEW = "new"
    IN_PROGRESS = "in progress"
    HOLD = "hold"
    PUBLISHED = "published"


class EditorPriority(Enum):
    """
    Enum representing the editor priority.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SearchResultMetadata:
    """
    Represents the metadata of a search result.
    """

    def __init__(self, node: etree._Element, last_modified: str):
        self.node = node
        self.last_modified = last_modified

    @property
    def author(self) -> str:
        """
        :return: The author of the search result
        """

        return self._get_xpath_match_string("//source-name/text()")

    @property
    def author_email(self) -> str:
        """
        :return: The email address of the author
        """

        return self._get_xpath_match_string("//source-email/text()")

    @property
    def consignment_reference(self) -> str:
        """
        :return: The consignment reference of this document submission
        """

        return self._get_xpath_match_string("//transfer-consignment-reference/text()")

    @property
    def assigned_to(self) -> str:
        """
        :return: The username of the editor assigned to this document
        """

        return self._get_xpath_match_string("//assigned-to/text()")

    @property
    def editor_hold(self) -> str:
        """
        :return: The editor hold status
        """

        return self._get_xpath_match_string("//editor-hold/text()")

    @property
    def is_published(self) -> bool:
        """
        :return:
        """
        return self._get_xpath_match_string("//published/text()") == "true"

    @property
    def editor_priority(self) -> str:
        """
        :return: The editor priority
        """

        return self._get_xpath_match_string(
            "//editor-priority/text()",
            EditorPriority.MEDIUM.value,
        )

    @property
    def submission_datetime(self) -> datetime:
        """
        :return: The submission datetime
        """

        extracted_submission_datetime = self._get_xpath_match_string(
            "//transfer-received-at/text()",
        )
        return (
            datetime.strptime(extracted_submission_datetime, "%Y-%m-%dT%H:%M:%SZ")
            if extracted_submission_datetime
            else datetime.min
        )

    @property
    def editor_status(
        self,
    ) -> str:
        """
        :return: The editor status based on the metadata
        """

        if self.is_published:
            return EditorStatus.PUBLISHED.value
        if self.editor_hold == "true":
            return EditorStatus.HOLD.value
        if self.assigned_to:
            return EditorStatus.IN_PROGRESS.value
        return EditorStatus.NEW.value

    def _get_xpath_match_string(self, path: str, fallback: str = "") -> str:
        return get_xpath_match_string(self.node, path, fallback=fallback)


class SearchResult:
    """
    Represents a search result obtained from XML data.
    """

    NAMESPACES: Dict[str, str] = {
        "search": "http://marklogic.com/appservices/search",
        "uk": "https://caselaw.nationalarchives.gov.uk/akn",
        "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    }
    """ Namespace mappings used in XPath expressions. """

    def __init__(self, node: etree._Element, client: MarklogicApiClient):
        """
        :param node: The XML element representing the search result
        """

        self.node = node
        self.client = client

    def __repr__(self) -> str:
        try:
            slug = self.slug
        except RuntimeError:
            slug = "**NO SLUG**"
        name = self.name or "**NO NAME**"
        return f"<SearchResult {self.uri} {slug} {name} {self.date}>"

    @property
    def uri(self) -> DocumentURIString:
        """
        :return: The URI of the search result
        """

        return DocumentURIString(
            self._get_xpath_match_string("@uri").lstrip("/").split(".xml")[0],
        )

    @property
    def identifiers(self) -> Identifiers:
        identifiers_etrees = self._get_xpath(".//identifiers")
        count = len(identifiers_etrees)
        if count != 1:
            logging.warning(f"{count} //identifiers nodes found in search result, expected 1.")
        identifiers_etree = None if not identifiers_etrees else identifiers_etrees[0]
        return unpack_all_identifiers_from_etree(identifiers_etree)

    @cached_property
    def slug(self) -> str:
        preferred = self.identifiers.preferred()
        if not preferred:
            raise RuntimeError("No preferred identifier for search result")
        return str(preferred.url_slug)

    @property
    def neutral_citation(self) -> str:
        """
        :return: The neutral citation of the search result, or the judgment it is a press summary of.
        """

        return self._get_xpath_match_string(
            "search:extracted/uk:cite/text()",
        ) or self._get_xpath_match_string("search:extracted/akn:neutralCitation/text()")

    @property
    def name(self) -> str:
        """
        :return: The title of the search result's document
        """

        return self._get_xpath_match_string("search:extracted/akn:FRBRname/@value")

    @property
    def court(
        self,
    ) -> Optional[Court]:
        """
        :return: The court of the search result
        """
        court: Optional[Court] = None
        court_code = self._get_xpath_match_string("search:extracted/uk:court/text()")
        jurisdiction_code = self._get_xpath_match_string(
            "search:extracted/uk:jurisdiction/text()",
        )
        if jurisdiction_code:
            try:
                court = courts.get_court_with_jurisdiction_by_code(
                    CourtCode(court_code), JurisdictionCode(jurisdiction_code)
                )
            except CourtNotFoundException:
                logging.warning(
                    "Court not found with court code %s and jurisdiction code %s for judgment with NCN %s, falling back to court."
                    % (court_code, jurisdiction_code, self.neutral_citation),
                )
        if court is None:
            try:
                court = courts.get_by_code(CourtCode(court_code))
            except CourtNotFoundException:
                logging.warning(
                    "Court not found with court code %s for judgment with NCN %s, returning None."
                    % (court_code, self.neutral_citation),
                )
                court = None
        return court

    @property
    def date(self) -> Optional[datetime]:
        """
        :return: The date of the search result
        """

        date_string = self._get_xpath_match_string(
            "search:extracted/akn:FRBRdate[(@name='judgment' or @name='decision')]/@date",
        )
        try:
            date = dateparser.parse(date_string)
        except ParserError as e:
            logging.warning(
                f'Unable to parse document date "{date_string}". Full error: {e}',
            )
            date = None
        return date

    @property
    def transformation_date(self) -> str:
        """
        :return: The transformation date of the search result
        """

        return self._get_xpath_match_string(
            "search:extracted/akn:FRBRdate[@name='transform']/@date",
        )

    @property
    def content_hash(self) -> str:
        """
        :return: The content hash of the search result
        """

        return self._get_xpath_match_string("search:extracted/uk:hash/text()")

    @property
    def matches(self) -> str:
        """
        :return: The search result matches
        """

        file_path = os.path.join(os.path.dirname(__file__), "xsl/search_match.xsl")
        xslt_transform = etree.XSLT(etree.parse(file_path))
        return str(xslt_transform(self.node))

    @cached_property
    def metadata(self) -> SearchResultMetadata:
        """
        :return: A `SearchResultMetadata` instance representing the metadata of this result
        """
        response_text = self.client.get_properties_for_search_results([self.uri])
        last_modified = self.client.get_last_modified(self.uri)
        root = etree.fromstring(response_text)
        return SearchResultMetadata(root, last_modified)

    def _get_xpath_match_string(self, path: str) -> str:
        return get_xpath_match_string(self.node, path, namespaces=self.NAMESPACES)

    def _get_xpath(self, path: str) -> Any:
        return self.node.xpath(path, namespaces=self.NAMESPACES)
