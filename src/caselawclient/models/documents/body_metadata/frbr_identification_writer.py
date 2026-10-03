"""Sync resolved metadata into ``meta/identification`` FRBR blocks."""

from __future__ import annotations

import copy
import datetime
import logging
from typing import TYPE_CHECKING, cast

from lxml import etree

from caselawclient.models.documents.metadata.fields.field import MetadataDateValue, MetadataStringValue
from caselawclient.xml_helpers import Element

from ..xml import XML
from .akn import (
    AKN_NS,
    DECISION_FRBRDATE_NAMES,
    FRBR_WORK_CHILDREN_ORDER,
    FRBR_WORK_XPATH,
    IDENTIFICATION_XPATH,
    JUDGMENT_NAME_XPATH,
)
from .xml_validation import FrbrIdentificationValidator, validate_frbr_identification_element

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

logger = logging.getLogger(__name__)


class FrbrIdentificationWriter:
    """Write resolved title and decision date metadata into ``FRBRWork``."""

    def __init__(self, identification_validator: FrbrIdentificationValidator | None = None) -> None:
        self._identification_validator = identification_validator

    def write(self, document: Document) -> bool:
        body = document.body
        if not body.supports_metadata_write_back:
            return False

        title_resolved = document.metadata_fields.resolve("title")
        date_resolved = document.metadata_fields.resolve("date")
        needs_title_write = title_resolved.has_any_claims or (not body.name.strip() and _work_has_frbrname(document))
        needs_date_write = date_resolved.has_any_claims
        if not needs_title_write and not needs_date_write:
            return False

        live_xml = body._xml  # noqa: SLF001
        trial_tree = copy.deepcopy(live_xml.xml_as_tree)
        trial_xml = XML(etree.tostring(trial_tree))

        try:
            _apply_resolved_metadata_to_identification(document, trial_xml, needs_title_write, needs_date_write)
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

        try:
            _apply_resolved_metadata_to_identification(document, live_xml, needs_title_write, needs_date_write)
        except ValueError as exc:
            logger.warning(
                "Skipping FRBR identification write-back for %s: %s",
                document.uri,
                exc,
            )
            return False

        invalidate: list[str] = []
        if needs_title_write:
            invalidate.append("name")
        if needs_date_write:
            invalidate.extend(
                (
                    "decision_date_raw",
                    "decision_date_is_unparsable",
                    "document_date_as_date",
                    "document_date_as_string",
                )
            )
        body._invalidate_cached_properties(*invalidate)  # noqa: SLF001
        return True


def _work_has_frbrname(document: Document) -> bool:
    return bool(document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRname"))


def _apply_resolved_metadata_to_identification(
    document: Document,
    xml: XML,
    needs_title_write: bool,
    needs_date_write: bool,
) -> None:
    if len(xml.get_xpath_nodes(FRBR_WORK_XPATH)) != 1:
        raise ValueError("FRBR write-back requires exactly one FRBRWork element under identification")

    if needs_title_write:
        _apply_resolved_title(document, xml)
    if needs_date_write:
        frbr_date_name = _frbr_date_name(document)
        _apply_resolved_decision_date(document, xml, frbr_date_name)


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


def _apply_resolved_decision_date(document: Document, xml: XML, frbr_date_name: str) -> None:
    resolved = document.metadata_fields.resolve("date")
    if resolved.value is None:
        _remove_work_decision_frbrdates(xml)
        return
    decision_date = cast(MetadataDateValue, resolved.value).value
    _upsert_work_decision_frbrdate(xml, frbr_date_name, decision_date)


def _frbr_date_name(document: Document) -> str:
    frbr_date_name = document.body.get_xpath_match_string(JUDGMENT_NAME_XPATH) or "judgment"
    if frbr_date_name not in DECISION_FRBRDATE_NAMES:
        return "judgment"
    return frbr_date_name


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
