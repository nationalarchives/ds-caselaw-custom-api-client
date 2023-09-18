import datetime
from unittest.mock import patch

import pytest
from ds_caselaw_utils.courts import Court
from lxml import etree

from caselawclient.responses.search_result import (
    EditorPriority,
    EditorStatus,
    SearchResult,
    SearchResultMetadata,
)


class TestSearchResult:
    @patch("caselawclient.responses.search_result.api_client")
    def test_init(self, mock_api_client, valid_search_result_xml):
        """
        GIVEN a valid search result XML and a mock API client
        WHEN initializing a SearchResult object
        THEN the attributes are set correctly
        """
        mock_api_client.get_properties_for_search_results.return_value = "<foo/>"
        mock_api_client.get_last_modified.return_value = "bar"

        node = etree.fromstring(valid_search_result_xml)
        search_result = SearchResult(node)

        assert search_result.uri == "a/c/2015/20"
        assert search_result.neutral_citation == "[2015] A 20 (C)"
        assert search_result.name == "Another made up case name"
        assert search_result.date == datetime.datetime(2017, 8, 8, 0, 0)
        assert search_result.court is None
        assert search_result.matches == (
            "<p data-path=\"fn:doc('/a/c/2015/20.xml')/*:akomaNtoso\">"
            "text from the document that matched the search</p>\n"
        )
        assert search_result.content_hash == "test_content_hash"
        assert search_result.transformation_date == "2023-04-09T18:05:45"
        assert etree.tostring(search_result.metadata.node).decode() == "<foo/>"
        assert search_result.metadata.last_modified == "bar"

    def test_create_from_node_with_unparsable_date(self):
        """
        GIVEN an XML node with an unparsable date
        WHEN creating a SearchResult object from the node
        THEN the date attribute is set to None
        """
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/a/c/2015/20.xml">\n '
            '<search:extracted kind="element">'
            '<FRBRdate date="blah" name="judgment" xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"/>'
            "</search:extracted>"
            "</search:result>"
        )
        node = etree.fromstring(xml)
        search_result = SearchResult(node)

        assert search_result.date is None

    def test_create_from_node_with_valid_court_code(self):
        """
        GIVEN an XML node with a valid court code
        WHEN creating a SearchResult object from the node
        THEN the court attribute is set to the corresponding Court object
        """
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" uri="/uksc/2015/20.xml">\n '
            '<search:extracted kind="element">'
            '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">UKSC</uk:court>'
            "</search:extracted>"
            "</search:result>"
        )
        node = etree.fromstring(xml)
        search_result = SearchResult(node)

        assert isinstance(search_result.court, Court)
        assert search_result.court.name == "United Kingdom Supreme Court"

    def test_create_from_node_with_invalid_court_code(self):
        """
        GIVEN an XML node with an invalid court code
        WHEN creating a SearchResult object from the node
        THEN the court attribute is set to None
        """
        xml = (
            '<search:result xmlns:search="http://marklogic.com/appservices/search" index="2" uri="/a/c/2015/20.xml">\n '
            '<search:extracted kind="element">'
            '<uk:court xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">A-C</uk:court>'
            "</search:extracted>"
            "</search:result>"
        )
        node = etree.fromstring(xml)
        search_result = SearchResult(node)

        assert search_result.date is None


