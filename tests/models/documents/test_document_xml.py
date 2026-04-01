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

    def test_modify_leaves_okay_namespaces(self):
        document_xml = XML(b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                           <judgment name="decision"> <meta> <identification source="#tna">
                           <FRBRWork> <akn:FRBRthis xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" value="https://caselaw.nationalarchives.gov.uk/id/doc/tn4t35ts"></akn:FRBRthis>
                           </FRBRWork> </identification></meta><header></header><judgmentBody><decision><p>This is a document.</p></decision></judgmentBody></judgment></akomaNtoso>""")
        modified_xml = document_xml.apply_xslt("sample.xsl")
        assert b"<FRBRthis" in modified_xml


class TestXMLMutationHelpers:
    """Tests for XML mutation helper methods: set_xpath_attribute, get_or_create_element, et al."""

    FULL_DOCUMENT_XML = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
    <judgment name="decision">
        <meta>
            <identification>
                <FRBRWork>
                    <FRBRname value="Original Case Name"/>
                    <FRBRdate date="2020-01-01" name="judgment"/>
                </FRBRWork>
            </identification>
            <proprietary>
                <uk:court>Original Court</uk:court>
                <uk:jurisdiction>Original Jurisdiction</uk:jurisdiction>
            </proprietary>
        </meta>
        <header><p>Header</p></header>
        <judgmentBody><decision><p>Content</p></decision></judgmentBody>
    </judgment>
</akomaNtoso>"""

    def test_xml_as_bytes_returns_canonicalized_xml(self):
        """Test that xml_as_bytes returns canonicalized XML bytes."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        result = document_xml.xml_as_bytes

        # Should be bytes
        assert isinstance(result, bytes)

        # Should be parseable XML
        tree = etree.fromstring(result)
        assert tree.tag == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}akomaNtoso"

        # Should be canonicalized (deterministic output)
        result2 = document_xml.xml_as_bytes
        assert result == result2

    def test_set_xpath_attribute_updates_existing_attribute(self):
        """Test that set_xpath_attribute updates an existing attribute value."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"

        document_xml.set_xpath_attribute(xpath, "value", "New Case Name", DEFAULT_NAMESPACES)

        # Verify the attribute was updated
        result = document_xml.get_xpath_match_string(xpath + "/@value", DEFAULT_NAMESPACES)
        assert result == "New Case Name"

    def test_set_xpath_attribute_raises_error_if_element_not_found(self):
        """Test that set_xpath_attribute raises ValueError if element doesn't exist."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:NonExistentElement"

        with pytest.raises(ValueError, match="No element found at xpath"):
            document_xml.set_xpath_attribute(xpath, "value", "test", DEFAULT_NAMESPACES)

    def test_get_or_create_element_returns_existing_element(self):
        """Test that get_or_create_element returns existing child element."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        # Get existing FRBRname element
        result = document_xml.get_or_create_element(parent_xpath, "akn:FRBRname", DEFAULT_NAMESPACES)

        # Should return the existing element
        assert result is not None
        assert result.get("value") == "Original Case Name"

    def test_get_or_create_element_creates_new_element(self):
        """Test that get_or_create_element creates a new element if it doesn't exist."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        # Create a new element that doesn't exist
        result = document_xml.get_or_create_element(parent_xpath, "akn:FRBRcustom", DEFAULT_NAMESPACES)

        # Should return the new element
        assert result is not None
        assert result.tag == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRcustom"

        # Verify it's in the tree
        verify_xpath = parent_xpath + "/akn:FRBRcustom"
        nodes = document_xml.get_xpath_nodes(verify_xpath, DEFAULT_NAMESPACES)
        assert len(nodes) == 1
        assert nodes[0] is result

    def test_get_or_create_element_with_namespace_prefix(self):
        """Test that get_or_create_element correctly handles namespace prefixes."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary"

        # Create element with uk namespace prefix
        result = document_xml.get_or_create_element(parent_xpath, "uk:customElement", DEFAULT_NAMESPACES)

        assert result is not None
        assert result.tag == "{https://caselaw.nationalarchives.gov.uk/akn}customElement"

        # Verify it's in the tree under the correct namespace
        verify_xpath = parent_xpath + "/uk:customElement"
        nodes = document_xml.get_xpath_nodes(verify_xpath, DEFAULT_NAMESPACES)
        assert len(nodes) == 1

    def test_get_or_create_element_raises_error_if_parent_not_found(self):
        """Test that get_or_create_element raises ValueError if parent element doesn't exist."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:NonExistent"

        with pytest.raises(ValueError, match="No parent element found"):
            document_xml.get_or_create_element(parent_xpath, "akn:child", DEFAULT_NAMESPACES)

    def test_set_xpath_element_value_sets_text_on_existing_element(self):
        """Test that set_xpath_element_value sets element text on existing element."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court"

        document_xml.set_xpath_element_value(xpath, "Supreme Court", "uk:court", DEFAULT_NAMESPACES)

        # Verify the value was set
        result = document_xml.get_xpath_match_string(xpath + "/text()", DEFAULT_NAMESPACES)
        assert result == "Supreme Court"

    def test_mutation_persists_in_tree(self):
        """Test that mutations persist in the XML tree and can be retrieved."""
        document_xml = XML(self.FULL_DOCUMENT_XML)

        # Perform multiple mutations
        name_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"
        document_xml.set_xpath_attribute(name_xpath, "value", "Updated Case Name", DEFAULT_NAMESPACES)

        court_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court"
        document_xml.set_xpath_element_value(court_xpath, "New Court", "uk:court", DEFAULT_NAMESPACES)

        # Verify both mutations persisted
        name_result = document_xml.get_xpath_match_string(name_xpath + "/@value", DEFAULT_NAMESPACES)
        court_result = document_xml.get_xpath_match_string(court_xpath + "/text()", DEFAULT_NAMESPACES)

        assert name_result == "Updated Case Name"
        assert court_result == "New Court"

    def test_mutation_reflects_in_serialized_xml(self):
        """Test that mutations reflect in serialized XML output."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"

        document_xml.set_xpath_attribute(xpath, "value", "Updated Title", DEFAULT_NAMESPACES)

        # Get serialized XML
        serialized = document_xml.xml_as_bytes.decode("utf-8")

        # Verify the updated value is in the serialized output
        assert "Updated Title" in serialized
        assert "Original Case Name" not in serialized

    def test_namespace_preservation_in_mutations(self):
        """Test that namespace declarations are preserved after mutations."""
        document_xml = XML(self.FULL_DOCUMENT_XML)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court"

        document_xml.set_xpath_element_value(xpath, "Updated", "uk:court", DEFAULT_NAMESPACES)

        # Serialize and check namespace declarations
        serialized = document_xml.xml_as_bytes.decode("utf-8")

        # Both namespace declarations should still be present
        assert "http://docs.oasis-open.org/legaldocml/ns/akn/3.0" in serialized
        assert "https://caselaw.nationalarchives.gov.uk/akn" in serialized
