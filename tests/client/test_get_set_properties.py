import json
import os
import unittest
from unittest.mock import patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient
from caselawclient.models.documents import DocumentURIString


class TestGetSetJudgmentProperties(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_set_boolean_property_true(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("/judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "true",
                "name": "my-property",
            }
            self.client.set_boolean_property(uri, name="my-property", value=True)

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_boolean_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_boolean_property_false(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("/judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "false",
                "name": "my-property",
            }
            self.client.set_boolean_property(uri, name="my-property", value=False)

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_boolean_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_get_unset_boolean_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.content = ""
            result = self.client.get_boolean_property(DocumentURIString("/judgment/uri"), "my-property")

            assert result is False

    def test_get_boolean_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/published/text()\r\n"
                b"\r\ntrue\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_boolean_property(DocumentURIString("/judgment/uri"), "my-property")

            assert result is True

    def test_get_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.text = "my-content"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/published/text()\r\n"
                b"\r\nmy-content\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_property(DocumentURIString("/judgment/uri"), "my-property")

            assert result == "my-content"

    def test_get_unset_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.content = ""
            result = self.client.get_property(DocumentURIString("/judgment/uri"), "my-property")

            assert result == ""

    def test_set_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("/judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "my-value",
                "name": "my-property",
            }
            self.client.set_property(uri, name="my-property", value="my-value")

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )
