import datetime
import os
import warnings
from functools import cached_property

from ds_caselaw_utils.types import CourtCode
from lxml import etree
from saxonche import PySaxonProcessor
from typing_extensions import deprecated

from caselawclient.models.documents.metadata.fields.field import MetadataPartyValue
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
JUDGES_XPATH = "/akn:akomaNtoso/akn:*/akn:header//akn:judge"
PARTIES_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:party"
AKN_NS = DEFAULT_NAMESPACES["akn"]
UK_NS = DEFAULT_NAMESPACES["uk"]
FRBR_WORK_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork"
FRBR_EXPRESSION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression"
IDENTIFICATION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification"
PROPRIETARY_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary"
JUDGMENT_NAME_XPATH = "/akn:akomaNtoso/akn:*/@name"
LIFECYCLE_EVENTREF_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:lifecycle/akn:eventRef"


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


def judges_from_nodes(nodes: list[Element]) -> list[str]:
    """Extract unique judge display names from Akoma Ntoso ``judge`` nodes.

    Names are returned in first-seen document order. Empty or whitespace-only
    text is skipped; duplicate names are de-duplicated. Nested inline markup
    inside a ``judge`` node is flattened via ``itertext``.
    """
    judges: list[str] = []

    for node in nodes:
        name = "".join(node.itertext()).strip()
        if not name or name in judges:
            continue
        judges.append(name)

    return judges


