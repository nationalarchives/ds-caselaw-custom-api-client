import unittest
from unittest.mock import patch

from caselawclient.Client import MarklogicApiClient


class TestValidateDocument(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_validation_success(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=c878f7cb55370005",
            }
            mock_eval.return_value.content = (
                b"\r\n--c878f7cb55370005\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /xdmp:validation-errors\r\n\r\n"
                b'<xdmp:validation-errors xmlns:xdmp="http://marklogic.com/xdmp"/>\r\n'
                b"--c878f7cb55370005--\r\n"
            )

            assert self.client.validate_document("/foo/bar/123") is True

    def test_validation_failure(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=c878f7cb55370005",
            }
            mock_eval.return_value.content = (
                b"\r\n--c878f7cb55370005\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /xdmp:validation-errors\r\n\r\n"
                b'<xdmp:validation-errors xmlns:xdmp="http://marklogic.com/xdmp">'
                b'<error:error xmlns:error="http://marklogic.com/xdmp/error" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                b"</error:error>"
                b"</xdmp:validation-errors>\r\n"
                b"--c878f7cb55370005--\r\n"
            )

            assert self.client.validate_document("/foo/bar/123") is False
