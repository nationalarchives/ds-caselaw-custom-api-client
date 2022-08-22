import json
import logging
import os
import unittest
import warnings
from datetime import datetime
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient
import pytest as pytest


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

    def test_advanced_search_user_can_view_unpublished_but_show_unpublished_is_false(self):
        """If a user who is allowed to view unpublished judgments wishes to specifically see only published
           judgments, do not change the value of `show_unpublished`"""
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'invoke'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=True):
                client.advanced_search(
                    q="my-query",
                    court="ewhc",
                    judge="a. judge",
                    party="a party",
                    page=2,
                    page_size=20,
                    show_unpublished=False
                )

                expected_vars = {
                    "court": "ewhc",
                    "judge": "a. judge",
                    "page": 2,
                    "page-size": 20,
                    "q": "my-query",
                    "party": "a party",
                    "neutral_citation": "",
                    "specific_keyword": "",
                    "order": "",
                    "from": "",
                    "to": "",
                    "show_unpublished": "false",
                    "only_unpublished": "false"
                }

                client.invoke.assert_called_with(
                    '/judgments/search/search.xqy',
                    json.dumps(expected_vars)
                )

    def test_advanced_search_user_can_view_unpublished_and_show_unpublished_is_true(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'invoke'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=True):
                client.advanced_search(
                    q="my-query",
                    court="ewhc",
                    judge="a. judge",
                    party="a party",
                    page=2,
                    page_size=20,
                    show_unpublished=True
                )

                expected_vars = {
                    "court": "ewhc",
                    "judge": "a. judge",
                    "page": 2,
                    "page-size": 20,
                    "q": "my-query",
                    "party": "a party",
                    "neutral_citation": "",
                    "specific_keyword": "",
                    "order": "",
                    "from": "",
                    "to": "",
                    "show_unpublished": "true",
                    "only_unpublished": "false"
                }

                client.invoke.assert_called_with(
                    '/judgments/search/search.xqy',
                    json.dumps(expected_vars)
                )

    def test_advanced_search_user_cannot_view_unpublished_but_show_unpublished_is_true(self):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'invoke'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=False):
                with patch.object(logging, "warning") as mock_logging:
                    client.advanced_search(
                        q="my-query",
                        court="ewhc",
                        judge="a. judge",
                        party="a party",
                        page=2,
                        page_size=20,
                        show_unpublished=True
                    )

                    expected_vars = {
                        "court": "ewhc",
                        "judge": "a. judge",
                        "page": 2,
                        "page-size": 20,
                        "q": "my-query",
                        "party": "a party",
                        "neutral_citation": "",
                        "specific_keyword": "",
                        "order": "",
                        "from": "",
                        "to": "",
                        "show_unpublished": "false",
                        "only_unpublished": "false"
                    }

                    client.invoke.assert_called_with(
                        '/judgments/search/search.xqy',
                        json.dumps(expected_vars)
                    )
                    mock_logging.assert_called()

    def test_eval_xslt_with_default_and_user_can_view_unpublished(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=True):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "judgment2.xsl"
                }
                client.eval_xslt(uri, show_unpublished=True)

                client.eval.assert_called_with(
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                    vars=json.dumps(expected_vars),
                    accept_header='application/xml'
                )

    def test_eval_xslt_with_default_and_user_cannot_view_unpublished(self):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=False):
                with patch.object(logging, "warning") as mock_logging:
                    uri = "/judgment/uri"
                    expected_vars = {
                        "uri": "/judgment/uri.xml",
                        "version_uri": None,
                        "show_unpublished": "false",
                        "img_location": "",
                        "xsl_filename": "judgment2.xsl"
                    }
                    client.eval_xslt(uri, show_unpublished=True)

                    client.eval.assert_called_with(
                        os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                        vars=json.dumps(expected_vars),
                        accept_header='application/xml'
                    )
                    mock_logging.assert_called()

    def test_eval_xslt_with_filename(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, 'eval'):
            with patch.object(client, 'user_can_view_unpublished_judgments', return_value=True):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "judgment0.xsl"
                }
                client.eval_xslt(uri, show_unpublished=True, xsl_filename="judgment0.xsl")

                client.eval.assert_called_with(
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                    vars=json.dumps(expected_vars),
                    accept_header='application/xml'
                )

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

            assert result == False

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

            assert result == True

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

            expected = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                        '<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">\n' \
                        '<judgment name="judgment" contains="originalVersion">\n' \
                        '</judgment>\n' \
                        '</akomaNtoso>'
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

    def test_checkout_judgment(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            annotation = "locked by A KITTEN"
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "annotation": "locked by A KITTEN",
                "timeout": -1,
            }
            client.checkout_judgment(uri, annotation)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_checkout_judgment_with_timeout(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            with patch.object(
                client, "calculate_seconds_until_midnight", return_value=3600
            ):
                uri = "/ewca/civ/2004/632"
                annotation = "locked by A KITTEN"
                expires_at_midnight = True
                expected_vars = {
                    "uri": "/ewca/civ/2004/632.xml",
                    "annotation": "locked by A KITTEN",
                    "timeout": 3600,
                }
                client.checkout_judgment(uri, annotation, expires_at_midnight)

                client.eval.assert_called_with(
                    os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"),
                    vars=json.dumps(expected_vars),
                    accept_header="application/xml",
                )

    def test_checkin_judgment(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml"}
            client.checkin_judgment(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "checkin_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

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

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_judgment_date_warn(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(warnings, "warn") as mock_warn, patch.object(client, "eval"):
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            client.set_judgment_date(uri, content)

            assert mock_warn.call_args.kwargs == {"stacklevel": 2}
            client.eval.assert_called_with(
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                ),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_judgment_date_work_expression(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            client.set_judgment_work_expression_date(uri, content)

            client.eval.assert_called_with(
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                ),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_get_checkout_status(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            client.get_judgment_checkout_status(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "get_judgment_checkout_status.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_get_checkout_status_message(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(MarklogicApiClient, "eval"):
            client.eval.return_value.text = "true"
            client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            client.eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b'<dls:checkout xmlns:dls="http://marklogic.com/xdmp/dls">'
                b"<dls:document-uri>/ukpc/2022/17.xml</dls:document-uri>"
                b"<dls:annotation>locked by a kitten</dls:annotation>"
                b"<dls:timeout>0</dls:timeout>"
                b"<dls:timestamp>1660210484</dls:timestamp>"
                b'<sec:user-id xmlns:sec="http://marklogic.com/xdmp/security">10853946559473170020</sec:user-id>'
                b"</dls:checkout>\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = client.get_judgment_checkout_status_message("/ewca/2002/2")
            assert result == "locked by a kitten"

    def test_get_checkout_status_message_empty(self):
        client = MarklogicApiClient("", "", "", False)
        with patch.object(MarklogicApiClient, "eval"):
            client.eval.return_value.text = "true"
            client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            client.eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b"\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = client.get_judgment_checkout_status_message("/ewca/2002/2")
            assert result is None

    def test_calculate_seconds_until_midnight(self):
        client = MarklogicApiClient("", "", "", False)
        dt = datetime.strptime(
            "2020-01-01 23:00", "%Y-%m-%d %H:%M"
        )  # 1 hour until midnight
        result = client.calculate_seconds_until_midnight(dt)
        expected_result = 3600 # 1 hour in seconds
        assert result == expected_result

    def test_user_has_privilege(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            user = "laura"
            privilege_uri = "https://caselaw.nationalarchives.gov.uk/custom/uri"
            privilege_action = "execute"
            expected_vars = {
                "user": "laura",
                "privilege_uri": "https://caselaw.nationalarchives.gov.uk/custom/uri",
                "privilege_action": "execute",
            }
            client.user_has_privilege(user, privilege_uri, privilege_action)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "user_has_privilege.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_user_can_view_unpublished_judgments_true(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "true"

            result = client.user_can_view_unpublished_judgments("laura")
            assert result == True

    def test_user_can_view_unpublished_judgments_false(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            client.eval.return_value.text = "false"

            result = client.user_can_view_unpublished_judgments("laura")
            assert result == False

    def test_verify_show_unpublished_user_cannot_view_unpublished_and_show_unpublished_true(self):
        # User cannot view unpublished but is asking to view unpublished judgments
        client = MarklogicApiClient("", "", "", False)
        with patch.object(client, "user_can_view_unpublished_judgments", return_value=False):
            with patch.object(logging, "warning") as mock_logger:
                result = client.verify_show_unpublished(True)
                assert result == False
                # Check the logger was called
                mock_logger.assert_called()

    def test_verify_show_unpublished_user_cannot_view_unpublished_and_show_unpublished_false(self):
        # User cannot view unpublished and is not asking to view unpublished judgments
        client = MarklogicApiClient("", "", "", False)
        with patch.object(client, "user_can_view_unpublished_judgments", return_value=False):
            result = client.verify_show_unpublished(False)
            self.assertEqual(result, False)

    def test_verify_show_unpublished_user_can_view_unpublished_and_show_unpublished_true(self):
        # User can view unpublished and is asking to view unpublished judgments
        client = MarklogicApiClient("", "", "", False)
        with patch.object(client, "user_can_view_unpublished_judgments", return_value=True):
            result = client.verify_show_unpublished(True)
            assert result == True

    def test_verify_show_unpublished_user_can_view_unpublished_and_show_unpublished_false(self):
        # User can view unpublished but is NOT asking to view unpublished judgments
        client = MarklogicApiClient("", "", "", False)
        with patch.object(client, "user_can_view_unpublished_judgments", return_value=True):
            result = client.verify_show_unpublished(False)
            assert result == False
