import datetime
import json
import os
from unittest.mock import ANY, Mock, PropertyMock, call, patch

import pytest
import time_machine

from caselawclient.errors import MarklogicResourceVersionInvalidError
from caselawclient.factories import JudgmentFactory
from caselawclient.models.documents import (
    CannotEnrichUnenrichableDocument,
    CannotPublishUnpublishableDocument,
    CannotRestoreDocumentWithoutConsignmentReference,
    CannotRestorePublishedDocument,
    Document,
    DocumentNotSafeForDeletion,
    DocumentURIString,
)
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
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

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish_sets_first_published_date_if_unset(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_publishable = True
        document.first_published_datetime = None
        document.publish()

        mock_api_client.set_datetime_property.assert_called_once_with(
            "test/1234", "first_published_datetime", datetime.datetime(1955, 11, 5, 6, 0, tzinfo=datetime.timezone.utc)
        )

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish_does_not_set_first_published_date_if_already_set(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_publishable = True
        document.first_published_datetime = datetime.datetime(
            2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc
        )
        document.publish()

        mock_api_client.set_datetime_property.assert_not_called()


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
        with pytest.raises(CannotEnrichUnenrichableDocument):
            document.force_enrich()

        mock_api_client.set_property.assert_called_once_with(
            "test/1234",
            "last_sent_to_enrichment",
            "1955-11-05T06:00:00+00:00",
        )

        mock_announce_document_event.assert_not_called()


class TestDocumentCanEnrich:
    @patch("caselawclient.models.documents.DocumentBody.has_content", new_callable=PropertyMock, return_value=True)
    def test_can_enrich_true_when_has_content(self, mock_has_content, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.can_enrich is True

    @patch("caselawclient.models.documents.DocumentBody.has_content", new_callable=PropertyMock, return_value=False)
    def test_can_enrich_false_when_no_content(self, mock_has_content, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.can_enrich is False


class TestDocumentEnrich:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.Document.can_enrich", new_callable=PropertyMock, return_value=False)
    def test_enrich_but_not_enrichable(self, mock_can_enrich, mock_announce_document_event, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
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

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.utilities.aws.create_sns_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"REPARSE_SNS_TOPIC": "MY_TOPIC"})
    def test_force_reparse_base_document(self, sns, mock_api_client):
        document = Document(DocumentURIString("test/2023/123"), mock_api_client)
        document.consignment_reference = "TDR-12345"

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


_MISSING_PAYLOAD = object()


def _make_tdr_payload(
    organisation: str,
    contact_name: str,
    contact_email: str,
    sender_identifier: str,
    completed_at: str,
    extra_tre_raw_metadata: dict | None = None,
    source_filename: str | None = None,
    images: list[str] | None = None,
):
    payload: dict = {
        "tre_raw_metadata": {
            "parameters": {
                "TDR": {
                    "Source-Organization": organisation,
                    "Contact-Name": contact_name,
                    "Contact-Email": contact_email,
                    "Internal-Sender-Identifier": sender_identifier,
                    "Consignment-Completed-Datetime": completed_at,
                },
            }
        }
    }
    if source_filename is not None or images is not None:
        payload["tre_raw_metadata"]["parameters"]["TRE"] = {
            "payload": {
                "filename": source_filename,
                "images": images or [],
            }
        }
    if extra_tre_raw_metadata:
        payload["tre_raw_metadata"].update(extra_tre_raw_metadata)
    return payload


def _make_version_document(
    version_number: int,
    annotation_type: str = "submission",
    payload: dict | None | object = _MISSING_PAYLOAD,
):
    version_document = Mock(spec=Document)
    version_document.version_number = version_number
    structured_annotation: dict[str, object] = {"type": annotation_type}
    if payload is not _MISSING_PAYLOAD:
        structured_annotation["payload"] = payload
    version_document.structured_annotation = structured_annotation
    return version_document


def _assert_tdr_metadata_set(
    mock_api_client, organisation: str, contact_name: str, contact_email: str, sender_id: str, completed_at: str
):
    mock_api_client.set_property.assert_has_calls(
        [
            call("test/1234", name="source-organisation", value=organisation),
            call("test/1234", name="source-name", value=contact_name),
            call("test/1234", name="source-email", value=contact_email),
            call("test/1234", name="transfer-consignment-reference", value=sender_id),
            call("test/1234", name="transfer-received-at", value=completed_at),
        ]
    )
    assert mock_api_client.set_property.call_count == 5


# Reusable consignment metadata so restores have the consignment reference now required to proceed.
_STANDARD_TRE_RAW_METADATA = {
    "parameters": {
        "TDR": {
            "Source-Organization": "Example Organisation",
            "Contact-Name": "Example Contact",
            "Contact-Email": "contact@example.com",
            "Internal-Sender-Identifier": "TDR-12345",
            "Consignment-Completed-Datetime": "2026-01-01T12:00:00Z",
        }
    }
}


def _standard_tdr_payload(**extra: object) -> dict:
    payload = _make_tdr_payload(
        "Example Organisation",
        "Example Contact",
        "contact@example.com",
        "TDR-12345",
        "2026-01-01T12:00:00Z",
    )
    payload.update(extra)
    return payload


class TestAssertIsRestorable:
    @pytest.fixture(autouse=True)
    def unpublished_document(self, mock_api_client):
        mock_api_client.get_published.return_value = False

    def test_raises_if_published(self, mock_api_client):
        mock_api_client.get_published.return_value = True
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with pytest.raises(CannotRestorePublishedDocument):
            document.assert_is_restorable(3)

    def test_raises_without_consignment_reference_when_no_metadata_source_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(Document, "versions_as_documents", new_callable=PropertyMock, return_value=[]),
            pytest.raises(CannotRestoreDocumentWithoutConsignmentReference),
        ):
            document.assert_is_restorable(3)

    @pytest.mark.parametrize("payload", [{}, {"tre_raw_metadata": None}, {"tre_raw_metadata": {}}])
    def test_raises_without_consignment_reference_when_metadata_lacks_tdr(self, mock_api_client, payload):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(3, payload=payload)],
            ),
            pytest.raises(CannotRestoreDocumentWithoutConsignmentReference),
        ):
            document.assert_is_restorable(3)

    def test_passes_for_unpublished_document_with_consignment_reference(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with patch.object(
            Document,
            "versions_as_documents",
            new_callable=PropertyMock,
            return_value=[_make_version_document(3, payload=_standard_tdr_payload())],
        ):
            assert document.assert_is_restorable(3) is None


class TestDocumentRestoreVersion:
    @pytest.fixture(autouse=True)
    def mock_restore_assets(self):
        with patch("caselawclient.models.documents.restore_assets_from_consignment_archive") as restore_assets:
            yield restore_assets

    @pytest.fixture(autouse=True)
    def unpublished_document(self, mock_api_client):
        # A document can only be restored when it is not currently published.
        mock_api_client.get_published.return_value = False

    def test_restore_version_calls_api_client(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with patch.object(
            Document,
            "versions_as_documents",
            new_callable=PropertyMock,
            return_value=[
                _make_version_document(
                    3,
                    payload=_standard_tdr_payload(submitter="user@example.com", other="should-not-be-removed"),
                )
            ],
        ):
            document.restore_version(3, automated=False)

        restore_call_args = mock_api_client.restore_document.call_args.args
        assert restore_call_args[0] == "test/1234"
        assert restore_call_args[1] == 3

        annotation = restore_call_args[2]
        assert isinstance(annotation, VersionAnnotation)
        assert annotation.version_type == VersionType.RESTORE
        assert annotation.automated is False
        assert annotation.message == "Restored from version 3"
        assert annotation.payload == {
            "submitter": "user@example.com",
            "other": "should-not-be-removed",
            "tre_raw_metadata": _STANDARD_TRE_RAW_METADATA,
        }
        assert annotation.calling_function == "restore_version"
        assert annotation.calling_agent == "marklogic-api-client-test"

    def test_restore_version_propagates_api_client_errors(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        mock_api_client.restore_document.side_effect = MarklogicResourceVersionInvalidError
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(3, payload=_standard_tdr_payload())],
            ),
            pytest.raises(MarklogicResourceVersionInvalidError),
        ):
            document.restore_version(3, automated=False)

    @pytest.mark.parametrize(
        "versions,target_version",
        [
            ([_make_version_document(1, payload={"test-key": "test-value"})], 99),
            ([], 1),
        ],
    )
    def test_restore_version_raises_if_version_number_not_found(self, mock_api_client, versions, target_version):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(Document, "versions_as_documents", new_callable=PropertyMock, return_value=versions),
            pytest.raises(ValueError, match=f"Version {target_version} not found"),
        ):
            document.restore_version(target_version, automated=False)

        mock_api_client.restore_document.assert_not_called()

    def test_restore_version_uses_previous_version_payload(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        payload = _standard_tdr_payload(
            submitter="user@example.com",
            **{"other-key-1": "other-value-1", "other-key-2": "other-value-2"},
        )
        with patch.object(
            Document,
            "versions_as_documents",
            new_callable=PropertyMock,
            return_value=[_make_version_document(7, payload=payload)],
        ):
            document.restore_version(7, automated=False)

        annotation = mock_api_client.restore_document.call_args.args[2]
        assert isinstance(annotation, VersionAnnotation)
        assert annotation.payload == {
            "submitter": "user@example.com",
            "other-key-1": "other-value-1",
            "other-key-2": "other-value-2",
            "tre_raw_metadata": _STANDARD_TRE_RAW_METADATA,
        }

    def test_restore_version_embeds_action_requested_by_in_payload(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with patch.object(
            Document,
            "versions_as_documents",
            new_callable=PropertyMock,
            return_value=[_make_version_document(3, payload=_standard_tdr_payload(other="value"))],
        ):
            document.restore_version(3, automated=False, action_requested_by="user@example.com")

        annotation = mock_api_client.restore_document.call_args.args[2]
        assert isinstance(annotation, VersionAnnotation)
        assert annotation.payload == {
            "other": "value",
            "tre_raw_metadata": _STANDARD_TRE_RAW_METADATA,
            "action_requested_by": "user@example.com",
        }

    def test_restore_version_omits_action_requested_by_when_not_provided(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with patch.object(
            Document,
            "versions_as_documents",
            new_callable=PropertyMock,
            return_value=[_make_version_document(3, payload=_standard_tdr_payload(other="value"))],
        ):
            document.restore_version(3, automated=False)

        annotation = mock_api_client.restore_document.call_args.args[2]
        assert isinstance(annotation, VersionAnnotation)
        assert annotation.payload is not None
        assert "action_requested_by" not in annotation.payload

    @pytest.mark.parametrize(
        "versions,target_version,expected_tdr",
        [
            (
                [
                    _make_version_document(
                        7,
                        payload=_make_tdr_payload(
                            "Example Organisation",
                            "Example Contact",
                            "contact@example.com",
                            "TDR-12345",
                            "2026-01-01T12:00:00Z",
                        ),
                    )
                ],
                7,
                ("Example Organisation", "Example Contact", "contact@example.com", "TDR-12345", "2026-01-01T12:00:00Z"),
            ),
            (
                [
                    _make_version_document(
                        7,
                        "not-a-submission",
                        _make_tdr_payload(
                            "Wrong Organisation",
                            "Wrong Contact",
                            "wrong@example.com",
                            "WRONG-12345",
                            "2025-01-01T12:00:00Z",
                        ),
                    ),
                    _make_version_document(
                        6,
                        payload=_make_tdr_payload(
                            "Correct Organisation",
                            "Correct Contact",
                            "correct@example.com",
                            "TDR-12345",
                            "2026-01-01T12:00:00Z",
                        ),
                    ),
                ],
                7,
                ("Correct Organisation", "Correct Contact", "correct@example.com", "TDR-12345", "2026-01-01T12:00:00Z"),
            ),
            (
                [
                    _make_version_document(4, "edit", payload={}),
                    _make_version_document(
                        3,
                        "restore",
                        _make_tdr_payload(
                            "Submission A Organisation",
                            "Submission A Contact",
                            "a@example.com",
                            "TDR-A",
                            "2026-01-01T12:00:00Z",
                        ),
                    ),
                    _make_version_document(
                        2,
                        payload=_make_tdr_payload(
                            "Submission B Organisation",
                            "Submission B Contact",
                            "b@example.com",
                            "TDR-B",
                            "2026-02-01T12:00:00Z",
                        ),
                    ),
                    _make_version_document(
                        1,
                        payload=_make_tdr_payload(
                            "Submission A Organisation",
                            "Submission A Contact",
                            "a@example.com",
                            "TDR-A",
                            "2026-01-01T12:00:00Z",
                        ),
                    ),
                ],
                3,
                ("Submission A Organisation", "Submission A Contact", "a@example.com", "TDR-A", "2026-01-01T12:00:00Z"),
            ),
        ],
    )
    def test_restore_version_sets_tdr_metadata_from_expected_source(
        self, mock_api_client, versions, target_version, expected_tdr
    ):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(Document, "versions_as_documents", new_callable=PropertyMock, return_value=versions),
            patch.object(document, "_initialise_document_body"),
        ):
            document.restore_version(target_version, automated=False)

        _assert_tdr_metadata_set(mock_api_client, *expected_tdr)

    def test_restore_version_reloads_document_body_after_restore(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(4, payload=_standard_tdr_payload())],
            ),
            patch.object(document, "_initialise_document_body") as initialise_document_body_mock,
        ):
            document.restore_version(4, automated=True)

        initialise_document_body_mock.assert_called_once_with()

    def test_restore_version_invalidates_cached_properties_when_tdr_metadata_is_set(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        mock_api_client.get_property.side_effect = ["old-contact", "new-contact"]
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.source_name == "old-contact"

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[
                    _make_version_document(
                        6,
                        payload=_make_tdr_payload(
                            "Example Organisation",
                            "Example Contact",
                            "contact@example.com",
                            "TDR-12345",
                            "2026-01-01T12:00:00Z",
                        ),
                    )
                ],
            ),
            patch.object(document, "_initialise_document_body"),
        ):
            document.restore_version(6, automated=False)

        assert document.source_name == "new-contact"
        assert mock_api_client.get_property.call_args_list == [
            call("test/1234", "source-name"),
            call("test/1234", "source-name"),
        ]

    def test_restore_version_preserves_full_tre_raw_metadata_from_metadata_source(self, mock_api_client):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[
                    _make_version_document(4, "edit", payload={}),
                    _make_version_document(
                        3,
                        annotation_type="restore",
                        payload=_make_tdr_payload(
                            "Example Organisation",
                            "Example Contact",
                            "contact@example.com",
                            "TDR-12345",
                            "2026-01-01T12:00:00Z",
                            extra_tre_raw_metadata={
                                "extra-tre-key-1": "extra-tre-value-1",
                                "extra-tre-key-2": {"example": True},
                            },
                        ),
                    ),
                ],
            ),
            patch.object(document, "_initialise_document_body"),
        ):
            document.restore_version(4, automated=False)

        mock_api_client.assert_has_calls(
            [
                call.set_property("test/1234", name="source-organisation", value="Example Organisation"),
                call.set_property("test/1234", name="source-name", value="Example Contact"),
                call.set_property("test/1234", name="source-email", value="contact@example.com"),
                call.set_property("test/1234", name="transfer-consignment-reference", value="TDR-12345"),
                call.set_property("test/1234", name="transfer-received-at", value="2026-01-01T12:00:00Z"),
                call.restore_document("test/1234", 4, ANY),
            ]
        )

        annotation = mock_api_client.restore_document.call_args.args[2]
        assert annotation.payload == {
            "tre_raw_metadata": {
                "parameters": {
                    "TDR": {
                        "Source-Organization": "Example Organisation",
                        "Contact-Name": "Example Contact",
                        "Contact-Email": "contact@example.com",
                        "Internal-Sender-Identifier": "TDR-12345",
                        "Consignment-Completed-Datetime": "2026-01-01T12:00:00Z",
                    }
                },
                "extra-tre-key-1": "extra-tre-value-1",
                "extra-tre-key-2": {"example": True},
            }
        }

    def test_restore_version_restores_s3_assets_using_tdr_consignment_reference(
        self, mock_api_client, mock_restore_assets
    ):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[
                    _make_version_document(
                        3,
                        payload=_make_tdr_payload(
                            "Example Organisation",
                            "Example Contact",
                            "contact@example.com",
                            "TDR-12345",
                            "2026-01-01T12:00:00Z",
                            source_filename="source.docx",
                            images=["image1.png"],
                        ),
                    ),
                ],
            ),
            patch.object(document, "_initialise_document_body"),
        ):
            document.restore_version(3, automated=False)

        mock_restore_assets.assert_called_once_with("test/1234", "TDR-12345", "source.docx", ["image1.png"])

    def test_restore_version_aborts_without_consignment_reference(self, mock_api_client, mock_restore_assets):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(3, payload={"other": "value"})],
            ),
            patch.object(document, "_initialise_document_body"),
            pytest.raises(CannotRestoreDocumentWithoutConsignmentReference),
        ):
            document.restore_version(3, automated=False)

        # Nothing should have been updated.
        mock_api_client.restore_document.assert_not_called()
        mock_api_client.set_property.assert_not_called()
        mock_restore_assets.assert_not_called()

    def test_restore_version_aborts_if_published(self, mock_api_client, mock_restore_assets):
        mock_api_client.user_agent = "marklogic-api-client-test"
        mock_api_client.get_published.return_value = True
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(3, payload=_standard_tdr_payload())],
            ),
            patch.object(document, "_initialise_document_body"),
            pytest.raises(CannotRestorePublishedDocument),
        ):
            document.restore_version(3, automated=False)

        # Nothing should have been updated.
        mock_api_client.restore_document.assert_not_called()
        mock_api_client.set_property.assert_not_called()
        mock_restore_assets.assert_not_called()

    def test_restore_version_does_not_restore_for_invalid_version(self, mock_api_client, mock_restore_assets):
        mock_api_client.user_agent = "marklogic-api-client-test"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(
                Document,
                "versions_as_documents",
                new_callable=PropertyMock,
                return_value=[_make_version_document(3, payload=_standard_tdr_payload())],
            ),
            pytest.raises(ValueError, match="Version 99 not found"),
        ):
            document.restore_version(99, automated=False)

        mock_api_client.restore_document.assert_not_called()
        mock_restore_assets.assert_not_called()

    def test_get_version_returns_matching_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        version_4 = _make_version_document(4)
        version_3 = _make_version_document(3)

        with patch.object(
            Document, "versions_as_documents", new_callable=PropertyMock, return_value=[version_4, version_3]
        ):
            assert document._get_version(3) is version_3  # noqa: SLF001
            assert document._get_version(99) is None  # noqa: SLF001

    @pytest.mark.parametrize(
        "versions,target_version,expected_version_number",
        [
            (
                [
                    _make_version_document(7, "not-submission"),
                    _make_version_document(6, "not-submission"),
                    _make_version_document(5, "submission"),
                    _make_version_document(4, "submission"),
                ],
                6,
                5,
            ),
            (
                [
                    _make_version_document(4, "edit"),
                    _make_version_document(3, "restore"),
                    _make_version_document(2, "submission"),
                    _make_version_document(1, "submission"),
                ],
                3,
                3,
            ),
            (
                [
                    _make_version_document(3, "not-submission"),
                    _make_version_document(2, "not-submission"),
                ],
                3,
                None,
            ),
        ],
    )
    def test_get_restore_metadata_source_version(
        self, mock_api_client, versions, target_version, expected_version_number
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with patch.object(Document, "versions_as_documents", new_callable=PropertyMock, return_value=versions):
            result = document._get_restore_metadata_source_version(target_version)  # noqa: SLF001

        if expected_version_number is None:
            assert result is None
        else:
            assert result is not None
            assert result.version_number == expected_version_number

    def test_set_tdr_metadata_sets_properties_and_invalidates_cached_values(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        mock_api_client.get_property.side_effect = [
            "old-source-name",
            "old-source-email",
            "old-consignment-reference",
            "new-source-name",
            "new-source-email",
            "new-consignment-reference",
        ]

        assert document.source_name == "old-source-name"
        assert document.source_email == "old-source-email"
        assert document.consignment_reference == "old-consignment-reference"

        document._set_tdr_metadata(  # noqa: SLF001
            {
                "Source-Organization": "Example Organisation",
                "Contact-Name": "Example Contact",
                "Contact-Email": "contact@example.com",
                "Internal-Sender-Identifier": "TDR-12345",
                "Consignment-Completed-Datetime": "2026-01-01T12:00:00Z",
            }
        )

        _assert_tdr_metadata_set(
            mock_api_client,
            "Example Organisation",
            "Example Contact",
            "contact@example.com",
            "TDR-12345",
            "2026-01-01T12:00:00Z",
        )

        assert document.source_name == "new-source-name"
        assert document.source_email == "new-source-email"
        assert document.consignment_reference == "new-consignment-reference"
