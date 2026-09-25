"""Sync resolved metadata into ``meta/identification`` FRBR blocks."""

from __future__ import annotations

import copy
import datetime
import logging
from typing import TYPE_CHECKING, cast

from lxml import etree

from caselawclient.models.documents.metadata.fields.field import MetadataDateValue, MetadataStringValue
from caselawclient.types import DocumentURIString
from caselawclient.xml_helpers import Element

from ..xml import AKN_META_CHILDREN_ORDER, XML
from .akn import (
    AKN_NS,
    DECISION_FRBRDATE_NAMES,
    DOC_ROOT_CHILDREN_ORDER,
    FCL_BASE,
    FRBR_EXPRESSION_CHILDREN_ORDER,
    FRBR_EXPRESSION_XPATH,
    FRBR_MANIFESTATION_CHILDREN_ORDER,
    FRBR_MANIFESTATION_XPATH,
    FRBR_WORK_CHILDREN_ORDER,
    FRBR_WORK_XPATH,
    IDENTIFICATION_CHILDREN_ORDER,
    IDENTIFICATION_SOURCE,
    IDENTIFICATION_XPATH,
    JUDGMENT_NAME_XPATH,
    JUDGMENT_ROOT_CHILDREN_ORDER,
    JUDGMENT_ROOT_XPATH,
    META_XPATH,
    writable_akn_document_root_xpath,
)
from .xml_validation import FrbrIdentificationValidator, validate_frbr_identification_element

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

logger = logging.getLogger(__name__)

DEFAULT_FRBR_AUTHOR_HREF = "#tna"
DEFAULT_FRBR_COUNTRY = "GB-UKM"
DEFAULT_FRBR_LANGUAGE = "eng"
DEFAULT_FRBR_FORMAT = "application/xml"
PLACEHOLDER_DECISION_DATE = datetime.date(1001, 1, 1)
_DECISION_FRBRDATE_NAME_XPATH_PREDICATE = " or ".join(f"@name='{name}'" for name in sorted(DECISION_FRBRDATE_NAMES))


class FrbrIdentificationWriter:
    """Write resolved metadata into Work, Expression, and Manifestation FRBR elements."""

    def __init__(self, identification_validator: FrbrIdentificationValidator | None = None) -> None:
        self._identification_validator = identification_validator

    def write(self, document: Document) -> bool:
        body = document.body
        if not body.supports_metadata_write_back:
            return False

        live_xml = body._xml  # noqa: SLF001
        trial_tree = copy.deepcopy(live_xml.xml_as_tree)
        trial_xml = XML(etree.tostring(trial_tree))

        try:
            _apply_resolved_metadata_to_identification(document, trial_xml)
        except ValueError as exc:
            logger.warning(
                "Skipping FRBR identification write-back for %s: %s",
                document.uri,
                exc,
            )
            return False

        identification = trial_xml.get_single_xpath_node(IDENTIFICATION_XPATH)
        validate = self._identification_validator or validate_frbr_identification_element
        if invalid_reason := validate(identification):
            logger.warning(
                "Skipping FRBR identification write-back for %s: %s",
                document.uri,
                invalid_reason,
            )
            return False

        live_xml.xml_as_tree = copy.deepcopy(trial_xml.xml_as_tree)
        body._invalidate_cached_properties(  # noqa: SLF001
            "name",
            "decision_date_raw",
            "decision_date_is_unparsable",
            "document_date_as_date",
            "document_date_as_string",
        )
        return True


def _apply_resolved_metadata_to_identification(document: Document, xml: XML) -> None:
    frbr_date_name = _frbr_date_name(document)
    _ensure_meta_and_identification(document, xml)

    title_claims = document.metadata_fields.resolve("title")

    _ensure_frbr_triple(xml)
    _apply_document_uri_frbr_identifiers(document, xml, frbr_date_name)

    if title_claims.has_any_claims:
        _apply_resolved_title(document, xml)

    if document.metadata_fields.resolve("date").has_any_claims:
        _apply_resolved_decision_date(document, xml, frbr_date_name)

    _normalize_frbr_identification_child_order(xml)


