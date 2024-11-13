import json
import logging
import os
import unittest
from unittest.mock import patch

from caselawclient.Client import ROOT_DIR, MarklogicApiClient, MarkLogicDocumentURIString
from caselawclient.models.documents import DocumentURIString
from caselawclient.xquery_type_dicts import XsltTransformDict


class TestEvalXslt(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "testuser", "", False)

    @patch.dict(os.environ, {"XSLT_IMAGE_LOCATION": "imagepath"}, clear=True)
    def test_eval_xslt_user_can_view_unpublished(self):
        with patch.object(self.client, "eval") as mock_eval, patch.object(
            self.client,
            "user_can_view_unpublished_judgments",
            return_value=True,
        ):
            uri = DocumentURIString("judgment/uri")
            expected_vars: XsltTransformDict = {
                "uri": MarkLogicDocumentURIString("/judgment/uri.xml"),
                "version_uri": None,
                "show_unpublished": True,
                "img_location": "imagepath",
                "xsl_filename": "accessible-html.xsl",
                "query": None,
            }
            self.client.eval_xslt(uri, show_unpublished=True)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    @patch.dict(os.environ, {"XSLT_IMAGE_LOCATION": "imagepath"}, clear=True)
    def test_eval_xslt_user_cannot_view_unpublished(self):
        """The user is not permitted to see unpublished judgments but is attempting to view them
        Set `show_unpublished` to false and log a warning"""
        with patch.object(self.client, "eval") as mock_eval, patch.object(
            self.client,
            "user_can_view_unpublished_judgments",
            return_value=False,
        ), patch.object(logging, "warning") as mock_logging:
            uri = DocumentURIString("judgment/uri")
            expected_vars: XsltTransformDict = {
                "uri": MarkLogicDocumentURIString("/judgment/uri.xml"),
                "version_uri": None,
                "show_unpublished": False,
                "img_location": "imagepath",
                "xsl_filename": "accessible-html.xsl",
                "query": None,
            }
            self.client.eval_xslt(uri, show_unpublished=True)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars,
            )
            mock_logging.assert_called()

    @patch.dict(os.environ, {"XSLT_IMAGE_LOCATION": "imagepath"}, clear=True)
    def test_eval_xslt_with_filename(self):
        with patch.object(self.client, "eval") as mock_eval, patch.object(
            self.client,
            "user_can_view_unpublished_judgments",
            return_value=True,
        ):
            uri = DocumentURIString("judgment/uri")
            expected_vars: XsltTransformDict = {
                "uri": MarkLogicDocumentURIString("/judgment/uri.xml"),
                "version_uri": None,
                "show_unpublished": True,
                "img_location": "imagepath",
                "xsl_filename": "as-handed-down.xsl",
                "query": None,
            }
            self.client.eval_xslt(
                uri,
                show_unpublished=True,
                xsl_filename="as-handed-down.xsl",
            )

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    @patch.dict(os.environ, {"XSLT_IMAGE_LOCATION": "imagepath"}, clear=True)
    def test_eval_xslt_with_query(self):
        with patch.object(self.client, "eval") as mock_eval, patch.object(
            self.client,
            "user_can_view_unpublished_judgments",
            return_value=True,
        ):
            uri = DocumentURIString("judgment/uri")
            query = "the query string"
            expected_vars: XsltTransformDict = {
                "uri": MarkLogicDocumentURIString("/judgment/uri.xml"),
                "version_uri": None,
                "show_unpublished": True,
                "img_location": "imagepath",
                "xsl_filename": "as-handed-down.xsl",
                "query": query,
            }
            self.client.eval_xslt(
                uri,
                show_unpublished=True,
                xsl_filename="as-handed-down.xsl",
                query=query,
            )

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy"))

            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
