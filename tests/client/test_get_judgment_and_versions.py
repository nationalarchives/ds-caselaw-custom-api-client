import json
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetJudgment(unittest.TestCase):
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