def _normalize_frbr_identification_child_order(xml: XML) -> None:
    identification_nodes = xml.get_xpath_nodes(IDENTIFICATION_XPATH)
    if not identification_nodes:
        return
    identification = identification_nodes[0]
    _normalize_element_child_order(identification, IDENTIFICATION_CHILDREN_ORDER)
    for parent_xpath, child_order in (
        (FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER),
        (FRBR_EXPRESSION_XPATH, FRBR_EXPRESSION_CHILDREN_ORDER),
        (FRBR_MANIFESTATION_XPATH, FRBR_MANIFESTATION_CHILDREN_ORDER),
    ):
        for parent in xml.get_xpath_nodes(parent_xpath):
            _normalize_element_child_order(parent, child_order)


def _normalize_element_child_order(parent: Element, child_order: tuple[str, ...]) -> None:
    akn_children = [child for child in parent if isinstance(child.tag, str) and etree.QName(child).namespace == AKN_NS]
    if not akn_children:
        return

    def sort_key(element: Element) -> tuple[int, int]:
        local_name = etree.QName(element).localname
        if local_name not in child_order:
            return len(child_order), 0
        return child_order.index(local_name), 0

    ordered_children = sorted(akn_children, key=sort_key)
    non_akn_children = [child for child in parent if child not in akn_children]
    for child in list(parent):
        parent.remove(child)
    parent.extend(ordered_children)
    parent.extend(non_akn_children)


def _ensure_meta_and_identification(document: Document, xml: XML) -> None:
    root_xpath = writable_akn_document_root_xpath(xml)
    if root_xpath is None:
        raise ValueError("Document body has no writable judgment or doc root")

    root_child_order = JUDGMENT_ROOT_CHILDREN_ORDER if root_xpath == JUDGMENT_ROOT_XPATH else DOC_ROOT_CHILDREN_ORDER
    xml.get_or_create_element_in_child_order(root_xpath, "meta", AKN_NS, root_child_order)

    identification = xml.get_or_create_element_in_child_order(
        META_XPATH,
        "identification",
        AKN_NS,
        AKN_META_CHILDREN_ORDER,
    )
    if not identification.get("source"):
        identification.set("source", IDENTIFICATION_SOURCE)


def _ensure_frbr_triple(xml: XML) -> None:
    for local_name in IDENTIFICATION_CHILDREN_ORDER:
        xml.get_or_create_element_in_child_order(
            IDENTIFICATION_XPATH,
            local_name,
            AKN_NS,
            IDENTIFICATION_CHILDREN_ORDER,
        )


def _apply_document_uri_frbr_identifiers(document: Document, xml: XML, frbr_date_name: str) -> None:
    work_uri, expression_uri, manifestation_uri = _frbr_uris_for_document_uri(document.uri)
    decision_date = _existing_decision_date_for_scaffold(xml, frbr_date_name)

    _sync_frbr_work_level(xml, frbr_date_name, work_uri, decision_date)
    _sync_frbr_expression_level(xml, frbr_date_name, expression_uri, decision_date)
    _sync_frbr_manifestation_level(xml, manifestation_uri, decision_date, frbr_date_name)


def _apply_resolved_decision_date(document: Document, xml: XML, frbr_date_name: str) -> None:
    resolved = document.metadata_fields.resolve("date")
    if resolved.value is None:
        _remove_work_decision_frbrdates(xml)
        return
    decision_date = cast(MetadataDateValue, resolved.value).value
    _upsert_work_decision_frbrdate(xml, frbr_date_name, decision_date)


def _apply_resolved_title(document: Document, xml: XML) -> None:
    resolved = document.metadata_fields.resolve("title")
    if resolved.value is None:
        _remove_frbr_children(xml, FRBR_WORK_XPATH, "FRBRname")
        return
    title = cast(MetadataStringValue, resolved.value).value.strip()
    if not title:
        _remove_frbr_children(xml, FRBR_WORK_XPATH, "FRBRname")
        return
    name_element = _ensure_frbr_child(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, "FRBRname")
    xml.set_element_attribute(name_element, "value", title)


def _frbr_date_name(document: Document) -> str:
    frbr_date_name = document.body.get_xpath_match_string(JUDGMENT_NAME_XPATH) or "judgment"
    if frbr_date_name not in DECISION_FRBRDATE_NAMES:
        return "judgment"
    return frbr_date_name


def _frbr_uris_for_document_uri(document_uri: DocumentURIString) -> tuple[str, str, str]:
    path = document_uri.lstrip("/")
    work_uri = f"{FCL_BASE}/id/{path}"
    expression_uri = f"{FCL_BASE}/{path}"
    manifestation_uri = f"{FCL_BASE}/{path}/data.xml"
    return work_uri, expression_uri, manifestation_uri


