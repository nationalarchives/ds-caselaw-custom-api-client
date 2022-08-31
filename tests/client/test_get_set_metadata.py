import json
import os
import unittest
from unittest.mock import patch

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestGetSetMetadata(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_get_judgment_citation(self):
        with patch.object(self.client, "eval"):
            uri = "judgment/uri"
            expected_vars = {"uri": "/judgment/uri.xml"}
            self.client.get_judgment_citation(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "get_metadata_citation.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

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
