import os

import pytest
from lxml import etree

from caselawclient.models.documents.body import DEFAULT_NAMESPACES
from caselawclient.models.documents.xml import XML, NonXMLDocumentError


@pytest.fixture
def full_document_xml():
    """Load the test document XML from file."""
    test_file_path = os.path.join(os.path.dirname(__file__), "xslt", "test_standard_judgment.xml")
    with open(test_file_path, "rb") as f:
        return f.read()


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

    def test_set_element_attribute_updates_existing_attribute(self, full_document_xml):
        """Test that set_element_attribute updates an existing attribute value."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"
        nodes = document_xml.get_xpath_nodes(xpath)
        assert len(nodes) == 1

        document_xml.set_element_attribute(nodes[0], "value", "New Case Name")

        # Verify the attribute was updated
        result = document_xml.get_xpath_match_string(xpath + "/@value")
        assert result == "New Case Name"

    def test_get_xpath_nodes_returns_empty_for_nonexistent_element(self, full_document_xml):
        """Test that get_xpath_nodes returns empty list for non-existent elements."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:NonExistentElement"

        nodes = document_xml.get_xpath_nodes(xpath)
        assert len(nodes) == 0

    def test_set_element_attribute_detects_multiple_matches(self):
        """Test that get_xpath_nodes can return multiple elements."""
        # Create XML with multiple matching elements
        multi_match_xml = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment>
                <p>First</p>
                <p>Second</p>
                <p>Third</p>
            </judgment>
        </akomaNtoso>"""
        document_xml = XML(multi_match_xml)
        # XPath that matches multiple <p> elements
        xpath = "/akn:akomaNtoso/akn:judgment/akn:p"

        nodes = document_xml.get_xpath_nodes(xpath)
        assert len(nodes) == 3
        # Caller must validate before using set_element_attribute
        assert len(nodes) > 1

    def test_get_or_create_element_returns_existing_element(self, full_document_xml):
        """Test that get_or_create_element returns existing child element."""
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        # Get existing FRBRname element
        result = document_xml.get_or_create_element(
            parent_xpath, "FRBRname", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        )

        # Should return the existing element with its current value
        assert result is not None
        assert result.get("value") is not None

    def test_get_or_create_element_creates_new_element(self, full_document_xml):
        """Test that get_or_create_element creates a new element if it doesn't exist."""
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        # Create a new element that doesn't exist
        result = document_xml.get_or_create_element(
            parent_xpath, "FRBRcustom", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        )

        # Should return the new element
        assert result is not None
        assert result.tag == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRcustom"

        # Verify it's in the tree
        verify_xpath = parent_xpath + "/akn:FRBRcustom"
        nodes = document_xml.get_xpath_nodes(verify_xpath)
        assert len(nodes) == 1
        assert nodes[0] is result

    def test_get_or_create_element_with_namespace_prefix(self, full_document_xml):
        """Test that get_or_create_element correctly handles namespace URIs."""
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary"

        # Create element with explicit uk namespace
        result = document_xml.get_or_create_element(
            parent_xpath, "customElement", "https://caselaw.nationalarchives.gov.uk/akn"
        )

        assert result is not None
        assert result.tag == "{https://caselaw.nationalarchives.gov.uk/akn}customElement"

        # Verify it's in the tree under the correct namespace
        verify_xpath = parent_xpath + "/uk:customElement"
        nodes = document_xml.get_xpath_nodes(verify_xpath)
        assert len(nodes) == 1

    def test_get_or_create_element_raises_error_if_parent_not_found(self, full_document_xml):
        """Test that get_or_create_element raises ValueError if parent element doesn't exist."""
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:NonExistent"

        with pytest.raises(ValueError, match="No parent element found"):
            document_xml.get_or_create_element(
                parent_xpath, "child", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            )

    def test_get_or_create_element_raises_error_if_multiple_parents_match(self):
        """Test that get_or_create_element raises ValueError if XPath matches multiple parent elements."""
        # Create XML with multiple matching parent elements
        multi_parent_xml = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment>
                <section><p>First</p></section>
                <section><p>Second</p></section>
                <section><p>Third</p></section>
            </judgment>
        </akomaNtoso>"""
        document_xml = XML(multi_parent_xml)
        # XPath that matches multiple <section> elements
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:section"

        with pytest.raises(ValueError, match="XPath expression matches 3 parent elements, expected exactly 1"):
            document_xml.get_or_create_element(
                parent_xpath, "child", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            )

    def test_get_or_create_element_raises_error_if_invalid_namespace(self, full_document_xml):
        """Test that get_or_create_element raises ValueError if namespace is not in DEFAULT_NAMESPACES."""
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        with pytest.raises(ValueError, match="Namespace not in DEFAULT_NAMESPACES"):
            document_xml.get_or_create_element(parent_xpath, "child", "http://invalid.namespace.org/")

    def test_get_or_create_element_raises_error_if_duplicate_children_exist(self):
        """Test that get_or_create_element raises ValueError if multiple children with same name already exist."""
        # Create XML with duplicate children
        duplicate_children_xml = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment>
                <meta>
                    <identification>
                        <FRBRWork>
                            <FRBRname value="first"/>
                            <FRBRname value="second"/>
                        </FRBRWork>
                    </identification>
                </meta>
            </judgment>
        </akomaNtoso>"""
        document_xml = XML(duplicate_children_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"

        with pytest.raises(ValueError, match="Multiple child elements with name FRBRname already exist"):
            document_xml.get_or_create_element(
                parent_xpath, "FRBRname", "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            )

    def test_set_element_value_sets_text_on_existing_element(self, full_document_xml):
        """Test that set_element_value sets element text on existing element."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court"
        nodes = document_xml.get_xpath_nodes(xpath)
        assert len(nodes) == 1

        document_xml.set_element_value(nodes[0], "Supreme Court")

        # Verify the value was set
        result = document_xml.get_xpath_match_string(xpath + "/text()")
        assert result == "Supreme Court"

    def test_mutation_persists_in_tree(self, full_document_xml):
        """Test that mutations persist in the XML tree and can be retrieved."""
        document_xml = XML(full_document_xml)

        # Perform multiple mutations
        name_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"
        name_nodes = document_xml.get_xpath_nodes(name_xpath)
        assert len(name_nodes) == 1
        document_xml.set_element_attribute(name_nodes[0], "value", "Updated Case Name")

        court_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary/uk:court"
        court_nodes = document_xml.get_xpath_nodes(court_xpath)
        assert len(court_nodes) == 1
        document_xml.set_element_value(court_nodes[0], "New Court")

        # Verify both mutations persisted by re-querying
        assert document_xml.get_xpath_match_string(name_xpath + "/@value") == "Updated Case Name"
        assert document_xml.get_xpath_match_string(court_xpath + "/text()") == "New Court"