def _existing_decision_date_for_scaffold(xml: XML, _frbr_date_name: str) -> datetime.date:
    for xpath in (FRBR_WORK_XPATH, FRBR_EXPRESSION_XPATH, FRBR_MANIFESTATION_XPATH):
        for date_string in xml.get_xpath_match_strings(
            f"{xpath}/akn:FRBRdate[{_DECISION_FRBRDATE_NAME_XPATH_PREDICATE}]/@date"
        ):
            try:
                return datetime.date.fromisoformat(date_string)
            except ValueError:
                continue
    return PLACEHOLDER_DECISION_DATE


def _sync_frbr_work_level(
    xml: XML,
    frbr_date_name: str,
    work_uri: str,
    decision_date: datetime.date,
) -> None:
    _ensure_frbr_this_uri(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, work_uri)
    _ensure_frbr_uri(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, work_uri)
    _ensure_named_frbr_date(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, decision_date, frbr_date_name)
    _ensure_frbr_author(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER)
    _ensure_frbr_country(xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER)


def _sync_frbr_expression_level(
    xml: XML,
    frbr_date_name: str,
    expression_uri: str,
    decision_date: datetime.date,
) -> None:
    _ensure_frbr_this_uri(xml, FRBR_EXPRESSION_XPATH, FRBR_EXPRESSION_CHILDREN_ORDER, expression_uri)
    _ensure_frbr_uri(xml, FRBR_EXPRESSION_XPATH, FRBR_EXPRESSION_CHILDREN_ORDER, expression_uri)
    _ensure_named_frbr_date(
        xml,
        FRBR_EXPRESSION_XPATH,
        FRBR_EXPRESSION_CHILDREN_ORDER,
        decision_date,
        frbr_date_name,
    )
    _ensure_frbr_author(xml, FRBR_EXPRESSION_XPATH, FRBR_EXPRESSION_CHILDREN_ORDER)
    language = _ensure_frbr_child(xml, FRBR_EXPRESSION_XPATH, FRBR_EXPRESSION_CHILDREN_ORDER, "FRBRlanguage")
    if not language.get("language"):
        language.set("language", DEFAULT_FRBR_LANGUAGE)


def _sync_frbr_manifestation_level(
    xml: XML,
    manifestation_uri: str,
    decision_date: datetime.date,
    frbr_date_name: str,
) -> None:
    _ensure_frbr_this_uri(xml, FRBR_MANIFESTATION_XPATH, FRBR_MANIFESTATION_CHILDREN_ORDER, manifestation_uri)
    _ensure_frbr_uri(xml, FRBR_MANIFESTATION_XPATH, FRBR_MANIFESTATION_CHILDREN_ORDER, manifestation_uri)
    _ensure_named_frbr_date(
        xml,
        FRBR_MANIFESTATION_XPATH,
        FRBR_MANIFESTATION_CHILDREN_ORDER,
        decision_date,
        frbr_date_name,
    )
    _ensure_frbr_author(xml, FRBR_MANIFESTATION_XPATH, FRBR_MANIFESTATION_CHILDREN_ORDER)
    frbr_format = _ensure_frbr_child(xml, FRBR_MANIFESTATION_XPATH, FRBR_MANIFESTATION_CHILDREN_ORDER, "FRBRformat")
    if not frbr_format.get("value"):
        frbr_format.set("value", DEFAULT_FRBR_FORMAT)


def _ensure_frbr_this_uri(xml: XML, parent_xpath: str, child_order: tuple[str, ...], uri: str) -> None:
    element = _ensure_frbr_child(xml, parent_xpath, child_order, "FRBRthis")
    xml.set_element_attribute(element, "value", uri)


def _ensure_frbr_uri(xml: XML, parent_xpath: str, child_order: tuple[str, ...], uri: str) -> None:
    element = _ensure_frbr_child(xml, parent_xpath, child_order, "FRBRuri")
    xml.set_element_attribute(element, "value", uri)


def _ensure_frbr_author(xml: XML, parent_xpath: str, child_order: tuple[str, ...]) -> None:
    element = _ensure_frbr_child(xml, parent_xpath, child_order, "FRBRauthor")
    if not element.get("href"):
        element.set("href", DEFAULT_FRBR_AUTHOR_HREF)


def _ensure_frbr_country(xml: XML, parent_xpath: str, child_order: tuple[str, ...]) -> None:
    if parent_xpath != FRBR_WORK_XPATH:
        return
    element = _ensure_frbr_child(xml, parent_xpath, child_order, "FRBRcountry")
    if not element.get("value"):
        element.set("value", DEFAULT_FRBR_COUNTRY)


