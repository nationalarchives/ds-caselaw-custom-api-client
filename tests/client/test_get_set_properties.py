import json
import os
from datetime import UTC, datetime
from unittest.mock import ANY, patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient
from caselawclient.models.documents import DocumentURIString


class TestGetSetStringDocumentProperties:
    """Test cases for getting and setting document properties which are strings."""

    def setup_method(self):
        self.client = MarklogicApiClient("", "", "", False)

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
            result = self.client.get_property(DocumentURIString("judgment/uri"), "my-property")

            assert result == "my-content"

    def test_get_unset_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.content = ""
            result = self.client.get_property(DocumentURIString("judgment/uri"), "my-property")

            assert result == ""

    def test_set_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
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
                timeout=ANY,
            )


class TestGetSetBooleanDocumentProperties:
    """Test cases for getting and setting document properties which are booleans."""

    def setup_method(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_set_boolean_property_true(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
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
                timeout=ANY,
            )

    def test_set_boolean_property_false(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
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
                timeout=ANY,
            )

    def test_get_unset_boolean_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.content = ""
            result = self.client.get_boolean_property(DocumentURIString("judgment/uri"), "my-property")

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
            result = self.client.get_boolean_property(DocumentURIString("judgment/uri"), "my-property")

            assert result is True


class TestGetSetDatetimeDocumentProperties:
    """Test cases for getting and setting document properties which are datetimes."""

    def setup_method(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_set_datetime_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "2025-08-19T08:00:00+00:00",
                "name": "my-property",
            }
            self.client.set_datetime_property(uri, name="my-property", value=datetime(2025, 8, 19, 8, 0, 0, tzinfo=UTC))

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_datetime_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
                timeout=ANY,
            )

    def test_get_datetime_property(self):
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
                b"\r\n2025-08-19T12:05:53.398214Z\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_datetime_property(DocumentURIString("judgment/uri"), "my-property")

            assert result == datetime(2025, 8, 19, 12, 5, 53, 398214, tzinfo=UTC)

    def test_get_unset_datetime_property(self):
        with patch.object(self.client, "eval") as mock_eval:
            mock_eval.return_value.content = ""
            result = self.client.get_datetime_property(DocumentURIString("judgment/uri"), "my-property")

            assert result is None
