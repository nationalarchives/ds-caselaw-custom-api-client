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


class EditorStatus(Enum):
    """
    Enum representing the editor status.
    """

    NEW = "new"
    IN_PROGRESS = "in progress"
    HOLD = "hold"


class SearchResultMetadata:
    """
    Represents the metadata of a search result.

    Properties:
        author (str): The author of the search result.
        author_email (str): The email of the author.
        consignment_reference (str): The consignment reference.
        assigned_to (str): The assigned editor.
        editor_hold (str): The editor hold status.
        editor_priority (str): The editor priority.
        last_modified (str): The last modified date.
        submission_datetime (datetime): The submission datetime.
        editor_status (EditorStatus): The editor status based on the metadata.
    """

    def __init__(self, node: etree._Element, last_modified: str):
        self.node = node
        self.last_modified = last_modified

    @staticmethod
    def create_from_uri(uri: str) -> "SearchResultMetadata":
        """
        Create a SearchResultMetadata instance from a search result URI.

        Args:
            uri (str): The URI of the search result.

        Returns:
            SearchResultMetadata: The created SearchResultMetadata instance.
        """
        response_text = api_client.get_properties_for_search_results([uri])
        last_modified = api_client.get_last_modified(uri)
        root = etree.fromstring(response_text)
        return SearchResultMetadata(root, last_modified)

    @property
    def submission_datetime(self) -> datetime:
        extracted_submission_datetime = self._get_xpath_match_string(
            "//transfer-received-at/text()"
        )
        return (
            datetime.strptime(extracted_submission_datetime, "%Y-%m-%dT%H:%M:%SZ")
            if extracted_submission_datetime
            else datetime.min
        )

    @property
    def author(self) -> str:
        return self._get_xpath_match_string("//source-name/text()")

    @property
    def author_email(self) -> str:
        return self._get_xpath_match_string("//source-email/text()")

    @property
    def consignment_reference(self) -> str:
        return self._get_xpath_match_string("//transfer-consignment-reference/text()")

    @property
    def assigned_to(self) -> str:
        return self._get_xpath_match_string("//assigned-to/text()")

    @property
    def editor_hold(self) -> str:
        return self._get_xpath_match_string("//editor-hold/text()")

    @property
    def editor_priority(self) -> str:
        return self._get_xpath_match_string(
            "//editor-priority/text()", "20"
        )  # medium priority default (20)

    @property
    def editor_status(
        self,
    ) -> EditorStatus:
        if self.editor_hold == "true":
            return EditorStatus.HOLD
        if self.assigned_to:
            return EditorStatus.IN_PROGRESS
        return EditorStatus.NEW

    def _get_xpath_match_string(self, path: str, fallback: str = "") -> str:
        return get_xpath_match_string(self.node, path, fallback=fallback)


class SearchResult:
    """
    Represents a search result obtained from XML data.

    Attributes:
        NAMESPACES (Dict[str, str]): Namespace mappings used in XPath expressions.

    Args:
        node (etree._Element): The XML element representing the search result.

    Properties:
        uri (str): The URI of the search result.
        neutral_citation (str): The neutral citation of the search result.
        name (str): The name of the search result.
        court (Optional[Court]): The court of the search result.
        date (Optional[datetime]): The date of the search result.
        transformation_date (str): The transformation date of the search result.
        content_hash (str): The content hash of the search result.
        matches (str): The search result matches.
        metadata (SearchResultMetadata): The metadata of the search result.
    """

    NAMESPACES: Dict[str, str] = {
        "search": "http://marklogic.com/appservices/search",
        "uk": "https://caselaw.nationalarchives.gov.uk/akn",
        "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    }

    def __init__(self, node: etree._Element):
        self.node = node

    @property
    def uri(self) -> str:
        return self._get_xpath_match_string("@uri").lstrip("/").split(".xml")[0]

    @property
    def neutral_citation(self) -> str:
        return self._get_xpath_match_string("search:extracted/uk:cite/text()")

    @property
    def name(self) -> str:
        return self._get_xpath_match_string("search:extracted/akn:FRBRname/@value")

    @property
    def court(
        self,
    ) -> Optional[Court]:
        court_code = self._get_xpath_match_string("search:extracted/uk:court/text()")
        try:
            court = courts.get_by_code(court_code)
        except CourtNotFoundException:
            court = None

        return court

    @property
    def date(self) -> Optional[datetime]:
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
        return self._get_xpath_match_string(
            "search:extracted/akn:FRBRdate[@name='transform']/@date"
        )

    @property
    def content_hash(self) -> str:
        return self._get_xpath_match_string("search:extracted/uk:hash/text()")

    @property
    def matches(self) -> str:
        file_path = os.path.join(os.path.dirname(__file__), "xsl/search_match.xsl")
        xslt_transform = etree.XSLT(etree.parse(file_path))
        return str(xslt_transform(self.node))

    @property
    def metadata(self) -> SearchResultMetadata:
        return SearchResultMetadata.create_from_uri(
            self.uri,
        )

    def _get_xpath_match_string(self, path: str) -> str:
        return get_xpath_match_string(self.node, path, namespaces=self.NAMESPACES)


def get_xpath_match_string(
    node: etree._Element,
    path: str,
    namespaces: Optional[Dict[str, str]] = None,
    fallback: str = "",
) -> str:
    kwargs = {"namespaces": namespaces} if namespaces else {}
    return str((node.xpath(path, **kwargs) or [fallback])[0])
