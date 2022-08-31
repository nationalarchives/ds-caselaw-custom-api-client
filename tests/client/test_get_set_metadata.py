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
                os.path.join(
                    ROOT_DIR, "xquery", "set_metadata_citation.xqy"
                )
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)