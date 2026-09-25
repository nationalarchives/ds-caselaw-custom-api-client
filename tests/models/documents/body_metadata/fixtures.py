"""Shared XML fixtures and helpers for body metadata write-back tests."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from lxml import etree

from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.metadata.fields.field import MetadataDateValue, MetadataField, MetadataStringValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import DEFAULT_NAMESPACES

AKN_NS = DEFAULT_NAMESPACES["akn"]
UK_NS = DEFAULT_NAMESPACES["uk"]
AKN_NS_URI = AKN_NS

FIXTURES_DIR = Path(__file__).parent / "fixtures"

FRBRWORK_NAME_VALUE_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
WORK_DECISION_FRBRDATE_XPATH = (
    "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/"
    "akn:FRBRdate[(@name='judgment' or @name='decision')]/@date"
)
EXPRESSION_DECISION_FRBRDATE_XPATH = (
    "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression/"
    "akn:FRBRdate[(@name='judgment' or @name='decision')]/@date"
)
IDENTIFICATION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification"


def read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def _identification_from_root(root: etree._Element) -> etree._Element:
    node = root.xpath("//akn:identification", namespaces=DEFAULT_NAMESPACES)[0]
    return node


def fresh_valid_identification() -> etree._Element:
    """Deep copy of a valid ``meta/identification`` node for per-test mutation."""
    root = etree.fromstring(read_fixture("valid_frbr_identification_judgment.xml"))
    return deepcopy(_identification_from_root(root))


def valid_frbr_triple_inner() -> str:
    identification = _identification_from_root(etree.fromstring(read_fixture("valid_frbr_identification_judgment.xml")))
    return "".join(etree.tostring(child, encoding="unicode") for child in identification if isinstance(child.tag, str))


def judgment_with_identification(
    *,
    judgment_name: str = "judgment",
    triple_inner: str | None = None,
    extra_identification_siblings: str = "",
    source: str | None = "#tna",
) -> bytes:
    if triple_inner is None and judgment_name == "judgment" and not extra_identification_siblings and source == "#tna":
        return read_fixture("valid_frbr_identification_judgment.xml")
    triple = triple_inner if triple_inner is not None else valid_frbr_triple_inner()
    source_attr = f' source="{source}"' if source is not None else ""
    return f"""<akomaNtoso xmlns="{AKN_NS_URI}">
  <judgment name="{judgment_name}">
    <meta><identification{source_attr}>
{triple}{extra_identification_siblings}
    </identification></meta>
    <header><p/></header>
    <judgmentBody><decision><p/></decision></judgmentBody>
  </judgment>
</akomaNtoso>""".encode()


def doc_with_identification(
    *,
    triple_inner: str,
    doc_name: str = "pressSummary",
    extra_identification_siblings: str = "",
    source: str = "#tna",
    include_main_body: bool = True,
) -> bytes:
    main_body = "    <mainBody><p/></mainBody>\n" if include_main_body else ""
    return f"""<akomaNtoso xmlns="{AKN_NS_URI}">
  <doc name="{doc_name}">
    <meta><identification source="{source}">
{triple_inner}
{extra_identification_siblings}    </identification></meta>
{main_body}  </doc>
</akomaNtoso>""".encode()


def judgment_minimal_body(*, judgment_name: str = "judgment") -> DocumentBody:
    xml = read_fixture("judgment_minimal.xml").replace(b"{{JUDGMENT_NAME}}", judgment_name.encode())
    return DocumentBody(xml)


def doc_press_summary_body() -> DocumentBody:
    return DocumentBody(read_fixture("doc_press_summary.xml"))


def doc_minimal_body(*, include_main_body: bool = True) -> DocumentBody:
    main_body = "<mainBody><p/></mainBody>" if include_main_body else ""
    return DocumentBody(
        f"""<akomaNtoso xmlns="{AKN_NS_URI}">
  <doc name="pressSummary">{main_body}
  </doc>
</akomaNtoso>""".encode()
    )


def akn_child(parent: etree._Element, local_name: str) -> etree._Element:
    child = parent.find(f"{{{AKN_NS}}}{local_name}")
    assert child is not None
    return child


def add_editor_date(document, decision_date: date) -> None:
    document.metadata_fields.add(
        MetadataField(
            name="date",
            value=MetadataDateValue(decision_date),
            source=MetadataSource.EDITOR,
            id=str(uuid4()),
            timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )


def add_editor_title(document, title: str) -> None:
    document.metadata_fields.add(
        MetadataField(
            name="title",
            value=MetadataStringValue(title),
            source=MetadataSource.EDITOR,
            id=str(uuid4()),
            timestamp=datetime(2025, 1, 1, tzinfo=UTC),
        )
    )


def akn_child_local_names(element: etree._Element) -> list[str]:
    return [
        etree.QName(child).localname
        for child in element
        if isinstance(child.tag, str) and etree.QName(child).namespace == AKN_NS
    ]
