from xml.etree import ElementTree
from xml.etree.ElementTree import Element

akn_uk_namespaces = {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
                     "uk": "https://caselaw.nationalarchives.gov.uk/akn"}
akn_namespace_uri = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
uk_namespace_uri = "https://caselaw.nationalarchives.gov.uk/akn"
search_namespace = {"search": "http://marklogic.com/appservices/search"}


class JudgmentMissingMetadataError(IndexError):
    pass


def get_metadata_name_value(xml: ElementTree) -> str:
    name = get_metadata_name_element(xml)
    value = name.attrib["value"]
    if value is None:
        return ""
    return value


def get_element(xml: ElementTree, xpath, element_name="FRBRname", element_namespace=akn_namespace_uri, has_value_attribute=True) -> Element:
    name = xml.find(
        xpath,
        namespaces=akn_uk_namespaces,
    )

    if name is None:
        element = ElementTree.Element(ElementTree.QName(element_namespace, element_name))
        if has_value_attribute:
            element.set("value", "")
        return element

    return name


def get_neutral_citation_name_value(xml) -> str:
    return get_neutral_citation_element(xml).text


def get_judgment_date_value(xml) -> str:
    return get_judgment_date_element(xml).attrib["date"]


def get_court_value(xml) -> str:
    return get_court_element(xml).text


def get_metadata_name_element(xml) -> Element:
    return get_element(xml, ".//akn:FRBRname", "FRBRname", akn_namespace_uri, True)


def get_neutral_citation_element(xml) -> Element:
    return get_element(xml, ".//uk:cite", "cite", uk_namespace_uri, False)


def get_judgment_date_element(xml) -> Element:
    name = xml.find(
        ".//akn:FRBRWork/akn:FRBRdate",
        namespaces=akn_uk_namespaces,
    )

    if name is None:
        element = ElementTree.Element(ElementTree.QName(akn_namespace_uri, "FRBRdate"))
        element.set("date", "")
        element.set("name", "judgment")

        return element

    return name


def get_court_element(xml) -> Element:
    return get_element(xml, ".//uk:court", "court", uk_namespace_uri, False)


def get_search_matches(element: ElementTree) -> [str]:
    nodes = element.findall(".//search:match", namespaces=search_namespace)
    results = []
    for node in nodes:
        text = ElementTree.tostring(node, method="text", encoding="UTF-8")
        results.append(text.decode("UTF-8").strip())
    return results


def get_error_code(xml_content: str) -> str:
    xml = ElementTree.fromstring(xml_content)
    return xml.find('message-code', namespaces={"": "http://marklogic.com/xdmp/error"}).text
