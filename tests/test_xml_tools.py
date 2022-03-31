import unittest
import xml.etree.ElementTree as ET

import src.caselawclient.xml_tools as xml_tools
from src.caselawclient.xml_tools import JudgmentMissingMetadataError


class XmlToolsTests(unittest.TestCase):
    def test_metadata_name_value_success(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRname value="My Judgment Name"/>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = ET.ElementTree(ET.fromstring(xml_string))
        result = xml_tools.get_metadata_name_value(xml)
        self.assertEqual(result, "My Judgment Name")

    def test_neutral_citation_name_value_success(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_neutral_citation_name_value(xml)
        self.assertEqual(result, "[2022] EWHC 482 (QB)")

    def test_neutral_citation_name_value_failure(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_neutral_citation_name_value, xml
        )

    def test_neutral_citation_element_success(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_neutral_citation_element(xml)
        self.assertEqual(
            result.tag, "{https://caselaw.nationalarchives.gov.uk/akn}cite"
        )
        self.assertEqual(result.text, "[2022] EWHC 482 (QB)")

    def test_neutral_citation_element_failure(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_neutral_citation_element, xml
        )

    def test_metadata_name_value_failure(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna"/>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = ET.ElementTree(ET.fromstring(xml_string))
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_metadata_name_value, xml
        )

    def test_metadata_name_element_success(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRname value="My Judgment Name"/>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = ET.ElementTree(ET.fromstring(xml_string))
        result = xml_tools.get_metadata_name_element(xml)
        self.assertEqual(
            result.tag, "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRname"
        )
        self.assertEqual(result.attrib, {"value": "My Judgment Name"})

    def test_metadata_name_element_failure(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna"/>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = ET.ElementTree(ET.fromstring(xml_string))
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_metadata_name_element, xml
        )

    def test_judgment_date_value_success(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRWork>
                                <FRBRdate date="2022-03-10" name="judgment"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_judgment_date_value(xml)
        self.assertEqual(result, "2022-03-10")

    def test_judgment_date_value_failure(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRWork>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_metadata_name_value, xml
        )

    def test_judgment_date_element_success(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRWork>
                                <FRBRdate date="2022-03-10" name="judgment"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_judgment_date_element(xml)
        self.assertEqual(
            result.tag, "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRdate"
        )
        self.assertEqual(result.attrib, {"date": "2022-03-10", "name": "judgment"})

    def test_judgment_date_element_failure(self):
        xml_string = """
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment" contains="originalVersion">
                    <meta>
                        <identification source="#tna">
                            <FRBRWork>
                            </FRBRWork>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_judgment_date_element, xml
        )

    def test_court_value_success(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_court_value(xml)
        self.assertEqual(result, "EWHC-QBD")

    def test_court_value_failure(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_court_value, xml
        )

    def test_court_element_success(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:court>EWHC-QBD</uk:court>
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        result = xml_tools.get_court_element(xml)
        self.assertEqual(
            result.tag, "{https://caselaw.nationalarchives.gov.uk/akn}court"
        )
        self.assertEqual(result.text, "EWHC-QBD")

    def test_court_element_failure(self):
        xml_string = """
            <proprietary source="#" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <uk:year>2022</uk:year>
                <uk:number>482</uk:number>
                <uk:cite>[2022] EWHC 482 (QB)</uk:cite>
                <uk:parser>0.3.1</uk:parser>
                <uk:hash>39c1eb4656a3a382a9b6f5627a07d9069048c91eec20ee13c724e16738a89bd2</uk:hash>
            </proprietary>
        """
        xml = etree.fromstring(xml_string)
        self.assertRaises(
            JudgmentMissingMetadataError, xml_tools.get_court_element, xml
        )

    def test_search_matches(self):
        xml_string = """
            <search:result index="11" xmlns:search="http://marklogic.com/appservices/search"
                uri="/ewhc/admin/2013/2575.xml"
                path="fn:doc('/ewhc/admin/2013/2575.xml')"
                href="/v1/documents?uri=%2Fewhc%2Fadmin%2F2013%2F2575.xml"
                mimetype="application/xml"
                format="xml">
                <search:snippet>
                    <search:match
                        path="fn:doc('/ewhc/admin/2013/2575.xml')/*:akomaNtoso/*:judgment/*:header/*:p[9]/*:span">
                        HH <search:highlight>Judge</search:highlight> Anthony Thornton QC
                    </search:match>
                </search:snippet>
            </search:result>
        """
        xml = ET.ElementTree(ET.fromstring(xml_string))
        result = xml_tools.get_search_matches(xml)
        self.assertEqual(result, ["HH Judge Anthony Thornton QC"])
