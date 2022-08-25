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

    def test_get_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "true"
            client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            client.eval.return_value.content = (
                b"\r\n--6bfe89fc4493c0e3\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: document-node()\r\n"
                b"X-URI: /ewca/civ/2004/632.xml\r\n"
                b'\r\n<?xml version="1.0" encoding="UTF-8"?>\n'
                b'<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n'
                b'<judgment name="judgment" contains="originalVersion">\n'
                b"</judgment>\n"
                b"</akomaNtoso>"
            )

            result = client.get_judgment_xml("/judgment/uri")

            expected = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n'
                '<judgment name="judgment" contains="originalVersion">\n'
                "</judgment>\n"
                "</akomaNtoso>"
            )
            assert result == expected

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

    def test_get_judgment_version(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            version = "3"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml", "version": "3"}
            client.get_judgment_version(uri, version)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "get_judgment_version.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_list_judgment_versions(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml"}
            client.list_judgment_versions(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "list_judgment_versions.xqy"),
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