class TestSearchResultMeta:
    def test_init(self):
        """
        GIVEN an XML node and last_modified string data
        WHEN SearchResultMetadata is initialized with them
        THEN all properties are set correctly
        """
        node = etree.fromstring(
            "<property-results>"
            "<property-result>"
            "<assigned-to>test_assigned_to</assigned-to>"
            "<source-name>test_author</source-name>"
            "<source-email>test_author_email</source-email>"
            "<transfer-consignment-reference>test_consignment_reference</transfer-consignment-reference>"
            "<editor-hold>false</editor-hold>"
            "<editor-priority>30</editor-priority>"
            "<published>true</published>"
            "<transfer-received-at>2023-01-26T14:17:02Z</transfer-received-at>"
            "</property-result>"
            "</property-results>"
        )
        meta = SearchResultMetadata(node, last_modified="test_last_modified")

        assert meta.assigned_to == "test_assigned_to"
        assert meta.author == "test_author"
        assert meta.author_email == "test_author_email"
        assert meta.consignment_reference == "test_consignment_reference"
        assert meta.editor_hold == "false"
        assert meta.editor_priority == "30"
        assert meta.submission_datetime == datetime.datetime(2023, 1, 26, 14, 17, 2)
        assert meta.last_modified == "test_last_modified"
        assert meta.is_published is True

    def test_empty_properties_init(self):
        """
        GIVEN an XML node without any properties and last_modified string data
        WHEN SearchResultMetadata is initialized with them
        THEN all properties are set correctly
        """
        node = etree.fromstring(
            "<property-results>"
            "<property-result>"
            "</property-result>"
            "</property-results>"
        )
        meta = SearchResultMetadata(node, last_modified="test_last_modified")

        assert meta.assigned_to == ""
        assert meta.author == ""
        assert meta.author_email == ""
        assert meta.consignment_reference == ""
        assert meta.editor_hold == ""
        assert meta.editor_priority == EditorPriority.MEDIUM.value
        assert meta.submission_datetime == datetime.datetime.min
        assert meta.last_modified == "test_last_modified"
        assert meta.is_published is False

    @pytest.mark.parametrize(
        "published_string, editor_hold, assigned_to, expected_editor_status",
        [
            ("", "false", "", EditorStatus.NEW),
            ("", "false", "TestEditor", EditorStatus.IN_PROGRESS),
            ("", "true", "", EditorStatus.HOLD),
            ("", "true", "TestEditor", EditorStatus.HOLD),
            ("true", "false", "", EditorStatus.PUBLISHED),
            ("true", "false", "TestEditor", EditorStatus.PUBLISHED),
            ("true", "true", "", EditorStatus.PUBLISHED),
            ("true", "true", "TestEditor", EditorStatus.PUBLISHED),
        ],
    )
    def test_editor_status(
        self, published_string, assigned_to, editor_hold, expected_editor_status
    ):
        """
        GIVEN editor_hold and assigned_to values
        WHEN creating a SearchResultMetadata instance
        THEN the editor_status property returns the expected_editor_status
        """
        node = etree.fromstring(
            "<property-results>"
            "<property-result>"
            f"<assigned-to>{assigned_to}</assigned-to>"
            f"<editor-hold>{editor_hold}</editor-hold>"
            f"<published>{published_string}</published>"
            "</property-result>"
            "</property-results>"
        )
        meta = SearchResultMetadata(node, last_modified="foo")

        assert meta.editor_status == expected_editor_status.value

    @patch("caselawclient.responses.search_result.api_client")
    def test_create_from_uri(self, mock_api_client):
        """
        GIVEN a uri and a mock API client
        WHEN SearchResultMetadata.create_from_uri is called with the uri
        THEN a SearchResultMetadata object is returned with expected attributes
        """
        mock_api_client.get_properties_for_search_results.return_value = (
            "<property-results>"
            "<property-result>"
            "<assigned-to>test_assigned_to</assigned-to>"
            "<source-name>test_author</source-name>"
            "<source-email>test_author_email</source-email>"
            "<transfer-consignment-reference>test_consignment_reference</transfer-consignment-reference>"
            "<editor-hold>false</editor-hold>"
            "<editor-priority>30</editor-priority>"
            "<transfer-received-at>2023-01-26T14:17:02Z</transfer-received-at>"
            "</property-result>"
            "</property-results>"
        )
        mock_api_client.get_last_modified.return_value = "test_last_modified"

        meta = SearchResultMetadata.create_from_uri("test_uri")

        assert (
            etree.tostring(meta.node).decode()
            == mock_api_client.get_properties_for_search_results.return_value
        )
        assert meta.last_modified == "test_last_modified"

    def test_submission_date_is_min_when_transfer_received_at_empty(self):
        """
        GIVEN a node where the `transfer-received-at` element is empty
        WHEN SearchResultMetadata.create_from_uri is called with the uri
        THEN a SearchResultMetadata object is returned with
            submission_datetime equal to datetime.min
        """
        node = etree.fromstring(
            "<property-results>"
            "<property-result>"
            "<transfer-received-at></transfer-received-at>"
            "</property-result>"
            "</property-results>"
        )
        meta = SearchResultMetadata(node, last_modified="foo")

        assert meta.submission_datetime == datetime.datetime.min
