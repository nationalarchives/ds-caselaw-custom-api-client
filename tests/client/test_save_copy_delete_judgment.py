import json
import os
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

import pytest

import caselawclient.Client
from caselawclient.Client import ROOT_DIR, MarklogicApiClient
from caselawclient.errors import InvalidContentHashError


class TestSaveCopyDeleteJudgment(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient("", "", "", False)

    def test_save_judgment_xml(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "my annotation",
            }
            self.client.save_judgment_xml(uri, judgment_xml, "my annotation")

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "update_judgment.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_save_locked_judgment_xml(self):
        """
        Given a locked judgement uri, a judgement_xml and an annotation
        When `Client.save_locked_judgment_xml` is called with these as arguments
        Then the xquery in `update_locked_judgment.xqy` is called on the Marklogic db with those arguments
        """
        with patch.object(caselawclient.Client, "validate_content_hash"):
            with patch.object(self.client, "eval") as mock_eval:
                uri = "/ewca/civ/2004/632"
                judgment_str = "<root>My updated judgment</root>"
                judgment_xml = judgment_str.encode("utf-8")
                expected_vars = {
                    "uri": "/ewca/civ/2004/632.xml",
                    "judgment": judgment_str,
                    "annotation": "my annotation",
                }
                self.client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

                assert mock_eval.call_args.args[0] == (
                    os.path.join(ROOT_DIR, "xquery", "update_locked_judgment.xqy")
                )
                assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_save_locked_judgment_xml_checks_content_hash(self):
        """
        Given content hash validation will fail with an error
        When `Client.save_locked_judgment_xml` is called
        Then the error is raised.
        """
        with patch.object(
            caselawclient.Client, "validate_content_hash"
        ) as mock_validate_hash:
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = judgment_str.encode("utf-8")
            mock_validate_hash.side_effect = InvalidContentHashError()
            with pytest.raises(InvalidContentHashError):
                self.client.save_locked_judgment_xml(uri, judgment_xml, "my annotation")

    def test_insert_judgment_xml(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "/ewca/civ/2004/632"
            judgment_str = "<root>My new judgment</root>"
            judgment_xml = ElementTree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": "",
            }
            self.client.insert_judgment_xml(uri, judgment_xml)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "insert_judgment.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_delete_document(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = "/judgment/uri"
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            self.client.delete_judgment(uri)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "delete_judgment.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_copy_judgment(self):
        with patch.object(self.client, "eval") as mock_eval:
            old_uri = "/judgment/old_uri"
            new_uri = "/judgment/new_uri"
            expected_vars = {
                "old_uri": "/judgment/old_uri.xml",
                "new_uri": "/judgment/new_uri.xml",
            }
            self.client.copy_judgment(old_uri, new_uri)

            assert mock_eval.call_args.args[0] == (
                os.path.join(ROOT_DIR, "xquery", "copy_judgment.xqy")
            )
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
