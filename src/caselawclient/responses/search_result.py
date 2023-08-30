import logging
import os
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from dateutil import parser as dateparser
from dateutil.parser import ParserError
from ds_caselaw_utils.courts import Court, CourtNotFoundException, courts
from lxml import etree

from caselawclient.Client import api_client
from caselawclient.models.documents import DocumentURIString
from caselawclient.xml_helpers import get_xpath_match_string


class EditorStatus(Enum):
    """
    Enum representing the editor status.
    """

    NEW = "new"
    IN_PROGRESS = "in progress"
    HOLD = "hold"


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

    @staticmethod
    def create_from_uri(uri: DocumentURIString) -> "SearchResultMetadata":
        """
        Create a SearchResultMetadata instance from a search result URI.

        :param uri: The URI of the search result

        :return: The created SearchResultMetadata instance
        """
        response_text = api_client.get_properties_for_search_results([uri])
        last_modified = api_client.get_last_modified(uri)
        root = etree.fromstring(response_text)
        return SearchResultMetadata(root, last_modified)

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
    def editor_priority(self) -> str:
        """
        :return: The editor priority
        """

        return self._get_xpath_match_string(
            "//editor-priority/text()", EditorPriority.MEDIUM.value
        )

    @property
    def submission_datetime(self) -> datetime:
        """
        :return: The submission datetime
        """

        extracted_submission_datetime = self._get_xpath_match_string(
            "//transfer-received-at/text()"
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

    def __init__(self, node: etree._Element):
        """
        :param node: The XML element representing the search result
        """

        self.node = node

    @property
    def uri(self) -> DocumentURIString:
        """
        :return: The URI of the search result
        """

        return DocumentURIString(
            self._get_xpath_match_string("@uri").lstrip("/").split(".xml")[0]
        )

    @property
    def neutral_citation(self) -> str:
        """
        :return: The neutral citation of the search result
        """

        return self._get_xpath_match_string("search:extracted/uk:cite/text()")

    @property
    def name(self) -> str:
        """
        :return: The neutral citation of the search result
        """

        return self._get_xpath_match_string("search:extracted/akn:FRBRname/@value")

    @property
    def court(
        self,
    ) -> Optional[Court]:
        """
        :return: The court of the search result
        """

        court_code = self._get_xpath_match_string("search:extracted/uk:court/text()")
        try:
            court = courts.get_by_code(court_code)
        except CourtNotFoundException:
            court = None

        return court

    @property
    def date(self) -> Optional[datetime]:
        """
        :return: The date of the search result
        """

        date_string = self._get_xpath_match_string(
            "search:extracted/akn:FRBRdate[(@name='judgment' or @name='decision')]/@date"
        )
        try:
            date = dateparser.parse(date_string)
        except ParserError as e:
            logging.warning(
                f'Unable to parse document date "{date_string}". Full error: {e}'
            )
            date = None
        return date

    @property
    def transformation_date(self) -> str:
        """
        :return: The transformation date of the search result
        """

        return self._get_xpath_match_string(
            "search:extracted/akn:FRBRdate[@name='transform']/@date"
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

    @property
    def metadata(self) -> SearchResultMetadata:
        """
        :return: The metadata of the search result
        """

        return SearchResultMetadata.create_from_uri(
            self.uri,
        )

    def _get_xpath_match_string(self, path: str) -> str:
        return get_xpath_match_string(self.node, path, namespaces=self.NAMESPACES)
