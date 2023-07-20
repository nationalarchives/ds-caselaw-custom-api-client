import logging
from typing import List, Optional
from xml.etree.ElementTree import (
    Element,
    ElementTree,
    ParseError,
    QName,
    fromstring,
    tostring,
)

akn_uk_namespaces = {
    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
}
akn_namespace_uri = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
uk_namespace_uri = "https://caselaw.nationalarchives.gov.uk/akn"
search_namespace = {"search": "http://marklogic.com/appservices/search"}


class JudgmentMissingMetadataError(IndexError):
    pass


def get_element(
    xml: ElementTree,
    xpath: str,
    element_name: str = "FRBRname",
    element_namespace: str = akn_namespace_uri,
    has_value_attribute: bool = True,
) -> Element:
    logging.warning(
        "XMLTools is deprecated and will be removed in later versions. "
        "Use methods from MarklogicApiClient.Client instead."
    )
    name = xml.find(
        xpath,
        namespaces=akn_uk_namespaces,
    )

    if name is None:
        element = Element(QName(element_namespace, element_name))  # type: ignore
        if has_value_attribute:
            element.set("value", "")
        return element

    return name


def get_neutral_citation_element(xml: ElementTree) -> Element:
    return get_element(xml, ".//uk:cite", "cite", uk_namespace_uri, False)


def get_neutral_citation_name_value(xml: ElementTree) -> Optional[str]:
    return get_neutral_citation_element(xml).text


def get_judgment_date_element(xml: ElementTree) -> Element:
    logging.warning(
        "XMLTools is deprecated and will be removed in later versions. "
        "Use methods from MarklogicApiClient.Client instead."
    )
    name = xml.find(
        ".//akn:FRBRWork/akn:FRBRdate",
        namespaces=akn_uk_namespaces,
    )

    if name is None:
        element = Element(QName(akn_namespace_uri, "FRBRdate"))  # type: ignore
        element.set("date", "")
        element.set("name", "judgment")

        return element

    return name


def get_judgment_date_value(xml: ElementTree) -> str:
    return get_judgment_date_element(xml).attrib["date"]


def get_court_element(xml: ElementTree) -> Element:
    return get_element(xml, ".//uk:court", "court", uk_namespace_uri, False)


def get_court_value(xml: ElementTree) -> Optional[str]:
    return get_court_element(xml).text


def get_metadata_name_element(xml: ElementTree) -> Element:
    return get_element(xml, ".//akn:FRBRname", "FRBRname", akn_namespace_uri, True)


def get_metadata_name_value(xml: ElementTree) -> str:
    name = get_metadata_name_element(xml)
    value = name.attrib["value"]
    if value is None:
        return ""
    return value


def get_search_matches(element: ElementTree) -> List[str]:
    logging.warning(
        "XMLTools is deprecated and will be removed in later versions. "
        "Use methods from MarklogicApiClient.Client instead."
    )
    nodes = element.findall(".//search:match", namespaces=search_namespace)
    results = []
    for node in nodes:
        text = tostring(node, method="text", encoding="UTF-8")
        results.append(text.decode("UTF-8").strip())
    return results


def get_error_code(content_as_xml: Optional[str]) -> str:
    logging.warning(
        "XMLTools is deprecated and will be removed in later versions. "
        "Use methods from MarklogicApiClient.Client instead."
    )
    if not content_as_xml:
        return "Unknown error, Marklogic returned a null or empty response"
    try:
        xml = fromstring(content_as_xml)
        return xml.find(
            "message-code", namespaces={"": "http://marklogic.com/xdmp/error"}
        ).text  # type: ignore
    except (ParseError, TypeError, AttributeError):
        return "Unknown error, Marklogic returned a null or empty response"