def parties_from_nodes(nodes: list[Element]) -> list[MetadataPartyValue]:
    """Extract unique parties from Akoma Ntoso ``uk:party`` nodes.

    Parties are returned in first-seen document order. Empty or whitespace-only
    names are skipped; duplicate name+role pairs are de-duplicated. Nested inline
    markup inside a party node is flattened via ``itertext``. Role is taken from
    the ``role`` attribute when present.
    """
    parties: list[MetadataPartyValue] = []

    for node in nodes:
        name = "".join(node.itertext()).strip()
        if not name:
            continue
        role = node.get("role")
        party = MetadataPartyValue(name=name, role=role)
        if party in parties:
            continue
        parties.append(party)

    return parties


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

    @property
    def supports_metadata_write_back(self) -> bool:
        """True when this body has AKN identification metadata that write-back can update."""
        return bool(self.get_xpath_nodes(IDENTIFICATION_XPATH))

    def _invalidate_cached_properties(self, *property_names: str) -> None:
        for name in {*property_names, "content_as_xml"}:
            self.__dict__.pop(name, None)

    def write_title(self, title: str) -> None:
        name_element = self._xml.get_or_create_element(FRBR_WORK_XPATH, "FRBRname", AKN_NS)
        self._xml.set_element_attribute(name_element, "value", title)
        self._invalidate_cached_properties("name")

    def write_decision_date(self, decision_date: datetime.date) -> None:
        date_string = decision_date.isoformat()
        frbr_date_name = self.get_xpath_match_string(JUDGMENT_NAME_XPATH) or "judgment"
        self._xml.get_or_create_element(IDENTIFICATION_XPATH, "FRBRExpression", AKN_NS)
        for work_parent_xpath in (FRBR_WORK_XPATH, FRBR_EXPRESSION_XPATH):
            frbr_date = self._xml.get_or_create_element(work_parent_xpath, "FRBRdate", AKN_NS)
            self._xml.set_element_attribute(frbr_date, "date", date_string)
            self._xml.set_element_attribute(frbr_date, "name", frbr_date_name)

        year_element = self._xml.get_or_create_element(PROPRIETARY_XPATH, "year", UK_NS)
        self._xml.set_element_value(year_element, str(decision_date.year))

        event_refs = self.get_xpath_nodes(LIFECYCLE_EVENTREF_XPATH)
        if event_refs:
            self._xml.set_element_attribute(event_refs[0], "date", date_string)

        self._invalidate_cached_properties("document_date_as_date", "document_date_as_string")

    def clear_decision_date(self) -> None:
        for frbr_date in self.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate") + self.get_xpath_nodes(
            f"{FRBR_EXPRESSION_XPATH}/akn:FRBRdate"
        ):
            parent = frbr_date.getparent()
            if parent is not None:
                parent.remove(frbr_date)
        self._xml.replace_child_elements(PROPRIETARY_XPATH, "year", UK_NS, [])
        for event_ref in self.get_xpath_nodes(LIFECYCLE_EVENTREF_XPATH):
            event_ref.attrib.pop("date", None)
        self._invalidate_cached_properties("document_date_as_date", "document_date_as_string")

    def _proprietary_uk_text_elements(self, local_name: str, text_values: list[str]) -> list[Element]:
        elements: list[Element] = []
        for text in text_values:
            element = etree.Element(etree.QName(UK_NS, local_name))
            element.text = text
            elements.append(element)
        return elements

    def write_court(self, court: str) -> None:
        if court == "":
            if self.get_xpath_nodes(f"{PROPRIETARY_XPATH}/uk:court"):
                self._xml.replace_child_elements(PROPRIETARY_XPATH, "court", UK_NS, [])
            else:
                self._xml.replace_child_elements(
                    PROPRIETARY_XPATH,
                    "court",
                    UK_NS,
                    self._proprietary_uk_text_elements("court", [""]),
                )
        else:
            self._xml.replace_child_elements(
                PROPRIETARY_XPATH,
                "court",
                UK_NS,
                self._proprietary_uk_text_elements("court", [court]),
            )
        self._invalidate_cached_properties("court")

    def write_jurisdiction(self, jurisdiction: str) -> None:
        if jurisdiction == "":
            self._xml.replace_child_elements(PROPRIETARY_XPATH, "jurisdiction", UK_NS, [])
        else:
            self._xml.replace_child_elements(
                PROPRIETARY_XPATH,
                "jurisdiction",
                UK_NS,
                self._proprietary_uk_text_elements("jurisdiction", [jurisdiction]),
            )
        self._invalidate_cached_properties("jurisdiction")

    def write_case_numbers(self, case_numbers: list[str]) -> None:
        elements = self._proprietary_uk_text_elements("caseNumber", case_numbers) if case_numbers else []
        self._xml.replace_child_elements(PROPRIETARY_XPATH, "caseNumber", UK_NS, elements)
        self._invalidate_cached_properties("case_number")

    def write_categories(self, categories: list[DocumentCategory]) -> None:
        elements: list[Element] = []

        def append_categories(tree: list[DocumentCategory], parent: str | None) -> None:
            for category in tree:
                if not category.name.strip():
                    continue
                element = etree.Element(etree.QName(UK_NS, "category"))
                element.text = category.name
                if parent is not None:
                    element.set("parent", parent)
                elements.append(element)
                append_categories(category.subcategories, category.name)

        append_categories(categories, None)
        self._xml.replace_child_elements(PROPRIETARY_XPATH, "category", UK_NS, elements)
        self._invalidate_cached_properties("categories", "category")

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
    def category(self) -> str | None:
        return self.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category[not(@parent)][1]/text()"
        )

    @cached_property
    def case_number(self) -> str | None:
        return self.get_xpath_match_string(CASE_NUMBER_XPATH)

    @cached_property
    def judges(self) -> list[str]:
        return judges_from_nodes(self.get_xpath_nodes(JUDGES_XPATH))

    @cached_property
    def parties(self) -> list[MetadataPartyValue]:
        return parties_from_nodes(self.get_xpath_nodes(PARTIES_XPATH))

    @property
    def court_and_jurisdiction_identifier_string(self) -> CourtCode:
        if self.jurisdiction != "":
            return CourtCode(f"{self.court}/{self.jurisdiction}")
        return CourtCode(self.court)

    @cached_property
    def document_date_as_date(self) -> datetime.date | None:
        date_as_string = self.get_xpath_match_string(DATE_XPATH)
        if not date_as_string:
            return None
        try:
            return datetime.date.fromisoformat(date_as_string)
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
        name: str | None = None,
    ) -> list[datetime.datetime]:
        name_filter = f"[@name='{name}']" if name else ""
        iso_datetimes = self.get_xpath_match_strings(
            f"/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRManifestation/akn:FRBRdate{name_filter}/@date",
        )

        return [parse_string_date_as_utc(event, datetime.UTC) for event in iso_datetimes]

    def get_latest_manifestation_datetime(
        self,
        name: str | None = None,
    ) -> datetime.datetime | None:
        events = self.get_manifestation_datetimes(name)
        if not events:
            return None
        return max(events)

    def get_latest_manifestation_type(self) -> str | None:
        return max(
            (
                (type, time)
                for type in ["transform", "tna-enriched"]
                if (time := self.get_latest_manifestation_datetime(type))
            ),
            key=lambda x: x[1],
        )[0]

    @cached_property
    def transformation_datetime(self) -> datetime.datetime | None:
        """When was this document successfully parsed or reparsed (date from XML)"""
        return self.get_latest_manifestation_datetime("transform")

    @cached_property
    def enrichment_datetime(self) -> datetime.datetime | None:
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

    def content_html(self, image_prefix: str) -> str | None:
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
