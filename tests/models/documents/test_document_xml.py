import os

import pytest
from lxml import etree

from caselawclient.models.documents.body_metadata.akn import FRBR_WORK_CHILDREN_ORDER
from caselawclient.models.documents.xml import (
    AKN_META_CHILDREN_ORDER,
    XML,
    NonXMLDocumentError,
    _local_name_in_namespace,
)
from caselawclient.xml_helpers import DEFAULT_NAMESPACES, Element

AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
META_XPATH = "/akn:akomaNtoso/akn:judgment/akn:meta"


@pytest.fixture
def full_document_xml():
    """Load the test document XML from file."""
    test_file_path = os.path.join(os.path.dirname(__file__), "xslt", "test_standard_judgment.xml")
    with open(test_file_path, "rb") as f:
        return f.read()


class TestDocumentXMLRepresentationMethods:
    def test_xml_as_string(self):
        document_xml = XML(b"<xml>content</xml>")

        assert document_xml.xml_as_string == "<xml>content</xml>"

    def test_xml_as_tree(self):
        document_xml = XML(
            b'<?xml version="1.0" encoding="UTF-8"?><xml></xml>',
        )

        assert etree.tostring(document_xml.xml_as_tree) == b"<xml/>"


class TestDocumentXMLRootCheckingMethods:
    def test_root_element_akomantoso(self):
        document_xml = XML(
            b"<akomaNtoso xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn' xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>judgment</akomaNtoso>",
        )

        assert document_xml.root_element == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}akomaNtoso"

    def test_root_element_error(self):
        document_xml = XML(b"<error>parser.log contents</error>")

        assert document_xml.root_element == "error"


class TestDocumentXMLValidationMethods:
    def test_catch_malformed_xml(self):
        with pytest.raises(NonXMLDocumentError):
            XML(b"<error>malformed xml")


