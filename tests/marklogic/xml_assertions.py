from lxml import etree

from caselawclient.Client import MarklogicApiClient
from caselawclient.types import DocumentURIString

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
UK_NS = "https://caselaw.nationalarchives.gov.uk/akn"
NAMESPACES = {"akn": AKN_NS, "uk": UK_NS}


def judgment_xml_root(client: MarklogicApiClient, document_uri: DocumentURIString) -> etree._Element:
    xml = client.get_judgment_xml_bytestring(document_uri, show_unpublished=True)
    return etree.fromstring(xml)


def judgment_frbr_name(client: MarklogicApiClient, document_uri: DocumentURIString) -> str:
    root = judgment_xml_root(client, document_uri)
    value = root.xpath("//akn:FRBRWork/akn:FRBRname/@value", namespaces=NAMESPACES)
    return str(value[0]) if value else ""


def judgment_court(client: MarklogicApiClient, document_uri: DocumentURIString) -> str:
    root = judgment_xml_root(client, document_uri)
    value = root.xpath("//uk:court/text()", namespaces=NAMESPACES)
    return str(value[0]) if value else ""


def judgment_work_expression_date(client: MarklogicApiClient, document_uri: DocumentURIString) -> str:
    root = judgment_xml_root(client, document_uri)
    value = root.xpath("//akn:FRBRWork/akn:FRBRdate[@name='judgment']/@date", namespaces=NAMESPACES)
    return str(value[0]) if value else ""