def _frbr_work_frbrdate_elements(xml: XML) -> list[Element]:
    return xml.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate")


def _work_decision_frbrdate_elements(xml: XML) -> list[Element]:
    return [
        element
        for element in _frbr_work_frbrdate_elements(xml)
        if (element.get("name") or "") in DECISION_FRBRDATE_NAMES
    ]


def _legacy_unnamed_work_frbrdate_element(xml: XML) -> Element | None:
    unnamed_dates = [element for element in _frbr_work_frbrdate_elements(xml) if (element.get("name") or "") == ""]
    if len(unnamed_dates) != 1:
        return None
    return unnamed_dates[0]


def _remove_work_decision_frbrdates(xml: XML) -> None:
    qname = etree.QName(AKN_NS, "FRBRdate")
    for parent in xml.get_xpath_nodes(FRBR_WORK_XPATH):
        children = list(parent.findall(qname))
        decision_dates = [child for child in children if (child.get("name") or "") in DECISION_FRBRDATE_NAMES]
        if decision_dates:
            for child in decision_dates:
                parent.remove(child)
            continue
        unnamed_dates = [child for child in children if (child.get("name") or "") == ""]
        if len(unnamed_dates) == 1:
            parent.remove(unnamed_dates[0])


def _upsert_work_decision_frbrdate(xml: XML, frbr_date_name: str, decision_date: datetime.date) -> None:
    existing_decision_dates = _work_decision_frbrdate_elements(xml)
    if len(existing_decision_dates) > 1:
        raise ValueError("Multiple decision FRBRdate elements under FRBRWork")
    if existing_decision_dates:
        frbr_date = existing_decision_dates[0]
    else:
        legacy_unnamed = _legacy_unnamed_work_frbrdate_element(xml)
        if legacy_unnamed is not None:
            frbr_date = legacy_unnamed
        else:
            frbr_date = xml.insert_element_in_child_order(
                FRBR_WORK_XPATH,
                "FRBRdate",
                AKN_NS,
                FRBR_WORK_CHILDREN_ORDER,
            )
    xml.set_element_attribute(frbr_date, "date", decision_date.isoformat())
    xml.set_element_attribute(frbr_date, "name", frbr_date_name)


def _ensure_named_frbr_date(
    xml: XML,
    parent_xpath: str,
    child_order: tuple[str, ...],
    decision_date: datetime.date,
    frbr_date_name: str,
) -> None:
    parent = xml.get_single_xpath_node(parent_xpath)
    qname = etree.QName(AKN_NS, "FRBRdate")
    for child in parent.findall(qname):
        if child.get("name") == frbr_date_name:
            return
    for child in parent.findall(qname):
        if (child.get("name") or "") in DECISION_FRBRDATE_NAMES:
            xml.set_element_attribute(child, "date", decision_date.isoformat())
            xml.set_element_attribute(child, "name", frbr_date_name)
            return
    if parent_xpath == FRBR_WORK_XPATH:
        legacy_unnamed = _legacy_unnamed_work_frbrdate_element(xml)
        if legacy_unnamed is not None:
            xml.set_element_attribute(legacy_unnamed, "date", decision_date.isoformat())
            xml.set_element_attribute(legacy_unnamed, "name", frbr_date_name)
            return
    date_element = xml.insert_element_in_child_order(parent_xpath, "FRBRdate", AKN_NS, child_order)
    date_element.set("date", decision_date.isoformat())
    date_element.set("name", frbr_date_name)


def _ensure_frbr_child(xml: XML, parent_xpath: str, child_order: tuple[str, ...], local_name: str) -> Element:
    if local_name not in child_order:
        raise ValueError(f"Element {local_name!r} is not listed in child_order")
    parent = xml.get_single_xpath_node(parent_xpath)
    qname = etree.QName(AKN_NS, local_name)
    existing = parent.findall(qname)
    if len(existing) > 1:
        raise ValueError(f"Multiple {local_name} elements under {parent_xpath}")
    if existing:
        return existing[0]
    return xml.insert_element_in_child_order(parent_xpath, local_name, AKN_NS, child_order)


def _remove_frbr_children(xml: XML, parent_xpath: str, child_local_name: str) -> None:
    qname = etree.QName(AKN_NS, child_local_name)
    for parent in xml.get_xpath_nodes(parent_xpath):
        for child in list(parent.findall(qname)):
            parent.remove(child)
