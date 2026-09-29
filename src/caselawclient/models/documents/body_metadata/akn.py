"""Shared Akoma Ntoso constants and helpers for body metadata writers."""

from caselawclient.xml_helpers import DEFAULT_NAMESPACES

from ..xml import XML

AKN_NS = DEFAULT_NAMESPACES["akn"]
META_XPATH = "/akn:akomaNtoso/akn:*/akn:meta"
IDENTIFICATION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification"
JUDGMENT_ROOT_XPATH = "/akn:akomaNtoso/akn:judgment"
DOC_ROOT_XPATH = "/akn:akomaNtoso/akn:doc"
JUDGMENT_NAME_XPATH = "/akn:akomaNtoso/akn:*/@name"
FRBR_WORK_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork"
FRBR_EXPRESSION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression"
FRBR_MANIFESTATION_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRManifestation"

IDENTIFICATION_CHILDREN_ORDER = (
    "FRBRWork",
    "FRBRExpression",
    "FRBRManifestation",
)
FRBR_WORK_CHILDREN_ORDER = (
    "FRBRthis",
    "FRBRuri",
    "FRBRalias",
    "FRBRdate",
    "FRBRauthor",
    "componentInfo",
    "preservation",
    "FRBRcountry",
    "FRBRsubtype",
    "FRBRnumber",
    "FRBRname",
    "FRBRprescriptive",
    "FRBRauthoritative",
)
CORE_FRBR_CHILDREN_ORDER = (
    "FRBRthis",
    "FRBRuri",
    "FRBRalias",
    "FRBRdate",
    "FRBRauthor",
    "componentInfo",
    "preservation",
)
FRBR_EXPRESSION_CHILDREN_ORDER = CORE_FRBR_CHILDREN_ORDER + ("FRBRlanguage",)
FRBR_MANIFESTATION_CHILDREN_ORDER = CORE_FRBR_CHILDREN_ORDER + ("FRBRformat",)

JUDGMENT_ROOT_CHILDREN_ORDER = (
    "meta",
    "coverPage",
    "preface",
    "preamble",
    "formula",
    "header",
    "judgmentBody",
    "conclusions",
    "attachments",
    "components",
)
DOC_ROOT_CHILDREN_ORDER = (
    "meta",
    "coverPage",
    "preface",
    "preamble",
    "mainBody",
    "conclusions",
    "attachments",
    "components",
)

DECISION_FRBRDATE_NAMES = frozenset({"judgment", "decision"})
IDENTIFICATION_SOURCE = "#tna"
FCL_BASE = "https://caselaw.nationalarchives.gov.uk"


def writable_akn_document_root_xpath(xml: XML) -> str | None:
    judgment_nodes = xml.get_xpath_nodes(JUDGMENT_ROOT_XPATH)
    doc_nodes = xml.get_xpath_nodes(DOC_ROOT_XPATH)
    if len(judgment_nodes) > 1 or len(doc_nodes) > 1 or (judgment_nodes and doc_nodes):
        return None
    if judgment_nodes:
        return JUDGMENT_ROOT_XPATH
    if doc_nodes:
        return DOC_ROOT_XPATH
    return None
