import unittest
from unittest.mock import MagicMock, patch

from src.caselawclient.Client import MarklogicApiClient


class ApiClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("src.caselawclient.Client.Path")
    def test_eval_calls_request(self, MockPath):
        mock_path_instance = MockPath.return_value
        mock_path_instance.read_text.return_value = "mock-query"

        self.client.session.request = MagicMock()

        self.client.eval("mock-query-path.xqy", vars='{{"testvar":"test"}}')

        self.client.session.request.assert_called_with(
            "POST",
            url=self.client._path_to_request_url("LATEST/eval"),
            headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "multipart/mixed",
            },
            data={"xquery": "mock-query", "vars": '{{"testvar":"test"}}'},
        )

    @patch("src.caselawclient.Client.Path")
    def test_invoke_calls_request(self, MockPath):
        mock_path_instance = MockPath.return_value
        mock_path_instance.read_text.return_value = "mock-query"

        self.client.session.request = MagicMock()

        self.client.invoke("mock-query-path.xqy", vars='{{"testvar":"test"}}')

        self.client.session.request.assert_called_with(
            "POST",
            url=self.client._path_to_request_url("LATEST/invoke"),
            headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "multipart/mixed",
            },
            data={"module": "mock-query-path.xqy", "vars": '{{"testvar":"test"}}'},
        )
