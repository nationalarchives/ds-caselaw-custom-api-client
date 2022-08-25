import json
import os
import unittest
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


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

    def test_save_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            client.save_judgment_xml(uri, judgment_xml, "my annotation")

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "update_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_save_locked_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = judgment_str.encode("utf-8")
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "update_locked_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_insert_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My new judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "",
            }
            client.insert_judgment_xml(uri, judgment_xml)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "insert_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_delete_document(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            client.delete_judgment(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "delete_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_copy_judgment(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            old_uri = "/judgment/old_uri"
            new_uri = "/judgment/new_uri"
            expected_vars = {
                "old_uri": "/judgment/old_uri.xml",
                "new_uri": "/judgment/new_uri.xml",
            }
            client.copy_judgment(old_uri, new_uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "copy_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )
