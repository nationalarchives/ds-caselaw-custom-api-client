from unittest import TestCase
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.judgments import Judgment


class TestGetDocument(TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.Judgment", autospec=True)
    def test_get_document_by_uri(self, mock_judgment):
        document = self.client.get_document_by_uri(uri="test/1234")

        mock_judgment.assert_called_with("test/1234", self.client)
        self.assertIsInstance(document, Judgment)
