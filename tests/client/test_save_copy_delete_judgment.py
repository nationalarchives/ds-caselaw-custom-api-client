import json
import os
import unittest
from unittest.mock import patch

import pytest
from lxml import etree

import caselawclient.Client
from caselawclient.Client import ROOT_DIR, MarklogicApiClient
from caselawclient.errors import InvalidContentHashError
from caselawclient.models.documents import DocumentURIString
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.judgments import Judgment


class TestSaveCopyDeleteJudgment(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient(
            host="",
            username="",
            password="",
            use_https=False,
            user_agent="marklogic-api-client-test",
        )

    def test_update_locked_document_xml(self):
        with (
            patch.object(caselawclient.Client, "validate_content_hash"),
            patch.object(self.client, "eval") as mock_eval,
        ):
            uri = DocumentURIString("ewca/civ/2004/632")
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = etree.fromstring(judgment_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "judgment": judgment_str,
                "annotation": json.dumps(
                    {
                        "type": "edit",
                        "calling_function": "update_locked_document_xml",
                        "calling_agent": "marklogic-api-client-test",
                        "automated": False,
                        "message": "test_update_locked_document_xml",
                        "payload": {"test_payload": True},
                    },
                ),
            }
            self.client.update_locked_document_xml(
                uri,
                judgment_xml,
                VersionAnnotation(
                    VersionType.EDIT,
                    message="test_update_locked_document_xml",
                    automated=False,
                    payload={"test_payload": True},
                ),
            )

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "update_locked_judgment.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_update_locked_document_xml_checks_content_hash(self):
        with patch.object(
            caselawclient.Client,
            "validate_content_hash",
        ) as mock_validate_hash:
            uri = DocumentURIString("ewca/civ/2004/632")
            judgment_str = "<root>My updated judgment</root>"
            judgment_xml = etree.fromstring(judgment_str)
            mock_validate_hash.side_effect = InvalidContentHashError()
            with pytest.raises(InvalidContentHashError):
                self.client.update_locked_document_xml(
                    uri,
                    judgment_xml,
                    VersionAnnotation(
                        VersionType.SUBMISSION,
                        message="test_update_locked_document_xml_checks_content_hash",
                        automated=False,
                        payload={"test_payload": True},
                    ),
                )

    def test_update_locked_document_xml_skips_content_hash_when_not_validating(self):
        with (
            patch.object(caselawclient.Client, "validate_content_hash") as mock_validate_hash,
            patch.object(self.client, "eval") as mock_eval,
        ):
            self.client.update_locked_document_xml(
                DocumentURIString("ewca/civ/2004/632"),
                etree.fromstring("<root>No hash here</root>"),
                VersionAnnotation(VersionType.EDIT, message="no hash", automated=False),
                validate_hash=False,
            )

            mock_validate_hash.assert_not_called()
            mock_eval.assert_called_once()

    def test_insert_document_xml(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("ewca/civ/2004/632")
            document_str = "<root>My judgment</root>"
            document_xml = etree.fromstring(document_str)
            expected_vars = {
                "uri": "/ewca/civ/2004/632.xml",
                "type_collection": "judgment",
                "document": document_str,
                "annotation": json.dumps(
                    {
                        "type": "submission",
                        "calling_function": "insert_document_xml",
                        "calling_agent": "marklogic-api-client-test",
                        "automated": False,
                        "message": "test_insert_document_xml",
                        "payload": {"test_payload": True},
                    },
                ),
            }
            self.client.insert_document_xml(
                document_uri=uri,
                document_xml=document_xml,
                document_type=Judgment,
                annotation=VersionAnnotation(
                    VersionType.SUBMISSION,
                    message="test_insert_document_xml",
                    automated=False,
                    payload={"test_payload": True},
                ),
            )

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "insert_document.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_delete_document(self):
        with patch.object(self.client, "eval") as mock_eval:
            uri = DocumentURIString("judgment/uri")
            expected_vars = {
                "uri": "/judgment/uri.xml",
            }
            self.client.delete_judgment(uri)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "delete_judgment.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)

    def test_copy_document(self):
        with patch.object(self.client, "eval") as mock_eval:
            old_uri = DocumentURIString("judgment/old_uri")
            new_uri = DocumentURIString("judgment/new_uri")
            expected_vars = {
                "old_uri": "/judgment/old_uri.xml",
                "new_uri": "/judgment/new_uri.xml",
            }
            self.client.copy_document(old_uri, new_uri)

            assert mock_eval.call_args.args[0] == (os.path.join(ROOT_DIR, "xquery", "copy_document.xqy"))
            assert mock_eval.call_args.kwargs["vars"] == json.dumps(expected_vars)
