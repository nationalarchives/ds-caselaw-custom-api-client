import re
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
import responses
from requests import Request

from caselawclient.Client import (
    MarklogicApiClient,
    MultipartResponseLongerThanExpected,
    get_multipart_strings_from_marklogic_response,
    get_single_string_from_marklogic_response,
)
from caselawclient.errors import GatewayTimeoutError
from caselawclient.models.documents import DocumentURIString


class TestErrors(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_timeout(self):
        with responses.RequestsMock() as response_list:
            response_list.add(
                responses.GET,
                url="http://example.com",
                status=504,
                body="Example Gateway Timeout.",
            )
            response = requests.get("http://example.com")  # noqa: S113
        with pytest.raises(GatewayTimeoutError) as gateway_exception:
            self.client._raise_for_status(response)
        assert "Example Gateway Timeout" in str(gateway_exception.value)


class TestMarklogicResponseHandlers(unittest.TestCase):
    @patch("caselawclient.Client.decoder.MultipartDecoder.from_response")
    def test_get_multipart_strings_from_marklogic_response(
        self,
        mock_multipart_decoder,
    ):
        mock_multipart_decoder.return_value.parts = (
            SimpleNamespace(text="string 1"),
            SimpleNamespace(text="string 2"),
        )
        assert get_multipart_strings_from_marklogic_response(
            MagicMock(requests.Response),
        ) == ["string 1", "string 2"]

    def test_get_multipart_strings_from_marklogic_response_if_no_content(self):
        response = MagicMock(requests.Response)
        response.content = None
        assert get_multipart_strings_from_marklogic_response(response) == []

    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_single_string_from_marklogic_response(
        self,
        mock_multipart_strings_handler,
    ):
        mock_multipart_strings_handler.return_value = ["test string"]
        assert get_single_string_from_marklogic_response(MagicMock(requests.Response)) == "test string"

    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_single_string_from_marklogic_response_if_empty_set(
        self,
        mock_multipart_strings_handler,
    ):
        mock_multipart_strings_handler.return_value = []
        assert get_single_string_from_marklogic_response(MagicMock(requests.Response)) == ""

    @patch("caselawclient.Client.get_multipart_strings_from_marklogic_response")
    def test_get_single_string_from_marklogic_response_if_multiple_strings(
        self,
        mock_multipart_strings_handler,
    ):
        mock_multipart_strings_handler.return_value = [
            "test string",
            "too many strings",
        ]
        with pytest.raises(MultipartResponseLongerThanExpected):
            get_single_string_from_marklogic_response(MagicMock(requests.Response))


class ApiClientTest(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    @patch("caselawclient.Client.MarklogicApiClient._send_to_eval")
    def test_eval_and_decode(self, mock_eval):
        mock_eval.return_value.headers = {
            "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
        }
        mock_eval.return_value.content = (
            b"\r\n--595658fa1db1aa98\r\n"
            b"Content-Type: application/xml\r\n"
            b"X-Primitive: element()\r\n"
            b"X-Path: /*\r\n\r\n"
            b"true\r\n"
            b"--595658fa1db1aa98--\r\n"
        )
        assert self.client._eval_and_decode({}, "myfile.xqy") == "true"

    @patch("caselawclient.Client.MarklogicApiClient._eval_and_decode")
    def test_document_exists(self, mock_decode):
        mock_decode.return_value = "true"
        assert self.client.document_exists(DocumentURIString("2029/eat/1")) is True
        mock_decode.assert_called_with(
            {"uri": "/2029/eat/1.xml"},
            "document_exists.xqy",
        )

    @patch("caselawclient.Client.MarklogicApiClient._eval_and_decode")
    def test_document_not_exists(self, mock_decode):
        mock_decode.return_value = "false"
        assert self.client.document_exists(DocumentURIString("2029/eat/1")) is False
        mock_decode.assert_called_with(
            {"uri": "/2029/eat/1.xml"},
            "document_exists.xqy",
        )

    @patch("caselawclient.Client.Path")
    def test_eval_calls_request(self, MockPath):
        mock_path_instance = MockPath.return_value
        mock_path_instance.read_text.return_value = "mock-query"

        with patch.object(self.client.session, "request") as patched_request:
            self.client.eval("mock-query-path.xqy", vars='{{"testvar":"test"}}')

            patched_request.assert_called_with(
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

        with patch.object(self.client.session, "request") as patched_request:
            self.client.invoke("mock-query-path.xqy", vars='{{"testvar":"test"}}')

            patched_request.assert_called_with(
                "POST",
                url=self.client._path_to_request_url("LATEST/invoke"),
                headers={
                    "Content-type": "application/x-www-form-urlencoded",
                    "Accept": "multipart/mixed",
                },
                data={"module": "mock-query-path.xqy", "vars": '{{"testvar":"test"}}'},
            )

    def test_format_uri(self):
        uri = DocumentURIString("ewca/2022/123")
        assert self.client._format_uri_for_marklogic(uri) == "/ewca/2022/123.xml"

    def test_user_agent(self):
        user_agent = self.client.session.prepare_request(
            Request("GET", "http://example.invalid"),
        ).headers["user-agent"]
        assert re.match(r"^ds-caselaw-marklogic-api-client/\d+", user_agent)

    def test_get_error_code(self):
        xml_string = """
        <error-response xmlns="http://marklogic.com/xdmp/error">
            <status-code>500</status-code>
            <status>Internal Server Error</status>
            <message-code>XDMP-DOCNOTFOUND</message-code>
            <message>
                XDMP-DOCNOTFOUND:
                xdmp:document-get-properties("/a/fake/judgment/.xml", fn:QName("","published"))
                 -- Document not found
            </message>
            <message-detail>
                <message-title>Document not found</message-title>
            </message-detail>
        </error-response>
        """
        result = self.client._get_error_code(xml_string)
        self.assertEqual(result, "XDMP-DOCNOTFOUND")

    def test_get_error_code_missing_message(self):
        xml_string = """
        <error-response xmlns="http://marklogic.com/xdmp/error">
            <status-code>500</status-code>
            <status>Internal Server Error</status>
        </error-response>
        """
        result = self.client._get_error_code(xml_string)
        self.assertEqual(
            result,
            "Unknown error, Marklogic returned a null or empty response",
        )

    def test_get_error_code_xml_empty_string(self):
        xml_string = ""
        result = self.client._get_error_code(xml_string)
        self.assertEqual(
            result,
            "Unknown error, Marklogic returned a null or empty response",
        )

    def test_get_error_code_xml_none(self):
        xml_string = None
        result = self.client._get_error_code(xml_string)
        self.assertEqual(
            result,
            "Unknown error, Marklogic returned a null or empty response",
        )
