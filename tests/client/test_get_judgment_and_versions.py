import json
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetJudgment(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_judgment_xml(self):
        with patch.object(self.client, "eval"):
            self.client.eval.return_value.text = "true"
            self.client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            self.client.eval.return_value.content = (
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

            result = self.client.get_judgment_xml("/judgment/uri")

            expected = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n'
                '<judgment name="judgment" contains="originalVersion">\n'
                "</judgment>\n"
                "</akomaNtoso>"
            )
            assert result == expected

    def test_get_judgment_version(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            version = "3"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml", "version": "3"}
            self.client.get_judgment_version(uri, version)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_judgment_version.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_list_judgment_versions(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml"}
            self.client.list_judgment_versions(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "list_judgment_versions.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )
