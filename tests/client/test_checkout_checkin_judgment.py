import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetCheckoutStatus(unittest.TestCase):
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
        expected_result = 3600  # 1 hour in seconds
        assert result == expected_result
