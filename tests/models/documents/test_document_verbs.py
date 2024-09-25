import datetime
import json
import os
from unittest.mock import PropertyMock, patch

import pytest
import time_machine

from caselawclient.models.documents import (
    CannotPublishUnpublishableDocument,
    Document,
    DocumentNotSafeForDeletion,
)
from caselawclient.models.judgments import Judgment
from tests.factories import JudgmentFactory


class TestDocumentPublish:
    def test_publish_fails_if_not_publishable(self, mock_api_client):
        with pytest.raises(CannotPublishUnpublishableDocument):
            document = Document("test/1234", mock_api_client)
            document.is_publishable = False
            document.publish()
            mock_api_client.set_published.assert_not_called()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document("test/1234", mock_api_client)
        document.is_publishable = True
        document.publish()
        mock_publish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", True)
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234",
            status="publish",
        )
        mock_enrich.assert_called_once()


class TestDocumentUnpublish:
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.unpublish_documents")
    def test_unpublish(
        self,
        mock_unpublish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document("test/1234", mock_api_client)
        document.unpublish()
        mock_unpublish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", False)
        mock_api_client.break_checkout.assert_called_once_with("test/1234")
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234",
            status="unpublish",
        )


class TestDocumentEnrich:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    def test_force_enrich(self, mock_announce_document_event, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.force_enrich()

        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "last_sent_to_enrichment",
            "1955-11-05T06:00:00+00:00",
        )

        mock_announce_document_event.assert_called_once_with(
            uri="test/1234",
            status="enrich",
            enrich=True,
        )

    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_no_enrich_when_can_enrich_is_false(self, force_enrich, mock_api_client):
        document = Document("test/1234", mock_api_client)
        with patch.object(
            Document,
            "can_enrich",
            new_callable=PropertyMock,
        ) as can_enrich:
            can_enrich.return_value = False
            document.enrich()
            force_enrich.assert_not_called()

    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_enrich_when_can_enrich_is_true(self, force_enrich, mock_api_client):
        document = Document("test/1234", mock_api_client)
        with patch.object(
            Document,
            "can_enrich",
            new_callable=PropertyMock,
        ) as can_enrich:
            can_enrich.return_value = True
            document.enrich()
            force_enrich.assert_called()


class TestDocumentHold:
    def test_hold(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.hold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "editor-hold",
            "true",
        )

    def test_unhold(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.unhold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "editor-hold",
            "false",
        )


class TestDocumentDelete:
    def test_not_safe_to_delete_if_published(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_published = True

        assert document.safe_to_delete is False

    def test_safe_to_delete_if_unpublished(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_published = False

        assert document.safe_to_delete is True

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_safe(self, mock_aws_delete_documents, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.safe_to_delete = True

        document.delete()

        mock_api_client.delete_judgment.assert_called_once_with("test/1234")
        mock_aws_delete_documents.assert_called_once_with("test/1234")

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_unsafe(self, mock_aws_delete_documents, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.safe_to_delete = False

        with pytest.raises(DocumentNotSafeForDeletion):
            document.delete()

        mock_api_client.delete_judgment.assert_not_called()
        mock_aws_delete_documents.assert_not_called()


class TestReparse:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.utilities.aws.create_sns_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"REPARSE_SNS_TOPIC": "MY_TOPIC"})
    def test_force_reparse_empty(self, sns, mock_api_client):
        document = Judgment("test/2023/123", mock_api_client)

        document.consignment_reference = "TDR-12345"

        document.body.document_date_as_date = datetime.date(1001, 1, 1)

        document.force_reparse()

        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "1955-11-05T06:00:00+00:00",
        )

        # first call, second argument (the kwargs), so [0][1]
        returned_message = json.loads(
            sns.return_value.publish.call_args_list[0][1]["Message"],
        )
        # hide random parameters
        del returned_message["properties"]["timestamp"]
        del returned_message["properties"]["executionId"]

        assert returned_message == {
            "properties": {
                "messageType": "uk.gov.nationalarchives.da.messages.request.courtdocument.parse.RequestCourtDocumentParse",
                "function": "fcl-judgment-parse-request",
                "producer": "FCL",
                "parentExecutionId": None,
            },
            "parameters": {
                "s3Bucket": "MY_BUCKET",
                "s3Key": "test/2023/123/test_2023_123.docx",
                "reference": "TDR-12345",
                "originator": "FCL",
                "parserInstructions": {
                    "documentType": "judgment",
                    "metadata": {
                        "name": None,
                        "cite": None,
                        "court": None,
                        "date": None,
                        "uri": "test/2023/123",
                    },
                },
            },
        }

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.utilities.aws.create_sns_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"REPARSE_SNS_TOPIC": "MY_TOPIC"})
    def test_force_reparse_full(self, sns, mock_api_client):
        document = Judgment("test/2023/123", mock_api_client)

        document.neutral_citation = "[2023] Test 123"
        document.consignment_reference = "TDR-12345"

        document.body.name = "Judgment v Judgement"
        document.body.court = "Court of Testing"
        document.body.document_date_as_date = datetime.date(2023, 2, 3)

        document.force_reparse()

        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "1955-11-05T06:00:00+00:00",
        )

        # first call, second argument (the kwargs), so [0][1]
        returned_message = json.loads(
            sns.return_value.publish.call_args_list[0][1]["Message"],
        )
        # hide random parameters
        del returned_message["properties"]["timestamp"]
        del returned_message["properties"]["executionId"]

        assert returned_message == {
            "properties": {
                "messageType": "uk.gov.nationalarchives.da.messages.request.courtdocument.parse.RequestCourtDocumentParse",
                "function": "fcl-judgment-parse-request",
                "producer": "FCL",
                "parentExecutionId": None,
            },
            "parameters": {
                "s3Bucket": "MY_BUCKET",
                "s3Key": "test/2023/123/test_2023_123.docx",
                "reference": "TDR-12345",
                "originator": "FCL",
                "parserInstructions": {
                    "documentType": "judgment",
                    "metadata": {
                        "name": "Judgment v Judgement",
                        "cite": "[2023] Test 123",
                        "court": "Court of Testing",
                        "date": "2023-02-03",
                        "uri": "test/2023/123",
                    },
                },
            },
        }

    @time_machine.travel(datetime.datetime(2015, 10, 21, 16, 29))
    def test_reparse_sets_last_sent_if_no_docx(self, mock_api_client):
        document = JudgmentFactory().build(is_published=True)
        document.api_client = mock_api_client
        document.can_reparse = False
        assert Judgment.reparse(document) is False
        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "2015-10-21T16:29:00+00:00",
        )

    @time_machine.travel(datetime.datetime(2015, 10, 21, 16, 29))
    def test_reparse_sets_last_sent_if_docx(self, mock_api_client):
        document = JudgmentFactory().build(is_published=True)
        document.api_client = mock_api_client
        document.can_reparse = True
        assert Judgment.reparse(document) is True
        # set_property is only called once because document.reparse isn't real
        assert "Mock" in str(type(document.reparse))
        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "2015-10-21T16:29:00+00:00",
        )
