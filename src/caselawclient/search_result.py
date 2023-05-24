import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from dateutil import parser as dateparser
from dateutil.parser import ParserError
from ds_caselaw_utils.courts import CourtNotFoundException, courts
from lxml import etree

from caselawclient.Client import api_client
from caselawclient.models.search_results import SearchMatches


@dataclass
class SearchResult:
    """
    Represents a search result obtained from XML data.

    Attributes:
        uri (str): The URI of the search result.
        neutral_citation (str): The neutral citation of the search result.
        name (str): The name of the search result.
        court (str): The court of the search result.
        date (datetime): The date of the search result.
        matches (str): The search result matches.
        content_hash (str): The content hash of the search result.
        transformation_date (str): The transformation date of the search result.
        meta (Optional[SearchResultMeta]): The metadata of the search result.
    """

    uri: str = ""
    neutral_citation: str = ""
    name: str = ""
    court: str = ""
    date: Optional[datetime] = None
    matches: str = ""
    content_hash: str = ""
    transformation_date: str = ""
    meta: Optional["SearchResultMeta"] = None

    @staticmethod
    def create_from_node(
        node: etree._Element, meta: Optional["SearchResultMeta"]
    ) -> Optional["SearchResult"]:
        """
        Create a SearchResult instance from an XML node.

        Args:
            node (etree._Element): The XML node representing the search result.
            meta (Optional[SearchResultMeta]): The metadata of the search result.

        Returns:
            Optional[SearchResult]: The created SearchResult instance or None if creation failed.
        """
        uri = node.xpath("@uri")[0].lstrip("/").split(".xml")[0]
        matches = SearchMatches(etree.tostring(node, encoding="UTF-8").decode("UTF-8"))
        matches_html = matches.transform_to_html()
        namespaces = {
            "search": "http://marklogic.com/appservices/search",
            "uk": "https://caselaw.nationalarchives.gov.uk/akn",
            "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
        }
        neutral_citation = (
            node.xpath("search:extracted/uk:cite/text()", namespaces=namespaces) or [""]
        )[0]
        court_code = (
            node.xpath("search:extracted/uk:court/text()", namespaces=namespaces)
            or [""]
        )[0]
        metadata_name = (
            node.xpath("search:extracted/akn:FRBRname/@value", namespaces=namespaces)
            or [""]
        )[0]
        date_string = (
            node.xpath(
                "search:extracted/akn:FRBRdate[(@name='judgment' or @name='decision')]/@date",
                namespaces=namespaces,
            )
            or [""]
        )[0]
        transformation_date = (
            node.xpath(
                "search:extracted/akn:FRBRdate[@name='transform']/@date",
                namespaces=namespaces,
            )
            or [""]
        )[0]
        content_hash = (
            node.xpath("search:extracted/uk:hash/text()", namespaces=namespaces) or [""]
        )[0]

        try:
            date = dateparser.parse(date_string)
        except ParserError as e:
            logging.warning(
                f'Unable to parse document date "{date_string}". Full error: {e}'
            )
            date = None

        try:
            court = courts.get_by_code(court_code)
        except CourtNotFoundException:
            court = None

        return SearchResult(
            uri=uri,
            neutral_citation=neutral_citation,
            name=metadata_name,
            matches=matches_html,
            court=court,
            date=date,
            content_hash=content_hash,
            transformation_date=transformation_date,
            meta=meta,
        )


class EditorStatus(Enum):
    """
    Enum representing the editor status.
    """

    NEW = "new"
    IN_PROGRESS = "in progress"
    HOLD = "hold"


@dataclass
class SearchResultMeta:
    """
    Represents the metadata of a search result.

    Attributes:
        author (str): The author of the search result.
        author_email (str): The email of the author.
        consignment_reference (str): The consignment reference.
        submission_datetime (Optional[datetime]): The submission datetime.
        assigned_to (str): The assigned editor.
        editor_hold (str): The editor hold status.
        editor_priority (str): The editor priority.
        last_modified (str): The last modified date.

    Properties:
        editor_status (EditorStatus): The editor status based on the metadata.
    """

    author: str = ""
    author_email: str = ""
    consignment_reference: str = ""
    submission_datetime: Optional[datetime] = None
    assigned_to: str = ""
    editor_hold: str = "false"
    editor_priority: str = ""
    last_modified: str = ""

    @property
    def editor_status(
        self,
    ) -> EditorStatus:
        """
        Get the editor status based on the metadata.

        Returns:
            EditorStatus: The editor status.
        """
        if self.editor_hold == "true":
            return EditorStatus.HOLD
        if self.assigned_to:
            return EditorStatus.IN_PROGRESS
        return EditorStatus.NEW

    @staticmethod
    def create_from_uri(uri: str) -> "SearchResultMeta":
        """
        Create a SearchResultMeta instance from a URI.

        Args:
            uri (str): The URI of the search result.

        Returns:
            SearchResultMeta: The created SearchResultMeta instance.
        """
        response_text = api_client.get_properties_for_search_results([uri])
        last_modified = api_client.get_last_modified(uri)
        root = etree.fromstring(response_text)
        return SearchResultMeta.create_from_node(root, last_modified)

    @staticmethod
    def create_from_node(
        node: etree._Element, last_modified: str
    ) -> "SearchResultMeta":
        """
        Create a SearchResultMeta instance from an XML node.

        Args:
            node (etree._Element): The XML node representing the search result.
            last_modified (str): The last modified date.

        Returns:
            SearchResultMeta: The created SearchResultMeta instance.
        """
        extracted_submission_datetime = (
            node.xpath("//transfer-received-at/text()") or [""]
        )[0]
        submission_datetime = (
            datetime.strptime(extracted_submission_datetime, "%Y-%m-%dT%H:%M:%SZ")
            if extracted_submission_datetime
            else datetime.min
        )

        return SearchResultMeta(
            author=(node.xpath("//source-name/text()") or [""])[0],
            author_email=(node.xpath("//source-email/text()") or [""])[0],
            consignment_reference=(
                node.xpath("//transfer-consignment-reference/text()") or [""]
            )[0],
            submission_datetime=submission_datetime,
            assigned_to=(node.xpath("//assigned-to/text()") or [""])[0],
            editor_hold=(node.xpath("//editor-hold/text()") or [""])[0],
            editor_priority=(node.xpath("//editor-priority/text()") or ["20"])[
                0
            ],  # medium priority default (20)
            last_modified=last_modified,
        )