class TestDocumentXMLXSLTMethods:
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

    def test_applying_xslt_leaves_correct_namespaces(self):
        document_xml = XML(b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                           <judgment name="decision"> <meta> <identification source="#tna">
                           <FRBRWork> <akn:FRBRthis xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" value="https://caselaw.nationalarchives.gov.uk/id/doc/tn4t35ts"></akn:FRBRthis>
                           </FRBRWork> </identification></meta><header></header><judgmentBody><decision><p>This is a document.</p></decision></judgmentBody></judgment></akomaNtoso>""")
        modified_xml = document_xml.apply_xslt("sample.xsl")
        assert b"<FRBRthis" in modified_xml


class TestDocumentXMLXPathMethods:
    def test_get_xpath_match_strings_returns_all_matches(self):
        document_xml = XML(
            b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment>
                <meta>
                    <identification>
                        <FRBRWork>
                            <FRBRdate date="2020-01-01" name="judgment"/>
                            <FRBRdate date="2021-01-01" name="transform"/>
                        </FRBRWork>
                    </identification>
                </meta>
            </judgment>
        </akomaNtoso>"""
        )
        dates = document_xml.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date"
        )
        assert dates == ["2020-01-01", "2021-01-01"]

    def test_get_xpath_nodes_returns_empty_for_nonexistent_element(self, full_document_xml):
        """Test that get_xpath_nodes returns empty list for non-existent elements."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:NonExistentElement"

        nodes = document_xml.get_xpath_nodes(xpath)
        assert len(nodes) == 0

    def test_get_xpath_nodes_detects_multiple_matches(self):
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

    def test_get_single_xpath_node_returns_element(self, full_document_xml):
        """Test that get_single_xpath_node returns an Element."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"

        node = document_xml.get_single_xpath_node(xpath)
        assert isinstance(node, Element)

    def test_get_single_xpath_node_raises_error_on_empty_result(self, full_document_xml):
        """Test that get_xpath_nodes returns empty list for non-existent elements."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:NonExistentElement"

        with pytest.raises(
            ValueError,
            match="No element found at xpath: /akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:NonExistentElement",
        ):
            document_xml.get_single_xpath_node(xpath)

    def test_get_single_xpath_node_raises_error_on_multiple_results(self):
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

        with pytest.raises(
            ValueError,
            match="XPath expression matches 3 elements, expected exactly 1: /akn:akomaNtoso/akn:judgment/akn:p",
        ):
            document_xml.get_single_xpath_node(xpath)


class TestDocumentXMLElementSetters:
    def test_set_element_attribute_updates_existing_attribute(self, full_document_xml):
        """Test that set_element_attribute updates an existing attribute value."""
        document_xml = XML(full_document_xml)
        xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname"
        node = document_xml.get_single_xpath_node(xpath)

        document_xml.set_element_attribute(node, "value", "New Case Name")

        # Verify the attribute was updated
        result = document_xml.get_xpath_match_string(xpath + "/@value")
        assert result == "New Case Name"

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
        assert result.get("value") == "Test Claimant v TestDefendant"

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
        node = document_xml.get_single_xpath_node(verify_xpath)
        assert node is result

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
        node = document_xml.get_single_xpath_node(verify_xpath)
        assert node is result

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
        node = document_xml.get_single_xpath_node(xpath)

        document_xml.set_element_value(node, "Supreme Court")

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

    def test_get_or_create_element_without_namespace(self):
        document_xml = XML(b"<root><parent><existing/></parent></root>")
        parent_xpath = "/root/parent"
        created = document_xml.get_or_create_element(parent_xpath, "newChild")
        assert created.tag == "newChild"
        assert document_xml.get_single_xpath_node("/root/parent/newChild") is created


class TestLocalNameInNamespace:
    def test_returns_local_name_for_matching_namespace(self):
        element = etree.Element(etree.QName(AKN_NS, "proprietary"))
        assert _local_name_in_namespace(element, AKN_NS) == "proprietary"

    def test_returns_none_for_different_namespace(self):
        element = etree.Element(etree.QName("https://caselaw.nationalarchives.gov.uk/akn", "court"))
        assert _local_name_in_namespace(element, AKN_NS) is None

    def test_returns_none_for_unqualified_tag(self):
        element = etree.Element("plain")
        assert _local_name_in_namespace(element, AKN_NS) is None


class TestGetOrCreateElementInChildOrder:
    def test_returns_existing_element(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification/>
                        <proprietary/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        existing = document_xml.get_single_xpath_node(f"{META_XPATH}/akn:proprietary")
        result = document_xml.get_or_create_element_in_child_order(
            META_XPATH, "proprietary", AKN_NS, AKN_META_CHILDREN_ORDER
        )
        assert result is existing

    def test_inserts_before_later_schema_sibling(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:html="http://www.w3.org/1999/xhtml">
                <judgment>
                    <meta>
                        <identification/>
                        <unknownMeta/>
                        <html:foreign/>
                        <presentation><html:style/></presentation>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        proprietary = document_xml.get_or_create_element_in_child_order(
            META_XPATH, "proprietary", AKN_NS, AKN_META_CHILDREN_ORDER
        )
        meta = document_xml.get_single_xpath_node(META_XPATH)
        child_tags = [etree.QName(child).localname for child in meta]
        assert child_tags.index("proprietary") < child_tags.index("presentation")
        assert proprietary.tag == f"{{{AKN_NS}}}proprietary"

    def test_inserts_publication_before_lifecycle(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification/>
                        <lifecycle/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        document_xml.get_or_create_element_in_child_order(META_XPATH, "publication", AKN_NS, AKN_META_CHILDREN_ORDER)
        meta = document_xml.get_single_xpath_node(META_XPATH)
        child_tags = [etree.QName(child).localname for child in meta]
        assert child_tags.index("publication") < child_tags.index("lifecycle")

    def test_inserts_lifecycle_before_workflow(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification/>
                        <workflow/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        document_xml.get_or_create_element_in_child_order(META_XPATH, "lifecycle", AKN_NS, AKN_META_CHILDREN_ORDER)
        meta = document_xml.get_single_xpath_node(META_XPATH)
        child_tags = [etree.QName(child).localname for child in meta]
        assert child_tags.index("lifecycle") < child_tags.index("workflow")

    def test_inserts_proprietary_after_analysis(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification/>
                        <analysis/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        document_xml.get_or_create_element_in_child_order(META_XPATH, "proprietary", AKN_NS, AKN_META_CHILDREN_ORDER)
        meta = document_xml.get_single_xpath_node(META_XPATH)
        child_tags = [etree.QName(child).localname for child in meta]
        assert child_tags.index("analysis") < child_tags.index("proprietary")

    def test_insert_element_in_child_order_allows_repeatable_siblings(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="2025-07-29" name="transform"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        work_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"
        new_date = document_xml.insert_element_in_child_order(work_xpath, "FRBRdate", AKN_NS, FRBR_WORK_CHILDREN_ORDER)
        new_date.set("date", "2024-01-01")
        new_date.set("name", "judgment")
        dates = document_xml.get_xpath_match_strings(f"{work_xpath}/akn:FRBRdate/@name")
        assert sorted(dates) == ["judgment", "transform"]
        assert new_date.get("name") == "judgment"

    def test_inserts_frbrname_before_prescriptive(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRthis value=""/>
                                <FRBRuri value=""/>
                                <FRBRdate date="2020-01-01" name="judgment"/>
                                <FRBRauthor href="#court"/>
                                <FRBRcountry value="GB"/>
                                <FRBRprescriptive value="prescriptive-id"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        work_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:identification/akn:FRBRWork"
        name_element = document_xml.get_or_create_element_in_child_order(
            work_xpath, "FRBRname", AKN_NS, FRBR_WORK_CHILDREN_ORDER
        )
        name_element.set("value", "Title")
        work = document_xml.get_single_xpath_node(work_xpath)
        child_tags = [etree.QName(child).localname for child in work]
        assert child_tags.index("FRBRname") < child_tags.index("FRBRprescriptive")

    def test_appends_when_no_later_schema_siblings(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        document_xml.get_or_create_element_in_child_order(META_XPATH, "proprietary", AKN_NS, AKN_META_CHILDREN_ORDER)
        meta = document_xml.get_single_xpath_node(META_XPATH)
        assert etree.QName(meta[-1]).localname == "proprietary"

    def test_raises_for_invalid_namespace(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta/></judgment>
            </akomaNtoso>
            """
        )
        with pytest.raises(ValueError, match="Namespace not in DEFAULT_NAMESPACES"):
            document_xml.get_or_create_element_in_child_order(
                META_XPATH, "proprietary", "http://invalid.example/ns", AKN_META_CHILDREN_ORDER
            )

    def test_insert_raises_for_invalid_namespace(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta/></judgment>
            </akomaNtoso>
            """
        )
        with pytest.raises(ValueError, match="Namespace not in DEFAULT_NAMESPACES"):
            document_xml.insert_element_in_child_order(
                META_XPATH, "proprietary", "http://invalid.example/ns", AKN_META_CHILDREN_ORDER
            )

    def test_raises_when_element_not_in_child_order(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta/></judgment>
            </akomaNtoso>
            """
        )
        with pytest.raises(ValueError, match="not listed in child_order"):
            document_xml.get_or_create_element_in_child_order(META_XPATH, "unknown", AKN_NS, AKN_META_CHILDREN_ORDER)

    def test_insert_raises_when_element_not_in_child_order(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta/></judgment>
            </akomaNtoso>
            """
        )
        with pytest.raises(ValueError, match="not listed in child_order"):
            document_xml.insert_element_in_child_order(META_XPATH, "unknown", AKN_NS, AKN_META_CHILDREN_ORDER)

    def test_raises_when_duplicate_children_exist(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <proprietary/>
                        <proprietary/>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        with pytest.raises(ValueError, match="Multiple child elements with name proprietary"):
            document_xml.get_or_create_element_in_child_order(
                META_XPATH, "proprietary", AKN_NS, AKN_META_CHILDREN_ORDER
            )


class TestReplaceChildElements:
    UK_NS = "https://caselaw.nationalarchives.gov.uk/akn"

    def test_replaces_all_matching_children(self):
        document_xml = XML(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:court>Old</uk:court>
                        </proprietary>
                    </meta>
                </judgment>
            </akomaNtoso>
            """
        )
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary"
        replacement = etree.Element(etree.QName(self.UK_NS, "court"))
        replacement.text = "New"
        document_xml.replace_child_elements(parent_xpath, "court", self.UK_NS, [replacement])
        assert document_xml.get_xpath_match_string(f"{parent_xpath}/uk:court/text()") == "New"

    def test_raises_for_invalid_namespace(self, full_document_xml):
        document_xml = XML(full_document_xml)
        parent_xpath = "/akn:akomaNtoso/akn:judgment/akn:meta/akn:proprietary"
        with pytest.raises(ValueError, match="Namespace not in DEFAULT_NAMESPACES"):
            document_xml.replace_child_elements(parent_xpath, "court", "http://invalid.example/ns", [])
