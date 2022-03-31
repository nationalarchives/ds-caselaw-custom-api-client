from xml.etree import ElementTree
from xml.etree.ElementTree import Element

akn_namespace = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"}
search_namespace = {"search": "http://marklogic.com/appservices/search"}


class JudgmentMissingMetadataError(IndexError):
    pass


def get_metadata_name_value(xml: ElementTree) -> str:
    name = get_metadata_name_element(xml)
    return name.attrib["value"]


def get_metadata_name_element(xml: ElementTree) -> Element:
    name = xml.find(
        ".//akn:FRBRname",
        namespaces=akn_namespace,
    )

    if name is None:
        raise JudgmentMissingMetadataError

    return name


def get_search_matches(element: ElementTree) -> [str]:
    nodes = element.findall(".//search:match", namespaces=search_namespace)
    results = []
    for node in nodes:
        text = ElementTree.tostring(node, method="text", encoding="UTF-8")
        results.append(text.decode("UTF-8").strip())
    return results
