import pytest
from lxml import etree

from caselawclient.models.documents.body import DEFAULT_NAMESPACES
from caselawclient.models.documents.xml import XML, NonXMLDocumentError


class TestDocumentXml:
    def test_xml_as_string(self):
        document_xml = XML(b"<xml>content</xml>")

        assert document_xml.xml_as_string == "<xml>content</xml>"

    def test_xml_as_tree(self):
        document_xml = XML(
            b'<?xml version="1.0" encoding="UTF-8"?><xml></xml>',
        )

        assert etree.tostring(document_xml.xml_as_tree) == b"<xml/>"

    def test_root_element_akomantoso(self):
        document_xml = XML(
            b"<akomaNtoso xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn' xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>judgment</akomaNtoso>",
        )

        assert document_xml.root_element == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}akomaNtoso"

    def test_root_element_error(self):
        document_xml = XML(b"<error>parser.log contents</error>")

        assert document_xml.root_element == "error"

    def test_catch_malformed_xml(self):
        with pytest.raises(NonXMLDocumentError):
            XML(b"<error>malformed xml")

    def test_apply_xslt(self):
        document_xml = XML(
            b"""<akomaNtoso xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn' xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>
                <judgment><text>example</text> and <attribute attribute="example"/></judgment></akomaNtoso>"""
        )

        modified_xml = document_xml.apply_xslt("sample.xsl", cat="lion", dog="wolf")
        root = etree.fromstring(modified_xml)
        # XML is correctly namespaced
        assert root.xpath("//akn:text/text()", namespaces=DEFAULT_NAMESPACES) == ["lion"]
        assert root.xpath("//akn:attribute/@attribute", namespaces=DEFAULT_NAMESPACES) == ["wolf"]
        # but text does not contain wierd namespacing artifacts
        assert b"<text>lion</text>" in modified_xml
