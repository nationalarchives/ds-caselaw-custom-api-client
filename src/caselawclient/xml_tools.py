from xml.etree import ElementTree
from xml.etree.ElementTree import Element

akn_uk_namespaces = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
                     "uk": "https://caselaw.nationalarchives.gov.uk/akn"}
search_namespace = {"search": "http://marklogic.com/appservices/search"}


class JudgmentMissingMetadataError(IndexError):
    pass


def get_metadata_name_value(xml: ElementTree) -> str:
    name = get_metadata_name_element(xml)
    return name.attrib["value"]


def get_element(xml: ElementTree, xpath) -> Element:
    name = xml.find(
        xpath,
        namespaces=akn_uk_namespaces,
    )

    if name is None:
        raise JudgmentMissingMetadataError

    return name


def get_neutral_citation_name_value(xml) -> str:
    return get_neutral_citation_element(xml).text


def get_judgment_date_value(xml) -> str:
    return get_judgment_date_element(xml).attrib["date"]


def get_court_value(xml) -> str:
    return get_court_element(xml).text


def get_metadata_name_element(xml) -> Element:
    return get_element(xml, ".//akn:FRBRname")


def get_neutral_citation_element(xml) -> Element:
    return get_element(xml, ".//uk:cite")


def get_judgment_date_element(xml) -> Element:
    return get_element(xml, ".//akn:FRBRWork/akn:FRBRdate")


def get_court_element(xml) -> Element:
    return get_element(xml, ".//uk:court")


def get_search_matches(element: ElementTree) -> [str]:
    nodes = element.findall(".//search:match", namespaces=search_namespace)
    results = []
    for node in nodes:
        text = ElementTree.tostring(node, method="text", encoding="UTF-8")
        results.append(text.decode("UTF-8").strip())
    return results
