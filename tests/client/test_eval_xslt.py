import json
import logging
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestEvalXslt(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "testuser", "", False)

    def test_eval_xslt_user_can_view_unpublished(self):
        with patch.object(self.client, "eval"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "accessible-html.xsl",
                }
                self.client.eval_xslt(uri, show_unpublished=True)

                assert self.client.eval.call_args.args[0] == (
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy")
                )
                assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                    expected_vars
                )

    def test_eval_xslt_user_cannot_view_unpublished(self):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        with patch.object(self.client, "eval"):
            with patch.object(
                self.client,
                "user_can_view_unpublished_judgments",
                return_value=False,
            ):
                with patch.object(logging, "warning") as mock_logging:
                    uri = "/judgment/uri"
                    expected_vars = {
                        "uri": "/judgment/uri.xml",
                        "version_uri": None,
                        "show_unpublished": "false",
                        "img_location": "",
                        "xsl_filename": "accessible-html.xsl",
                    }
                    self.client.eval_xslt(uri, show_unpublished=True)

                    assert self.client.eval.call_args.args[0] == (
                        os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy")
                    )
                    assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                        expected_vars
                    )
                    mock_logging.assert_called()

    def test_eval_xslt_with_filename(self):
        with patch.object(self.client, "eval"):
            with patch.object(
                self.client, "user_can_view_unpublished_judgments", return_value=True
            ):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "as-handed-down.xsl",
                }
                self.client.eval_xslt(
                    uri, show_unpublished=True, xsl_filename="as-handed-down.xsl"
                )

                assert self.client.eval.call_args.args[0] == (
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy")
                )
                assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                    expected_vars
                )
