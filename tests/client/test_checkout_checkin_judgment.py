import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetCheckoutStatus(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_checkout_judgment(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            annotation = "locked by A KITTEN"
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "annotation": "locked by A KITTEN",
                "timeout": -1,
            }
            self.client.checkout_judgment(uri, annotation)

            self.client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_checkout_judgment_with_timeout(self):
        with patch.object(self.client, "eval"):
            with patch.object(
                self.client, "calculate_seconds_until_midnight", return_value=3600
            ):
                uri = "/ewca/civ/2004/632"
                annotation = "locked by A KITTEN"
                expires_at_midnight = True
                expected_vars = {
                    "uri": "/ewca/civ/2004/632.xml",
                    "annotation": "locked by A KITTEN",
                    "timeout": 3600,
                }
                self.client.checkout_judgment(uri, annotation, expires_at_midnight)

                assert self.client.eval.call_args.args[0] == (
                    os.path.join(ROOT_DIR, "xquery", "checkout_judgment.xqy")
                )
                assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                    expected_vars
                )

    def test_checkin_judgment(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            expected_vars = {"uri": "/ewca/civ/2004/632.xml"}
            self.client.checkin_judgment(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "checkin_judgment.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_get_checkout_status(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            self.client.get_judgment_checkout_status(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_judgment_checkout_status.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_get_checkout_status_message(self):
        with patch.object(MarklogicApiClient, "eval"):
            self.client.eval.return_value.text = "true"
            self.client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            self.client.eval.return_value.content = (
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
            result = self.client.get_judgment_checkout_status_message("/ewca/2002/2")
            assert result == "locked by a kitten"

    def test_get_checkout_status_message_empty(self):
        with patch.object(MarklogicApiClient, "eval"):
            self.client.eval.return_value.text = "true"
            self.client.eval.return_value.headers = {
                "content-type": "multipart/mixed; boundary=595658fa1db1aa98"
            }
            self.client.eval.return_value.content = (
                b"\r\n--595658fa1db1aa98\r\n"
                b"Content-Type: application/xml\r\n"
                b"X-Primitive: element()\r\n"
                b"X-Path: /*\r\n\r\n"
                b"\r\n"
                b"--595658fa1db1aa98--\r\n"
            )
            result = self.client.get_judgment_checkout_status_message("/ewca/2002/2")
            assert result is None

    def test_calculate_seconds_until_midnight(self):
        dt = datetime.strptime(
            "2020-01-01 23:00", "%Y-%m-%d %H:%M"
        )  # 1 hour until midnight
        result = self.client.calculate_seconds_until_midnight(dt)
        expected_result = 3600  # 1 hour in seconds
        assert result == expected_result

    def test_break_judgment_checkout(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            client.break_checkout(uri)

            client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "break_judgment_checkout.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )