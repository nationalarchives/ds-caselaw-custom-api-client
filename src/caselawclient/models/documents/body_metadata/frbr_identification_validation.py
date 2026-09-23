"""Structural validation for ``meta/identification`` FRBR blocks."""

from __future__ import annotations

from lxml import etree

from caselawclient.xml_helpers import Element

from .akn import (
    AKN_NS,
    DECISION_FRBRDATE_NAMES,
    FRBR_EXPRESSION_CHILDREN_ORDER,
    FRBR_MANIFESTATION_CHILDREN_ORDER,
    FRBR_WORK_CHILDREN_ORDER,
    IDENTIFICATION_CHILDREN_ORDER,
)


def frbr_identification_validation_failure(identification: Element) -> str | None:
    """Return a reason string when ``identification`` is invalid, else ``None``."""
    if etree.QName(identification).localname != "identification":
        return "node is not an identification element"
    if etree.QName(identification).namespace != AKN_NS:
        return "identification is not in the Akoma Ntoso namespace"
    if not (identification.get("source") or "").strip():
        return "identification is missing a source attribute"

    work, expression, manifestation = _identification_frbr_triple(identification)
    if work is None:
        return "identification is missing FRBRWork"
    if expression is None:
        return "identification is missing FRBRExpression"
    if manifestation is None:
        return "identification is missing FRBRManifestation"

    extra_children = _unexpected_identification_children(identification)
    if extra_children:
        return f"identification has unexpected children: {', '.join(extra_children)}"

    for label, element, child_order, required in (
        ("FRBRWork", work, FRBR_WORK_CHILDREN_ORDER, _required_work_children()),
        ("FRBRExpression", expression, FRBR_EXPRESSION_CHILDREN_ORDER, _required_expression_children()),
        ("FRBRManifestation", manifestation, FRBR_MANIFESTATION_CHILDREN_ORDER, _required_manifestation_children()),
    ):
        if reason := _frbr_level_validation_failure(label, element, child_order, required):
            return reason

    return None


def is_valid_frbr_identification(identification: Element) -> bool:
    return frbr_identification_validation_failure(identification) is None


def _identification_frbr_triple(identification: Element) -> tuple[Element | None, Element | None, Element | None]:
    work = expression = manifestation = None
    for child in identification:
        if not isinstance(child.tag, str):
            continue
        qname = etree.QName(child)
        if qname.namespace != AKN_NS:
            continue
        if qname.localname == "FRBRWork":
            work = child
        elif qname.localname == "FRBRExpression":
            expression = child
        elif qname.localname == "FRBRManifestation":
            manifestation = child
    return work, expression, manifestation


def _unexpected_identification_children(identification: Element) -> list[str]:
    allowed = set(IDENTIFICATION_CHILDREN_ORDER)
    unexpected: list[str] = []
    for child in identification:
        if not isinstance(child.tag, str):
            continue
        qname = etree.QName(child)
        if qname.namespace != AKN_NS:
            unexpected.append(qname.localname)
            continue
        if qname.localname not in allowed:
            unexpected.append(qname.localname)
    return unexpected


def _required_work_children() -> frozenset[str]:
    return frozenset({"FRBRthis", "FRBRuri", "FRBRdate", "FRBRauthor", "FRBRcountry"})


def _required_expression_children() -> frozenset[str]:
    return frozenset({"FRBRthis", "FRBRuri", "FRBRdate", "FRBRauthor", "FRBRlanguage"})


def _required_manifestation_children() -> frozenset[str]:
    return frozenset({"FRBRthis", "FRBRuri", "FRBRdate", "FRBRauthor", "FRBRformat"})


def _frbr_level_validation_failure(
    label: str,
    element: Element,
    child_order: tuple[str, ...],
    required_local_names: frozenset[str],
) -> str | None:
    if etree.QName(element).localname != label:
        return f"expected {label} element"

    children_by_name = _akn_children_by_local_name(element)
    for local_name in required_local_names:
        if local_name not in children_by_name:
            return f"{label} is missing {local_name}"

    for local_name, nodes in children_by_name.items():
        if local_name not in child_order:
            return f"{label} has unexpected child {local_name}"
        if local_name != "FRBRdate" and len(nodes) > 1:
            return f"{label} has multiple {local_name} elements"

    if reason := _check_frbr_attribute_values(label, children_by_name):
        return reason

    if reason := _check_child_order(label, element, child_order):
        return reason

    return None


def _akn_children_by_local_name(element: Element) -> dict[str, list[Element]]:
    grouped: dict[str, list[Element]] = {}
    for child in element:
        if not isinstance(child.tag, str):
            continue
        qname = etree.QName(child)
        if qname.namespace != AKN_NS:
            continue
        grouped.setdefault(qname.localname, []).append(child)
    return grouped


def _check_frbr_attribute_values(label: str, children_by_name: dict[str, list[Element]]) -> str | None:
    for local_name in ("FRBRthis", "FRBRuri", "FRBRcountry", "FRBRformat"):
        for node in children_by_name.get(local_name, []):
            if not (node.get("value") or "").strip():
                return f"{label}/{local_name} is missing a value attribute"

    for node in children_by_name.get("FRBRauthor", []):
        if not (node.get("href") or "").strip():
            return f"{label}/FRBRauthor is missing an href attribute"

    for node in children_by_name.get("FRBRlanguage", []):
        if not (node.get("language") or "").strip():
            return f"{label}/FRBRlanguage is missing a language attribute"

    return _check_decision_frbrdate_values(label, children_by_name)


def _check_decision_frbrdate_values(label: str, children_by_name: dict[str, list[Element]]) -> str | None:
    decision_dates = [
        node for node in children_by_name.get("FRBRdate", []) if (node.get("name") or "") in DECISION_FRBRDATE_NAMES
    ]
    if not decision_dates:
        return f"{label} is missing a decision FRBRdate"
    for node in decision_dates:
        if not (node.get("date") or "").strip():
            return f"{label}/FRBRdate is missing a date attribute"
    return None


def _check_child_order(label: str, element: Element, child_order: tuple[str, ...]) -> str | None:
    seen_order_indices: list[int] = []
    for child in element:
        if not isinstance(child.tag, str):
            continue
        qname = etree.QName(child)
        if qname.namespace != AKN_NS:
            return f"{label} contains a non-AKN child"
        local_name = qname.localname
        if local_name not in child_order:
            return f"{label} contains unexpected child {local_name}"
        index = child_order.index(local_name)
        if seen_order_indices and index < seen_order_indices[-1]:
            return f"{label} child elements are not in schema order"
        seen_order_indices.append(index)
    return None
