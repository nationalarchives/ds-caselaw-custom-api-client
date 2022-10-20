import json
import os
import unittest
import warnings
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


@patch("src.caselawclient.Client.decode_multipart")
@patch("src.caselawclient.Client.MarklogicApiClient.eval")
def test_get_judgment_citation(send, decode):
    uri = "judgment/uri"
    expected_vars = {"uri": "/judgment/uri.xml"}
    decode.return_value = "ewca/fam/1"  # The decoder is called
    MarklogicApiClient("", "", "", "").get_judgment_citation(uri) == "ewca/fam/1"

    assert send.call_args.args[0] == (
        os.path.join(ROOT_DIR, "xquery", "get_metadata_citation.xqy")
    )
    assert send.call_args.kwargs["vars"] == json.dumps(expected_vars)


class TestGetSetMetadata(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_set_judgment_citation(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            content = "new neutral citation"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_citation(uri, content)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_citation.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_get_judgment_court(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            self.client.get_judgment_court(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_metadata_court.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_set_judgment_court(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            content = "new court"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_court(uri, content)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_court.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_get_judgment_date(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            self.client.get_judgment_work_date(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_metadata_work_date.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_set_judgment_date(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            content = "01-01-2023"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_work_expression_date(uri, content)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_set_judgment_date_warn(self):
        with patch.object(warnings, "warn") as mock_warn, patch.object(
            self.client, "eval"
        ):
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            self.client.set_judgment_date(uri, content)

            assert mock_warn.call_args.kwargs == {"stacklevel": 2}
            assert self.client.eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_set_internal_uri_leading_slash(self):
        with patch.object(self.client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            self.client.set_judgment_this_uri(uri)

            self.client.eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_internal_uri_no_leading_slash(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            self.client.set_judgment_this_uri(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )
