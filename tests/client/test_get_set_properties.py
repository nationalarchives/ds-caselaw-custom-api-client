import json
import os
import unittest
import warnings
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetSetJudgmentProperties(unittest.TestCase):
    def test_set_boolean_property_true(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "true",
                "name": "my-property",
            }
            client.set_boolean_property(uri, name="my-property", value="true")

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_boolean_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_boolean_property_false(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "false",
                "name": "my-property",
            }
            client.set_boolean_property(uri, name="my-property", value=False)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_boolean_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_get_unset_boolean_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = ""
            result = client.get_boolean_property("/judgment/uri", "my-property")

            assert result is False

    def test_get_boolean_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "true"
            client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            client.eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/published/text()\r\n"
                b"\r\ntrue\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = client.get_boolean_property("/judgment/uri", "my-property")

            assert result is True

    def test_get_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "my-content"
            client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            client.eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: text/plain\r\n"
                b"X-Primitive: text()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b"X-Path: /prop:properties/published/text()\r\n"
                b"\r\nmy-content\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = client.get_property("/judgment/uri", "my-property")

            assert "my-content" == result

    def test_get_unset_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = ""
            result = client.get_property("/judgment/uri", "my-property")

            assert "" == result

    def test_set_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "my-value",
                "name": "my-property",
            }
            client.set_property(uri, name="my-property", value="my-value")

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_internal_uri_leading_slash(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            client.set_judgment_this_uri(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_internal_uri_no_leading_slash(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            client.set_judgment_this_uri(uri)

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_judgment_date_warn(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(warnings, "warn") as mock_warn, patch.object(client, "eval"):
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            client.set_judgment_date(uri, content)

            assert mock_warn.call_args.kwargs == {"stacklevel": 2}
            assert client.eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_judgment_date_work_expression(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            client.set_judgment_work_expression_date(uri, content)

            assert client.eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
