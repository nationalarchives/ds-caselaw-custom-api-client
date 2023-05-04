import unittest
from unittest.mock import MagicMock, patch

from caselawclient.Client import MarklogicApiClient


class ApiClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    def test_eval_and_decode(self, mock_eval):
        mock_eval.return_value.headers = {
            "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
        }
        mock_eval.return_value.content = (
            b"\r\n--595658fa1db1aa98\r\n"
            b"Content-Type: application/xml\r\n"
            b"X-Primitive: element()\r\n"
            b"X-Path: /*\r\n\r\n"
            b"true\r\n"
            b"--595658fa1db1aa98--\r\n"
        )
        assert (
            self.client._eval_and_decode({"url": "/2029/eat/1"}, "myfile.xqy") == "true"
        )

    @patch("caselawclient.Client.MarklogicApiClient._eval_and_decode")
    def test_judgment_exists(self, mock_decode):
        mock_decode.return_value = "true"
        assert self.client.judgment_exists("/2029/eat/1") is True
        mock_decode.assert_called_with(
            {"uri": "/2029/eat/1.xml"}, "judgment_exists.xqy"
        )

    @patch("caselawclient.Client.MarklogicApiClient._eval_and_decode")
    def test_judgment_not_exists(self, mock_decode):
        mock_decode.return_value = "false"
        assert self.client.judgment_exists("/2029/eat/1") is False
        mock_decode.assert_called_with(
            {"uri": "/2029/eat/1.xml"}, "judgment_exists.xqy"
        )

    @patch("caselawclient.Client.Path")
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

    @patch("caselawclient.Client.Path")
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

    def test_format_uri(self):
        uri = "/ewca/2022/123"
        assert self.client._format_uri_for_marklogic(uri) == "/ewca/2022/123.xml"

    def test_format_uri_no_leading_slash(self):
        uri = "ewca/2022/123"
        assert self.client._format_uri_for_marklogic(uri) == "/ewca/2022/123.xml"

    def test_format_uri_trailing_slash(self):
        uri = "ewca/2022/123/"
        assert self.client._format_uri_for_marklogic(uri) == "/ewca/2022/123.xml"

    def test_format_uri_all_the_slashes(self):
        uri = "/ewca/2022/123/"
        assert self.client._format_uri_for_marklogic(uri) == "/ewca/2022/123.xml"
