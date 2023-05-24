import datetime
from unittest.mock import patch

import pytest

from caselawclient.search_result import EditorStatus, SearchResultMeta


class TestSearchResultMeta:
    def test_init(self):
        """
        GIVEN initial data for SearchResultMeta
        WHEN SearchResultMeta is initialized
        THEN the attributes are set correctly
        """
        meta = SearchResultMeta(
            assigned_to="test_assigned_to",
            author="test_author",
            author_email="test_author_email",
            consignment_reference="test_consignment_reference",
            editor_hold="false",
            editor_priority=20,
            last_modified="test_last_modified",
            submission_datetime=datetime.datetime(2022, 2, 14, 12, 5, 8),
        )

        assert meta.assigned_to == "test_assigned_to"
        assert meta.author == "test_author"
        assert meta.author_email == "test_author_email"
        assert meta.consignment_reference == "test_consignment_reference"
        assert meta.editor_hold == "false"
        assert meta.editor_priority == 20
        assert meta.last_modified == "test_last_modified"
        assert meta.submission_datetime == datetime.datetime(2022, 2, 14, 12, 5, 8)

    def test_empty_init(self):
        """
        GIVEN no initial data for SearchResultMeta
        WHEN SearchResultMeta is initialized with default values
        THEN the attributes are set to their default values
        """
        meta = SearchResultMeta()

        assert meta.assigned_to == ""
        assert meta.author == ""
        assert meta.author_email == ""
        assert meta.consignment_reference == ""
        assert meta.editor_hold == "false"
        assert meta.editor_priority == ""
        assert meta.last_modified == ""
        assert meta.submission_datetime is None

    @pytest.mark.parametrize(
        "editor_hold, assigned_to, expected_editor_status",
        [
            ("false", None, EditorStatus.NEW),
            ("false", "TestEditor", EditorStatus.IN_PROGRESS),
            ("true", None, EditorStatus.HOLD),
            ("true", "TestEditor", EditorStatus.HOLD),
        ],
    )
    def test_editor_status(self, assigned_to, editor_hold, expected_editor_status):
        """
        GIVEN editor_hold and assigned_to values
        WHEN creating a SearchResultMeta instance
        THEN the editor_status property returns the expected_editor_status
        """
        meta = SearchResultMeta(assigned_to=assigned_to, editor_hold=editor_hold)

        assert meta.editor_status == expected_editor_status

    @patch("caselawclient.search_result.api_client.get_last_modified")
    @patch("caselawclient.search_result.api_client.get_properties_for_search_results")
    def test_create_from_uri(
        self, mock_get_properties_for_search_results, mock_get_last_modified
    ):
        """
        GIVEN a uri
        AND get_properties_for_search_results and get_last_modified
            which have known mocked return values for that uri
        WHEN SearchResultMeta.create_from_uri is called with the uri
        THEN a SearchResultMeta object is returned with expected attributes
        """
        mock_get_properties_for_search_results.return_value = (
            "<property-results>"
            '<property-result uri="test_uri">'
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
        mock_get_last_modified.return_value = "test_last_modified"

        meta = SearchResultMeta.create_from_uri("test_uri")

        assert meta.assigned_to == "test_assigned_to"
        assert meta.author == "test_author"
        assert meta.author_email == "test_author_email"
        assert meta.consignment_reference == "test_consignment_reference"
        assert meta.editor_hold == "false"
        assert meta.editor_priority == "30"
        assert meta.last_modified == "test_last_modified"
        assert meta.submission_datetime == datetime.datetime(2023, 1, 26, 14, 17, 2)

    @patch("caselawclient.search_result.api_client.get_last_modified")
    @patch("caselawclient.search_result.api_client.get_properties_for_search_results")
    def test_create_from_uri_when_transfer_received_at_empty(
        self, mock_get_properties_for_search_results, _
    ):
        """
        GIVEN a uri
        AND get_properties_for_search_results and get_last_modified
            which have known mocked return values for that uri
        AND `transfer-received-at` element is empty
        WHEN SearchResultMeta.create_from_uri is called with the uri
        THEN a SearchResultMeta object is returned with
            submission_datetime equal to datetime.min

        """
        mock_get_properties_for_search_results.return_value = (
            "<property-results>"
            '<property-result uri="test_uri">'
            "<transfer-received-at></transfer-received-at>"
            "</property-result>"
            "</property-results>"
        )

        uri = "test_uri"

        meta = SearchResultMeta.create_from_uri(uri)

        assert meta.submission_datetime == datetime.datetime.min
