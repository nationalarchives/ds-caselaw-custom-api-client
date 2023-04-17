import json
import os
import unittest
import warnings
from unittest.mock import patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient


@patch("caselawclient.Client.decode_multipart")
@patch("caselawclient.Client.MarklogicApiClient.eval")
def test_get_properties_for_search_results(send, decode):
    uris = ["judgment/uri"]
    expected_vars = {"uris": ["/judgment/uri.xml"]}
    decode.return_value = "decoded_value"  # The decoder is called
    retval = MarklogicApiClient("", "", "", False).get_properties_for_search_results(
        uris
    )
    assert retval == "decoded_value"

    assert send.call_args.args[0] == (
        os.path.join(ROOT_DIR, "xquery", "get_properties_for_search_results.xqy")
    )
    assert send.call_args.kwargs["vars"] == json.dumps(expected_vars)


@patch("caselawclient.Client.decode_multipart")
@patch("caselawclient.Client.MarklogicApiClient.eval")
def test_get_judgment_citation(send, decode):
    uri = "judgment/uri"
    expected_vars = {"uri": "/judgment/uri.xml"}
    decode.return_value = "ewca/fam/1"  # The decoder is called
    retval = MarklogicApiClient("", "", "", False).get_judgment_citation(uri)
    assert retval == "ewca/fam/1"

    assert send.call_args.args[0] == (
        os.path.join(ROOT_DIR, "xquery", "get_metadata_citation.xqy")
    )
    assert send.call_args.kwargs["vars"] == json.dumps(expected_vars)


class TestGetSetMetadata(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_set_judgment_citation(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "judgment/uri"
            content = "new neutral citation"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_citation(uri, content)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_citation.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    @patch("caselawclient.Client.decode_multipart")
    def test_get_judgment_court(self, decode):
        with patch.object(self.client, "eval") as mock_eval:
            decode.return_value = "EWCA-Fam"
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            retval = self.client.get_judgment_court(uri)
            assert retval == "EWCA-Fam"

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_metadata_court.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_judgment_court(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "judgment/uri"
            content = "new court"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_court(uri, content)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_court.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    @patch("caselawclient.Client.decode_multipart")
    def test_get_judgment_date(self, decode):
        with patch.object(self.client, "eval") as mock_eval:
            decode.return_value = "2022-01-01"
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            retval = self.client.get_judgment_work_date(uri)
            assert retval == "2022-01-01"

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_metadata_work_date.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_judgment_date(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "judgment/uri"
            content = "01-01-2023"
            expected_vars = {"uri": "/judgment/uri.xml", "content": content}
            self.client.set_judgment_work_expression_date(uri, content)

            assert mock_eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_judgment_date_warn(self):
        with patch.object(warnings, "warn") as mock_warn, patch.object(
            self.client, "eval"
        ) as mock_eval:
            uri = "judgment/uri"
            content = "2022-01-01"
            expected_vars = {"uri": "/judgment/uri.xml", "content": "2022-01-01"}
            self.client.set_judgment_date(uri, content)

            assert mock_warn.call_args.kwargs == {"stacklevel": 2}
            assert mock_eval.call_args.args[0] == (
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_work_expression_date.xqy"
                )
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_set_internal_uri_leading_slash(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            self.client.set_judgment_this_uri(uri)

            mock_eval.assert_called_with(
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy"),
                vars=json.dumps(expected_vars),
                accept_header="application/xml",
            )

    def test_set_internal_uri_no_leading_slash(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
                "content_with_id": "https://caselaw.nationalarchives.gov.uk/id/judgment/uri",
                "content_without_id": "https://caselaw.nationalarchives.gov.uk/judgment/uri",
                "content_with_xml": "https://caselaw.nationalarchives.gov.uk/judgment/uri/data.xml",
            }
            self.client.set_judgment_this_uri(uri)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "set_metadata_this_uri.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
