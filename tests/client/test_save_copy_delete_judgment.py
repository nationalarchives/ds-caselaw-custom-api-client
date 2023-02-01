import json
import os
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

import pytest

import src.caselawclient.Client
from src.caselawclient.Client import ROOT_DIR, MarklogicApiClient
from src.caselawclient.errors import InvalidContentHashError


class TestSaveCopyDeleteJudgment(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_save_judgment_xml(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            self.client.save_judgment_xml(uri, judgment_xml, "my annotation")

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "update_judgment.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_save_locked_judgment_xml(self):
        with patch.object(src.caselawclient.Client, "validate_content_hash"):
            with patch.object(self.client, "eval"):
                uri = "/ewca/civ/2004/632"
                judgment_str = "<root>My updated judgment</root>"
                judgment_xml = judgment_str.encode("utf-8")
                expected_vars = {
                    "uri": "/ewca/civ/2004/632.xml",
                    "judgment": judgment_str,
                    "annotation": "my annotation",
                }
                self.client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

                assert self.client.eval.call_args.args[0] == (
                    os.path.join(ROOT_DIR, "xquery", "update_locked_judgment.xqy")
                )
                assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                    expected_vars
                )

    def test_save_locked_judgment_xml_checks_content_hash(self):
        with patch.object(src.caselawclient.Client, "validate_content_hash"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = judgment_str.encode("utf-8")
            src.caselawclient.Client.validate_content_hash.side_effect = (
                InvalidContentHashError()
            )
            with pytest.raises(InvalidContentHashError):
                self.client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

    def test_insert_judgment_xml(self):
        with patch.object(self.client, "eval"):
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My new judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "",
            }
            self.client.insert_judgment_xml(uri, judgment_xml)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "insert_judgment.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_delete_document(self):
        with patch.object(self.client, "eval"):
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            self.client.delete_judgment(uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "delete_judgment.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )

    def test_copy_judgment(self):
        with patch.object(self.client, "eval"):
            old_uri = "/judgment/old_uri"
            new_uri = "/judgment/new_uri"
            expected_vars = {
                "old_uri": "/judgment/old_uri.xml",
                "new_uri": "/judgment/new_uri.xml",
            }
            self.client.copy_judgment(old_uri, new_uri)

            assert self.client.eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "copy_judgment.xqy")
            )
            assert self.client.eval.call_args.kwargs["vars"] == json.dumps(
                expected_vars
            )
