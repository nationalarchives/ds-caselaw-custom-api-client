"""Sync resolved metadata into ``meta/identification`` FRBR blocks."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, cast

from lxml import etree

from caselawclient.models.documents.metadata.fields.field import MetadataStringValue
from caselawclient.xml_helpers import Element

from ..xml import XML
from .akn import (
    AKN_NS,
    FRBR_WORK_CHILDREN_ORDER,
    FRBR_WORK_XPATH,
    IDENTIFICATION_XPATH,
)
from .xml_validation import FrbrIdentificationValidator, validate_frbr_identification_element

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

logger = logging.getLogger(__name__)


class FrbrIdentificationWriter:
    """Write resolved title metadata into ``FRBRWork/FRBRname``."""

    def __init__(self, identification_validator: FrbrIdentificationValidator | None = None) -> None:
        self._identification_validator = identification_validator

    def write(self, document: Document) -> bool:
        body = document.body
        if not body.supports_metadata_write_back:
            return False
        if not document.metadata_fields.resolve("title").has_any_claims:
            return False

        live_xml = body._xml  # noqa: SLF001
        trial_tree = copy.deepcopy(live_xml.xml_as_tree)
        trial_xml = XML(etree.tostring(trial_tree))

        try:
            _apply_resolved_title_to_identification(document, trial_xml)
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
        body._invalidate_cached_properties("name")  # noqa: SLF001
        return True


def _apply_resolved_title_to_identification(document: Document, xml: XML) -> None:
    if len(xml.get_xpath_nodes(FRBR_WORK_XPATH)) != 1:
        raise ValueError("Title write-back requires exactly one FRBRWork element under identification")

    _apply_resolved_title(document, xml)


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
