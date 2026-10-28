"""Sync resolved judge metadata into ``akn:header`` judge elements."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING

from lxml import etree

from caselawclient.models.documents.metadata.types.judges import judge_names_from_field_values
from caselawclient.xml_helpers import Element

from ..xml import XML
from .akn import (
    AKN_NS,
    DOC_ROOT_CHILDREN_ORDER,
    HEADER_JUDGES_XPATH,
    JUDGMENT_ROOT_CHILDREN_ORDER,
    JUDGMENT_ROOT_XPATH,
    writable_akn_document_root_xpath,
)

if TYPE_CHECKING:
    from caselawclient.models.documents import Document

logger = logging.getLogger(__name__)


class HeaderJudgesWriter:
    """Write resolved judge names into header ``judge`` elements."""

    def write(self, document: Document) -> bool:
        body = document.body
        if not body.supports_header_judges_write_back:
            return False

        resolved = document.metadata_fields.resolve("judges")
        if not resolved.has_any_claims:
            return False

        root_xpath = writable_akn_document_root_xpath(body._xml)  # noqa: SLF001
        if root_xpath is None:
            return False

        names = judge_names_from_field_values(resolved.values)
        live_xml = body._xml  # noqa: SLF001
        trial_tree = copy.deepcopy(live_xml.xml_as_tree)
        trial_xml = XML(etree.tostring(trial_tree))

        try:
            _apply_resolved_judges(trial_xml, root_xpath, names)
        except ValueError as exc:
            logger.warning(
                "Skipping header judges write-back for %s: %s",
                document.uri,
                exc,
            )
            return False

        try:
            _apply_resolved_judges(live_xml, root_xpath, names)
        except ValueError as exc:
            logger.warning(
                "Skipping header judges write-back for %s: %s",
                document.uri,
                exc,
            )
            return False

        body._invalidate_cached_properties("judges")  # noqa: SLF001
        return True


def _apply_resolved_judges(xml: XML, root_xpath: str, names: list[str]) -> None:
    header = _resolve_header_element(xml, root_xpath)
    _remove_header_judge_nodes(xml)
    if not names:
        return

    qname_p = etree.QName(AKN_NS, "p")
    qname_judge = etree.QName(AKN_NS, "judge")
    for name in names:
        paragraph = etree.SubElement(header, qname_p)
        judge_element = etree.SubElement(paragraph, qname_judge)
        judge_element.text = name


def _remove_header_judge_nodes(xml: XML) -> None:
    for judge in list(xml.get_xpath_nodes(HEADER_JUDGES_XPATH)):
        parent = judge.getparent()
        if parent is not None:
            parent.remove(judge)
            if _is_empty_paragraph(parent):
                grandparent = parent.getparent()
                if grandparent is not None:
                    grandparent.remove(parent)


def _is_empty_paragraph(element: Element) -> bool:
    if etree.QName(element).localname != "p":
        return False
    if len(element) > 0:
        return False
    return not (element.text or "").strip()


def _resolve_header_element(xml: XML, root_xpath: str) -> Element:
    header_xpath = f"{root_xpath}/akn:header"
    existing = xml.get_xpath_nodes(header_xpath)
    if len(existing) > 1:
        raise ValueError(f"Multiple header elements under {root_xpath}")
    if existing:
        return existing[0]

    child_order = JUDGMENT_ROOT_CHILDREN_ORDER if root_xpath == JUDGMENT_ROOT_XPATH else DOC_ROOT_CHILDREN_ORDER
    return xml.get_or_create_element_in_child_order(root_xpath, "header", AKN_NS, child_order)
