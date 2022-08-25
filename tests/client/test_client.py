import unittest
from unittest.mock import MagicMock, patch

from src.caselawclient.Client import MarklogicApiClient


class ApiClientTest(unittest.TestCase):
    @patch("src.caselawclient.Client.Path")
    def test_eval_calls_request(self, MockPath):
        mock_path_instance = MockPath.return_value
        mock_path_instance.read_text.return_value = "mock-query"

        client = MarklogicApiClient("", "", "", False)
        client.session.request = MagicMock()

        client.eval("mock-query-path.xqy", vars='{{"testvar":"test"}}')

        client.session.request.assert_called_with(
            "POST",
            url=client._path_to_request_url("LATEST/eval"),
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

        client = MarklogicApiClient("", "", "", False)
        client.session.request = MagicMock()

        client.invoke("mock-query-path.xqy", vars='{{"testvar":"test"}}')

        client.session.request.assert_called_with(
            "POST",
            url=client._path_to_request_url("LATEST/invoke"),
            headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "multipart/mixed",
            },
            data={"module": "mock-query-path.xqy", "vars": '{{"testvar":"test"}}'},
        )
