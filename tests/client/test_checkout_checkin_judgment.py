import json
import os
import unittest
from datetime import UTC, datetime
from unittest.mock import ANY, patch

import pytest

from caselawclient.Client import ROOT_DIR, MarklogicApiClient
from caselawclient.models.documents import DocumentURIString


class TestGetCheckoutStatus(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_checkout_judgment(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("ewca/civ/2004/632")
            annotation = "locked by A KITTEN"
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "annotation": "locked by A KITTEN",
                "timeout": -1,
            }
            self.client.checkout_judgment(uri, annotation)

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
                timeout=ANY,
            )

    def test_checkout_judgment_with_midnight_timeout(self):
        with (
            patch.object(self.client, "eval") as mock_eval,
            patch.object(
                self.client,
                "calculate_seconds_until_midnight",
                return_value=3600,
            ),
        ):
            uri = DocumentURIString("ewca/civ/2004/632")
            annotation = "locked by A KITTEN"
            expires_at_midnight = True
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "annotation": "locked by A KITTEN",
                "timeout": 3600,
            }
            self.client.checkout_judgment(uri, annotation, expires_at_midnight)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_checkout_judgment_with_timeout_seconds(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("ewca/civ/2004/632")
            annotation = "locked by A KITTEN"
            timeout_seconds = 1234
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "annotation": "locked by A KITTEN",
                "timeout": 1234,
            }
            self.client.checkout_judgment(uri, annotation, timeout_seconds=timeout_seconds)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_checkin_judgment(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("ewca/civ/2004/632")
            expected_vars = {"uri": "/ewca/civ/2004/632.xml"}
            self.client.checkin_judgment(uri)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "checkin_judgment.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_get_checkout_status(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
            expected_vars = {"uri": "/judgment/uri.xml"}
            self.client.get_judgment_checkout_status(uri)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "get_judgment_checkout_status.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_get_checkout_status_message(self):
        with patch.object(MarklogicApiClient, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
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
            result = self.client.get_judgment_checkout_status_message(DocumentURIString("ewca/2002/2"))
            assert result == "locked by a kitten"

    def test_get_checkout_status_message_empty(self):
        with patch.object(MarklogicApiClient, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b"\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_judgment_checkout_status_message(DocumentURIString("ewca/2002/2"))
            assert result is None

    def test_get_checkout_status_message_missing_annotation_element(self):
        with patch.object(MarklogicApiClient, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            # XML response without dls:annotation element
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b'<dls:checkout xmlns:dls="http://marklogic.com/xdmp/dls">'
                b"<dls:document-uri>/ukpc/2022/17.xml</dls:document-uri>"
                b"<dls:timeout>0</dls:timeout>"
                b"</dls:checkout>"
                b"\r\n--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_judgment_checkout_status_message(DocumentURIString("ewca/2002/2"))
            assert result is None

    def test_get_checkout_status_message_annotation_element_no_text(self):
        with patch.object(MarklogicApiClient, "eval") as mock_eval:
            mock_eval.return_value.text = "true"
            mock_eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98",
            }
            # XML response with dls:annotation element but no text content
            mock_eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b'<dls:checkout xmlns:dls="http://marklogic.com/xdmp/dls">'
                b"<dls:document-uri>/ukpc/2022/17.xml</dls:document-uri>"
                b"<dls:annotation></dls:annotation>"
                b"<dls:timeout>0</dls:timeout>"
                b"</dls:checkout>"
                b"\r\n--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_judgment_checkout_status_message(DocumentURIString("ewca/2002/2"))
            assert result is None

    def test_calculate_seconds_until_midnight(self):
        dt = datetime(2020, 1, 1, 23, 0, tzinfo=UTC)  # 1 hour until midnight
        result = self.client.calculate_seconds_until_midnight(dt)
        expected_result = 3600  # 1 hour in seconds
        assert result == expected_result

    def test_calculate_seconds_until_midnight_rejects_naive_datetime(self):
        naive_datetime = datetime.fromisoformat("2020-01-01T23:00:00")
        with pytest.raises(ValueError, match="now must be timezone-aware"):
            self.client.calculate_seconds_until_midnight(naive_datetime)

    def test_break_judgment_checkout(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            client.break_checkout(uri)

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "break_judgment_checkout.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
                timeout=ANY,
            )


@pytest.mark.parametrize(
    ("method", "xquery_file"),
    [
        ("checkin_judgment_if_ours", "checkin_judgment_if_annotation_matches.xqy"),
        ("break_checkout_if_ours", "break_judgment_checkout_if_annotation_matches.xqy"),
    ],
)
class TestConditionalCheckoutRelease:
    def test_calls_conditional_xquery_with_uri_and_annotation(self, method, xquery_file):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "_eval_and_decode", return_value="true") as mock_eval_and_decode:
            getattr(client, method)(DocumentURIString("judgment/uri"), "session-token")

        mock_eval_and_decode.assert_called_once_with(
            {"uri": "/judgment/uri.xml", "annotation": "session-token"},
            xquery_file,
        )

    @pytest.mark.parametrize(("response", "expected"), [("true", True), ("false", False)])
    def test_returns_whether_checkout_was_released(self, method, xquery_file, response, expected):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "_eval_and_decode", return_value=response):
            assert getattr(client, method)(DocumentURIString("judgment/uri"), "session-token") is expected


class TestDeleteJudgmentIfOurs:
    @pytest.mark.parametrize("checkout_was_ours", [True, False])
    def test_deletes_only_after_breaking_our_checkout(self, checkout_was_ours):
        client = MarklogicApiClient("", "", "", False)

        with (
            patch.object(client, "break_checkout_if_ours", return_value=checkout_was_ours) as mock_break,
            patch.object(client, "delete_judgment") as mock_delete,
        ):
            result = client.delete_judgment_if_ours(DocumentURIString("judgment/uri"), "session-token")

        assert result is checkout_was_ours
        mock_break.assert_called_once_with("judgment/uri", "session-token")
        assert mock_delete.called is checkout_was_ours
