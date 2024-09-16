import pytest
from lxml import etree

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
