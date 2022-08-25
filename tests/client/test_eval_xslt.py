import json
import logging
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestEvalXslt(unittest.TestCase):
    def test_eval_xslt_user_can_view_unpublished(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            with patch.object(
                client, "user_can_view_unpublished_judgments", return_value=True
            ):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "judgment2.xsl",
                }
                client.eval_xslt(uri, show_unpublished=True)

                client.eval.assert_called_with(
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                    vars=json.dumps(expected_vars),
                    accept_header="application/xml",
                )

    def test_eval_xslt_user_cannot_view_unpublished(self):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            with patch.object(
                client, "user_can_view_unpublished_judgments", return_value=False
            ):
                with patch.object(logging, "warning") as mock_logging:
                    uri = "/judgment/uri"
                    expected_vars = {
                        "uri": "/judgment/uri.xml",
                        "version_uri": None,
                        "show_unpublished": "false",
                        "img_location": "",
                        "xsl_filename": "judgment2.xsl",
                    }
                    client.eval_xslt(uri, show_unpublished=True)

                    client.eval.assert_called_with(
                        os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                        vars=json.dumps(expected_vars),
                        accept_header="application/xml",
                    )
                    mock_logging.assert_called()

    def test_eval_xslt_with_filename(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            with patch.object(
                client, "user_can_view_unpublished_judgments", return_value=True
            ):
                uri = "/judgment/uri"
                expected_vars = {
                    "uri": "/judgment/uri.xml",
                    "version_uri": None,
                    "show_unpublished": "true",
                    "img_location": "",
                    "xsl_filename": "judgment0.xsl",
                }
                client.eval_xslt(
                    uri, show_unpublished=True, xsl_filename="judgment0.xsl"
                )

                client.eval.assert_called_with(
                    os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"),
                    vars=json.dumps(expected_vars),
                    accept_header="application/xml",
                )
