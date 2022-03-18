import json
import os
import unittest
from unittest.mock import MagicMock, patch

from lxml import etree

from src.caselawclient.Client import MarklogicApiClient, RESULTS_PER_PAGE, ROOT_DIR


class ApiClientTest(unittest.TestCase):
    @patch("src.caselawclient.Client.Path")
    def test_eval_calls_request(self, MockPath):
        mock_path_instance = MockPath.return_value
        mock_path_instance.read_text.return_value = "mock-query"

        client = MarklogicApiClient("", "", "", False)
        client.session.request = MagicMock()

        client.eval("mock-query-path.xqy", vars='{{"testvar":"test"}}', database="mockdatabase")

        client.session.request.assert_called_with(
            "POST",
            url=client._path_to_request_url("LATEST/eval?database=mockdatabase"),
            headers={
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "multipart/mixed"
            },
            data={
                "xquery": "mock-query",
                "vars": '{{"testvar":"test"}}'
            }
        )

    def test_advanced_search(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            client.advanced_search(
                q="my-query",
                court="ewhc",
                judge="a. judge",
                party="a party",
                page=2,
            )

            expected_vars = {
                "court": "ewhc",
                "judge": "a. judge",
                "page": 2,
                "page-size": RESULTS_PER_PAGE,
                "q": "my-query",
                "party": "a party",
                "order": "",
                "from": "",
                "to": "",
                "show_unpublished": "false"
            }

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "search.xqy"),
                json.dumps(expected_vars)
            )

    def test_eval_xslt(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "show_unpublished": "true",
            }
            client.eval_xslt(uri, show_unpublished=True)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                vars=json.dumps(expected_vars),
                accept_header='application/xml'
            )

    def test_set_boolean_property_true(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "true",
                "name": "my-property"
            }
            client.set_boolean_property(uri, name="my-property", value="true")

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml"
            )

    def test_set_boolean_property_false(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "value": "false",
                "name": "my-property"
            }
            client.set_boolean_property(uri, name="my-property", value=False)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_property.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml"
            )

    def test_get_unset_boolean_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            client.eval.return_value.text = ''
            result = client.get_boolean_property("/judgment/uri", "my-property")

            self.assertFalse(result)

    def test_get_boolean_property(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            client.eval.return_value.text = 'true'
            client.eval.return_value.headers = {'content-type': 'multipart/mixed; boundary=595658fa1db1aa98'}
            client.eval.return_value.content = b'\r\n--595658fa1db1aa98\r\n' \
                                               b'Content-Type: text/plain\r\n' \
                                               b'X-Primitive: text()\r\n' \
                                               b'X-URI: /ewca/civ/2004/632.xml\r\n' \
                                               b'X-Path: /prop:properties/published/text()\r\n' \
                                               b'\r\ntrue\r\n' \
                                               b'--595658fa1db1aa98--\r\n'
            result = client.get_boolean_property("/judgment/uri", "my-property")

            self.assertTrue(result)

    def test_get_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            client.eval.return_value.text = 'true'
            client.eval.return_value.headers = {'content-type': 'multipart/mixed; boundary=595658fa1db1aa98'}
            client.eval.return_value.content = b'\r\n--6bfe89fc4493c0e3\r\n' \
                                               b'Content-Type: application/xml\r\n' \
                                               b'X-Primitive: document-node()\r\n' \
                                               b'X-URI: /ewca/civ/2004/632.xml\r\n' \
                                               b'\r\n<?xml version="1.0" encoding="UTF-8"?>\n' \
                                               b'<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n' \
                                               b'<judgment name="judgment" contains="originalVersion">\n' \
                                               b'</judgment>\n' \
                                               b'</akomaNtoso>'

            result = client.get_judgment_xml("/judgment/uri")

            expected = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n' \
                        '<judgment name="judgment" contains="originalVersion">\n' \
                        '</judgment>\n' \
                        '</akomaNtoso>'
            self.assertEqual(result, expected)

    def test_save_judgment_xml(self):
        api_client = MarklogicApiClient("a", "b", "c", True)
        with patch.object(api_client, 'make_request'):
            uri = "/ewca/civ/2004/632"
            xml = etree.fromstring("<root></root>")
            api_client.save_judgment_xml(uri, xml)
            api_client.make_request.assert_called_with(
                "PUT",
                "LATEST/documents?uri=/ewca/civ/2004/632.xml",
                headers={"Accept": "text/xml", "Content-type": "application/xml"},
                body=b"<root/>",
            )