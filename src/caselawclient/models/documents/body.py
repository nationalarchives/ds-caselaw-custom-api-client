import datetime
import os
import warnings
from functools import cached_property
from typing import Optional

import pytz
from ds_caselaw_utils.types import CourtCode
from saxonche import PySaxonProcessor
from typing_extensions import deprecated

from caselawclient.models.documents.metadata.types.date import date_as_string_from_value
from caselawclient.models.utilities.dates import parse_string_date_as_utc
from caselawclient.types import DocumentCategory
from caselawclient.xml_helpers import DEFAULT_NAMESPACES, Element

from .xml import XML


class UnparsableDate(Warning):
    pass


NAME_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
COURT_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court/text()"
JURISDICTION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:jurisdiction/text()"
CATEGORIES_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category"
CASE_NUMBER_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:caseNumber/text()"
DATE_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date"


def categories_from_nodes(nodes: list[Element]) -> list[DocumentCategory]:
    """Build a tree of document categories from Akoma Ntoso category XML nodes.

    Top-level categories (nodes without a ``parent`` attribute) are returned in
    document order. Child categories are attached to their parent's
    ``subcategories`` list.
    """
    categories: dict[str, DocumentCategory] = {}
    children_map: dict[str, list[DocumentCategory]] = {}

    for node in nodes:
        name = node.text
        if name is None or not name.strip():
            continue

        category = DocumentCategory(name=name)
        categories[name] = category

        parent = node.get("parent")

        if parent:
            children_map.setdefault(parent, []).append(category)

    for parent, subcategories in children_map.items():
        if parent in categories:
            categories[parent].subcategories.extend(subcategories)

    return [
        categories[name] for node in nodes if node.get("parent") is None if (name := node.text) and name in categories
    ]


class DocumentBody:
    """
    A class for abstracting out interactions with the body of a document.
    """

    def __init__(self, xml_bytestring: bytes):
        self._xml = XML(xml_bytestring=xml_bytestring)
        """ This is an instance of the `Document.XML` class for manipulation of the XML document itself. """

    def get_xpath_match_string(self, xpath: str) -> str:
        return self._xml.get_xpath_match_string(xpath)

    def get_xpath_match_strings(self, xpath: str) -> list[str]:
        return self._xml.get_xpath_match_strings(xpath)

    def get_xpath_nodes(self, xpath: str) -> list[Element]:
        return self._xml.get_xpath_nodes(xpath)

    @cached_property
    def name(self) -> str:
        return self.get_xpath_match_string(NAME_XPATH)

    @cached_property
    def court(self) -> str:
        return self.get_xpath_match_string(COURT_XPATH)

    @cached_property
    def jurisdiction(self) -> str:
        return self.get_xpath_match_string(JURISDICTION_XPATH)

    @cached_property
    def categories(self) -> list[DocumentCategory]:
        return categories_from_nodes(self.get_xpath_nodes(CATEGORIES_XPATH))

    # NOTE: Deprecated - use categories function
    @cached_property
    def category(self) -> Optional[str]:
        return self.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category[not(@parent)][1]/text()"
        )

    @cached_property
    def case_number(self) -> Optional[str]:
        return self.get_xpath_match_string(CASE_NUMBER_XPATH)

    @property
    def court_and_jurisdiction_identifier_string(self) -> CourtCode:
        if self.jurisdiction != "":
            return CourtCode("/".join((self.court, self.jurisdiction)))
        return CourtCode(self.court)

    @cached_property
    def document_date_as_date(self) -> Optional[datetime.date]:
        date_as_string = self.get_xpath_match_string(DATE_XPATH)
        if not date_as_string:
            return None
        try:
            return datetime.datetime.strptime(
                date_as_string,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            warnings.warn(
                f"Unparsable date encountered: {date_as_string}",
                UnparsableDate,
            )
            return None

    @cached_property
    @deprecated("Use Document.metadata['date'].as_string instead")
    def document_date_as_string(self) -> str:
        return date_as_string_from_value(self.document_date_as_date)

    def get_manifestation_datetimes(
        self,
        name: Optional[str] = None,
    ) -> list[datetime.datetime]:
        name_filter = f"[@name='{name}']" if name else ""
        iso_datetimes = self.get_xpath_match_strings(
            f"/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRdate{name_filter}/@date",
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

    @property
    def content_as_xml_tree(self) -> Element:
        """Get the XML tree representation of the document."""
        return self._xml.xml_as_tree

    @cached_property
    def has_content(self) -> bool:
        """Does this XML contain rendered document content?

        There are two main judgment shapes we need to handle.

        PDF-only documents may have visible text only in the header and no usable
        judgment body content.

        DOCX-backed documents usually have visible text in both the header and the
        judgment body, but parser edge cases can leave the header empty even when
        the judgment body still contains the rendered judgment text.

        Press summaries are represented as top-level ``doc`` nodes and
        are assumed to have content.
        """
        return bool(
            self._xml.xml_as_tree.xpath("//akn:header[normalize-space(string(.))]", namespaces=DEFAULT_NAMESPACES)
            or self._xml.xml_as_tree.xpath(
                "//akn:judgmentBody[normalize-space(string(.))]", namespaces=DEFAULT_NAMESPACES
            )
            or self._xml.xml_as_tree.xpath("//akn:doc", namespaces=DEFAULT_NAMESPACES)
        )

    @cached_property
    def has_external_data(self) -> bool:
        """Is there data which is not present within the source document:
        is there a spreadsheet which has populated some fields. The current implementation
        "is there a uk:party tag" is intended as a stopgap whilst we're not importing that data."""
        return bool(self._xml.xml_as_tree.xpath("//uk:party", namespaces=DEFAULT_NAMESPACES))

    def content_html(self, image_prefix: str) -> Optional[str]:
        """Convert the XML representation of the Document into HTML for rendering."""
        """This used to be called content_as_html but we have changed the parameter passed to it from the
        domain of the assets to the path in which the assets are stored (from assets to assets/d-a1b2c3)
        and made the image_prefix mandatory"""
        if not self.has_content:
            return None

        html_xslt_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), "transforms", "html.xsl")

        with PySaxonProcessor() as proc:
            xslt_processor = proc.new_xslt30_processor()
            document = proc.parse_xml(xml_text=self._xml.xml_as_string)

            executable = xslt_processor.compile_stylesheet(stylesheet_file=html_xslt_location)

            if image_prefix:
                executable.set_parameter("image-prefix", proc.make_string_value(image_prefix))

            return str(executable.transform_to_string(xdm_node=document))

    @cached_property
    def failed_to_parse(self) -> bool:
        """
        Did this document entirely fail to parse?

        :return: `True` if there was a complete parser failure, otherwise `False`
        """
        return "error" in self._xml.root_element

    def apply_xslt(self, xslt_filename: str, **values: str) -> bytes:
        return self._xml.apply_xslt(xslt_filename, **values)
