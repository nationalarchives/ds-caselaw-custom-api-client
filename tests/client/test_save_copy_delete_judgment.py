import json
import os
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient


class TestSaveCopyDeleteJudgment(unittest.TestCase):
    def test_save_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            client.save_judgment_xml(uri, judgment_xml, "my annotation")

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "update_judgment.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_save_locked_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = judgment_str.encode("utf-8")
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "update_locked_judgment.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_insert_judgment_xml(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My new judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "",
            }
            client.insert_judgment_xml(uri, judgment_xml)

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "insert_judgment.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_delete_document(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            client.delete_judgment(uri)

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "delete_judgment.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_copy_judgment(self):
        client = MarklogicApiClient("", "", "", False)

        with patch.object(client, "eval"):
            old_uri = "/judgment/old_uri"
            new_uri = "/judgment/new_uri"
            expected_vars = {
                "old_uri": "/judgment/old_uri.xml",
                "new_uri": "/judgment/new_uri.xml",
            }
            client.copy_judgment(old_uri, new_uri)

            assert client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "copy_judgment.xqy")
            )
            assert client.eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
