import json
import unittest
from unittest.mock import patch

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import MarklogicResourceUnmanagedError, MarklogicResourceVersionInvalidError
from caselawclient.models.documents import DocumentURIString
from caselawclient.models.documents.versions import VersionAnnotation, VersionType


class TestRestoreDocument(unittest.TestCase):
    def setUp(self):
        self.client = MarklogicApiClient(
            host="",
            username="",
            password="",
            use_https=False,
            user_agent="marklogic-api-client-test",
        )

    def test_restore_document_calls_correct_xquery(self):
        """
        Given a document URI and a version number,
        When `Client.restore_document` is called,
        Then the xquery in `restore_version.xqy` is called on the MarkLogic db.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            uri = DocumentURIString("test/1234")
            self.client.restore_document(uri, 3)

            assert mock_send_to_eval.call_args.args[1] == "restore_version.xqy"

    def test_restore_document_sends_correct_vars_default_annotation(self):
        """
        Given a document URI and a version number,
        When `Client.restore_document` is called with no annotation,
        Then the correct vars are passed to the xquery, with a default restore annotation.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            uri = DocumentURIString("test/1234")
            version_number = 3
            expected_vars = {
                "uri": "/test/1234.xml",
                "version_number": version_number,
                "annotation": json.dumps(
                    {
                        "type": "restore",
                        "calling_function": "restore_document",
                        "calling_agent": "marklogic-api-client-test",
                        "automated": True,
                        "message": "Restored from version 3",
                        "payload": {"restored_from_version": 3},
                    }
                ),
            }
            self.client.restore_document(uri, version_number)

            assert mock_send_to_eval.call_args.args[0] == expected_vars

    def test_restore_document_sends_correct_vars_with_provided_annotation(self):
        """
        Given a document URI, version number, and custom annotation,
        When `Client.restore_document` is called,
        Then the provided annotation is sent with restored_from_version attached.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            uri = DocumentURIString("test/1234")
            version_number = 5
            annotation = VersionAnnotation(
                VersionType.RESTORE,
                automated=False,
                message="Restored from version 3",
                payload={"test-key": "test-value"},
            )
            annotation.set_calling_function("test-caller")
            annotation.set_calling_agent("test-agent")
            expected_vars = {
                "uri": "/test/1234.xml",
                "version_number": version_number,
                "annotation": json.dumps(
                    {
                        "type": "restore",
                        "calling_function": "test-caller",
                        "calling_agent": "test-agent",
                        "automated": False,
                        "message": "Restored from version 3",
                        "payload": {
                            "test-key": "test-value",
                            "restored_from_version": version_number,
                        },
                    }
                ),
            }
            self.client.restore_document(uri, version_number, annotation=annotation)

            assert mock_send_to_eval.call_args.args[0] == expected_vars

    def test_restore_document_returns_eval_response(self):
        """
        Given a successful call to `_send_to_eval`,
        When `Client.restore_document` is called,
        Then the response from `_send_to_eval` is returned.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            uri = DocumentURIString("test/1234")
            result = self.client.restore_document(uri, 2)

            assert result == mock_send_to_eval.return_value

    def test_restore_document_raises_if_version_does_not_exist(self):
        """
        Given a version number that does not exist (MarkLogic: DLS-INVALIDVERSION),
        When `Client.restore_document` is called,
        Then a MarklogicResourceVersionInvalidError is raised.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            mock_send_to_eval.side_effect = MarklogicResourceVersionInvalidError
            uri = DocumentURIString("test/1234")
            with pytest.raises(MarklogicResourceVersionInvalidError):
                self.client.restore_document(uri, 99)

    def test_restore_document_raises_if_document_is_unmanaged(self):
        """
        Given a document URI that is not DLS-managed (MarkLogic: DLS-UNMANAGED),
        When `Client.restore_document` is called,
        Then a MarklogicResourceUnmanagedError is raised.
        """
        with patch.object(self.client, "_send_to_eval") as mock_send_to_eval:
            mock_send_to_eval.side_effect = MarklogicResourceUnmanagedError
            uri = DocumentURIString("test/1234")
            with pytest.raises(MarklogicResourceUnmanagedError):
                self.client.restore_document(uri, 3)
