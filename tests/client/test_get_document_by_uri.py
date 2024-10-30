from unittest import TestCase
from unittest.mock import patch

import pytest

from caselawclient.Client import (
    DOCUMENT_COLLECTION_URI_JUDGMENT,
    DOCUMENT_COLLECTION_URI_PRESS_SUMMARY,
    DocumentHasNoTypeCollection,
    MarklogicApiClient,
)
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary


class TestGetDocumentByUri(TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.Judgment", autospec=True)
    @patch("caselawclient.Client.MarklogicApiClient.get_document_type_from_uri")
    def test_get_document_by_uri(self, mock_get_document_type, mock_judgment):
        mock_get_document_type.return_value = mock_judgment

        document = self.client.get_document_by_uri(uri="test/1234")

        mock_get_document_type.assert_called_with("test/1234")
        mock_judgment.assert_called_with("test/1234", self.client, search_query=None)

        self.assertIsInstance(document, Judgment)

    @patch("caselawclient.Client.Judgment", autospec=True)
    @patch("caselawclient.Client.MarklogicApiClient.get_document_type_from_uri")
    def test_get_document_by_uri_with_search_query(self, mock_get_document_type, mock_judgment):
        mock_get_document_type.return_value = mock_judgment

        document = self.client.get_document_by_uri(uri="test/1234", search_query="Test search")

        mock_get_document_type.assert_called_with("test/1234")
        mock_judgment.assert_called_with("test/1234", self.client, search_query="Test search")

        self.assertIsInstance(document, Judgment)


class TestGetDocumentTypeFromUri(TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_document_type_from_uri_if_judgment(
        self,
        mock_get_marklogic_response,
        mock_eval,
    ):
        mock_get_marklogic_response.return_value = [DOCUMENT_COLLECTION_URI_JUDGMENT]
        document_type = self.client.get_document_type_from_uri(uri="test/1234")
        assert document_type == Judgment

    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_document_type_from_uri_if_press_summary(
        self,
        mock_get_marklogic_response,
        mock_eval,
    ):
        mock_get_marklogic_response.return_value = [
            DOCUMENT_COLLECTION_URI_PRESS_SUMMARY,
        ]
        document_type = self.client.get_document_type_from_uri(uri="test/1234")
        assert document_type == PressSummary

    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_document_type_from_uri_if_no_valid_collection(
        self,
        mock_get_marklogic_response,
        mock_eval,
    ):
        mock_get_marklogic_response.return_value = []

        with pytest.raises(DocumentHasNoTypeCollection):
            self.client.get_document_type_from_uri(uri="test/1234")
