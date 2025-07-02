import datetime
import json
import os
from unittest.mock import Mock, PropertyMock, patch

import pytest
import time_machine

from caselawclient.factories import JudgmentFactory
from caselawclient.models.documents import (
    CannotEnrichUnenrichableDocument,
    CannotPublishUnpublishableDocument,
    Document,
    DocumentNotSafeForDeletion,
    DocumentURIString,
)
from caselawclient.models.identifiers.collection import IdentifiersCollection
from caselawclient.models.identifiers.exceptions import IdentifierValidationException
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier
from caselawclient.models.judgments import Judgment
from caselawclient.models.neutral_citation_mixin import NeutralCitationString
from caselawclient.types import SuccessFailureMessageTuple


class TestDocumentSaveIdentifiers:
    def test_document_save_identifiers(self, mock_api_client):
        """
        given a particular Document with a known value of Identifiers (probably mock this out tbh)
        when I call document.save_identifiers() it
        validates that the identifiers meet constraints using `perform_all_validations` and
        calls set_property_as_node with expected values (edited)
        """
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.identifiers = Mock(autospec=IdentifiersCollection)
        document.identifiers.as_etree = "fake_node"

        document.identifiers.perform_all_validations.return_value = SuccessFailureMessageTuple(True, [])

        document.save_identifiers()
        document.identifiers.perform_all_validations.assert_called_once_with(
            document_type=Document, api_client=mock_api_client
        )
        mock_api_client.set_property_as_node.assert_called_with("test/1234", "identifiers", "fake_node")

    def test_document_save_identifiers_raises_exception_on_validation_failure(self, mock_api_client):
        """
        Check that if validating identifiers at save time fails then an exception is raised and the save is not performed
        """
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.identifiers = Mock(autospec=IdentifiersCollection)
        document.identifiers.as_etree = "fake_node"

        document.identifiers.perform_all_validations.return_value = SuccessFailureMessageTuple(
            False, ["Validation message one", "Validation message two"]
        )

        with pytest.raises(
            IdentifierValidationException,
            match="Unable to save identifiers; validation constraints not met: Validation message one, Validation message two",
        ):
            document.save_identifiers()
            document.identifiers.perform_all_validations.assert_called_once_with(
                document_type=Document, api_client=mock_api_client
            )
            mock_api_client.set_property_as_node.assert_not_called


class TestDocumentPublish:
    def test_publish_fails_if_not_publishable(self, mock_api_client):
        with pytest.raises(CannotPublishUnpublishableDocument):
            document = Document(DocumentURIString("test/1234"), mock_api_client)
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
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_publishable = True
        document.publish()
        mock_publish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", True)
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234",
            status="publish",
        )
        mock_enrich.assert_called_once()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish_assigns_new_fclid(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_publishable = True
        mock_api_client.get_next_document_sequence_number.return_value = 123
        document.publish()

        assert len(document.identifiers.of_type(FindCaseLawIdentifier)) == 1
        assert [identifier.value for identifier in document.identifiers.of_type(FindCaseLawIdentifier)][0] == "z27xcnhr"

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish_only_assigns_new_fclid_if_none_present(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_publishable = True
        document.identifiers.add(FindCaseLawIdentifier(value="tn4t35ts"))
        mock_api_client.get_next_document_sequence_number.return_value = 123
        document.publish()

        assert len(document.identifiers.of_type(FindCaseLawIdentifier)) == 1
        assert [identifier.value for identifier in document.identifiers.of_type(FindCaseLawIdentifier)][0] == "tn4t35ts"


class TestDocumentUnpublish:
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.unpublish_documents")
    def test_unpublish(
        self,
        mock_unpublish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.unpublish()
        mock_unpublish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", False)
        mock_api_client.break_checkout.assert_called_once_with("test/1234")
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234",
            status="unpublish",
        )


class TestDocumentForceEnrich:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.can_enrich", new_callable=PropertyMock, return_value=True)
    def test_force_enrich(self, mock_can_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
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

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.can_enrich", new_callable=PropertyMock, return_value=False)
    def test_force_enrich_but_not_enrichable(self, mock_can_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.can_enrich = False
        with pytest.raises(CannotEnrichUnenrichableDocument):
            document.force_enrich()

        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "last_sent_to_enrichment",
            "1955-11-05T06:00:00+00:00",
        )

        mock_announce_document_event.assert_not_called()


class TestDocumentEnrich:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.can_enrich", new_callable=PropertyMock, return_value=False)
    def test_enrich_but_not_enrichable(self, mock_can_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.can_enrich = False
        with pytest.raises(CannotEnrichUnenrichableDocument):
            document.enrich()

        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "last_sent_to_enrichment",
            "1955-11-05T06:00:00+00:00",
        )

        mock_announce_document_event.assert_not_called()

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.can_enrich", new_callable=PropertyMock, return_value=False)
    def test_enrich_of_unenrichable_but_exception_ignored(
        self, mock_can_enrich, mock_announce_document_event, mock_api_client
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.can_enrich = False
        document.enrich(accept_failures=True)

        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "last_sent_to_enrichment",
            "1955-11-05T06:00:00+00:00",
        )

        mock_announce_document_event.assert_not_called()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_enrich_not_recently_enriched(self, mock_force_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.enriched_recently = False

        result = document.enrich()

        assert result is True
        mock_force_enrich.assert_called_once()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_enrich_recently_enriched(self, mock_force_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.enriched_recently = True

        result = document.enrich()

        assert result is False
        mock_force_enrich.assert_not_called()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_enrich_recently_enriched_but_ignore_it(
        self, mock_force_enrich, mock_announce_document_event, mock_api_client
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.enriched_recently = True

        result = document.enrich(even_if_recent=True)

        assert result is True
        mock_force_enrich.assert_called_once()


class TestDocumentHold:
    def test_hold(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.hold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "editor-hold",
            "true",
        )

    def test_unhold(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.unhold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "editor-hold",
            "false",
        )


class TestDocumentDelete:
    def test_not_safe_to_delete_if_published(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_published = True

        assert document.safe_to_delete is False

    def test_safe_to_delete_if_unpublished(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_published = False

        assert document.safe_to_delete is True

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_safe(self, mock_aws_delete_documents, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = True

        document.delete()

        mock_api_client.delete_judgment.assert_called_once_with("test/1234")
        mock_aws_delete_documents.assert_called_once_with("test/1234")

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_unsafe(self, mock_aws_delete_documents, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
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
        document = Judgment(DocumentURIString("test/2023/123"), mock_api_client)

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
        document = Judgment(DocumentURIString("test/2023/123"), mock_api_client)

        document.neutral_citation = NeutralCitationString("[2023] Test 123")
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
        document = JudgmentFactory().build(api_client=mock_api_client)
        document.can_reparse = False
        assert document.reparse() is False
        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "2015-10-21T16:29:00+00:00",
        )

    @time_machine.travel(datetime.datetime(2015, 10, 21, 16, 29))
    def test_reparse_sets_last_sent_if_docx(self, mock_api_client):
        document = JudgmentFactory().build(api_client=mock_api_client)
        document.can_reparse = True

        # Patch force_reparse so we don't actually try to call boto here
        with patch.object(Document, "force_reparse"):
            assert document.reparse() is True

        # set_property is only called once because document.force_reparse isn't real
        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123",
            "last_sent_to_parser",
            "2015-10-21T16:29:00+00:00",
        )
