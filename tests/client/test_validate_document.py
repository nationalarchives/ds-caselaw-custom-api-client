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
                "content-type": "multipart/mixed; boundary=c878f7cb55370005"
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
                "content-type": "multipart/mixed; boundary=c878f7cb55370005"
            }
            mock_eval.return_value.content = (
                b"\r\n--c878f7cb55370005\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /xdmp:validation-errors\r\n\r\n"
                b'<xdmp:validation-errors xmlns:xdmp="http://marklogic.com/xdmp">'
                b'<error:error xmlns:error="http://marklogic.com/xdmp/error" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                b"<error:code>XDMP-VALIDATEUNEXPECTED"
                b"</error:code>"
                b"<error:name>err:XQDY0027"
                b"</error:name>"
                b"<error:xquery-version>1.0-ml"
                b"</error:xquery-version>"
                b"<error:message>Invalid node"
                b"</error:message>"
                b'<error:format-string>XDMP-VALIDATEUNEXPECTED: (err:XQDY0027) validate full { () } -- Invalid node: Found {http://docs.oasis-open.org/legaldocml/ns/akn/3.0}badger but expected ({http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRWork,{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRExpression,{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRManifestation,{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}FRBRItem?) at fn:doc("/ewca/civ/2004/632.xml")/*:akomaNtoso/*:judgment/*:meta/*:identification/*:badger using schema "/akn-modified.xsd"'
                b"</error:format-string>"
                b"<error:retryable>false"
                b"</error:retryable>"
                b"<error:expr>validate full { () }"
                b"</error:expr>"
                b"<error:data></error:data>"
                b"<error:stack></error:stack>"
                b"</error:error>"
                b"</xdmp:validation-errors>\r\n"
                b"--c878f7cb55370005--\r\n"
            )

            assert self.client.validate_document("/foo/bar/123") is False
