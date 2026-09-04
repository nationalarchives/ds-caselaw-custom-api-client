"""Tests for Document.save() method."""

from datetime import UTC, datetime
from unittest.mock import ANY, patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents import DocumentURIString
from caselawclient.models.documents.exceptions import DocumentAlreadyExistsError, DocumentNotPersistedError
from caselawclient.models.documents.metadata.fields.exceptions import MetadataFieldValidationException
from caselawclient.models.documents.metadata.fields.field import MetadataField
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.models.documents.metadata.materialisation import (
    CURRENT_METADATA_MATERIALISATION_VERSION,
    LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY,
)
from caselawclient.models.documents.versions import VersionAnnotation, VersionType
from caselawclient.models.identifiers.exceptions import IdentifierValidationException
from caselawclient.models.judgments import Judgment
from caselawclient.types import SuccessFailureMessageTuple


@pytest.fixture(autouse=True)
def document_does_not_exist_in_marklogic(mock_api_client):
    mock_api_client.document_exists.return_value = False


class TestDocumentSave:
    """Tests for the Document.save() method."""

    def test_save_calls_update_document_xml(self):
        """Test that save() calls update_document_xml exactly once."""
        uri = DocumentURIString("test/2023/101")
        document = JudgmentFactory.build(uri=uri)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document, "_convert_body_claims_to_structured_metadata"),
            patch.object(document, "_validate_metadata_for_save"),
            patch.object(document, "_validate_identifiers_for_save"),
            patch.object(document, "_save_identifiers_to_marklogic"),
            patch.object(document, "_save_structured_metadata_to_marklogic") as mock_save_metadata,
        ):
            document.save(message="Changed document")

            mock_update.assert_called_once()
            mock_save_metadata.assert_called_once()

    def test_save_creates_edit_annotation(self):
        """Test that save() creates an EDIT annotation with automated=False."""
        uri = DocumentURIString("test/2023/123")
        document = JudgmentFactory.build(uri=uri)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document, "_convert_body_claims_to_structured_metadata"),
            patch.object(document, "_validate_metadata_for_save"),
            patch.object(document, "_validate_identifiers_for_save"),
            patch.object(document, "_save_identifiers_to_marklogic"),
            patch.object(document, "_save_structured_metadata_to_marklogic"),
        ):
            document.save(message="Changed document")

            call_args = mock_update.call_args
            annotation = call_args[0][2]
            assert isinstance(annotation, VersionAnnotation)
            assert annotation.version_type == VersionType.EDIT
            assert annotation.automated is False

    def test_save_passes_uri_and_xml_to_api(self):
        """Test that save() passes the correct URI and XML to the API."""
        uri = DocumentURIString("test/2023/456")
        document = JudgmentFactory.build(uri=uri)
        expected_xml = document.body.content_as_xml_tree

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document, "_convert_body_claims_to_structured_metadata"),
            patch.object(document, "_validate_metadata_for_save"),
            patch.object(document, "_validate_identifiers_for_save"),
            patch.object(document, "_save_identifiers_to_marklogic"),
            patch.object(document, "_save_structured_metadata_to_marklogic"),
        ):
            document.save(message="Changed document")

            call_args = mock_update.call_args
            assert call_args[0][0] == uri
            assert call_args[0][1] is expected_xml

    def test_save_with_message_includes_message_in_annotation(self):
        """Test that save() includes the message in the annotation."""
        uri = DocumentURIString("test/2023/789")
        document = JudgmentFactory.build(uri=uri)
        test_message = "Fixed typo in court name"

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document, "_convert_body_claims_to_structured_metadata"),
            patch.object(document, "_validate_metadata_for_save"),
            patch.object(document, "_validate_identifiers_for_save"),
            patch.object(document, "_save_identifiers_to_marklogic"),
            patch.object(document, "_save_structured_metadata_to_marklogic"),
        ):
            document.save(message=test_message)

            call_args = mock_update.call_args
            annotation = call_args[0][2]
            assert annotation.message == test_message

    def test_save_validates_and_converts_before_xml_update(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client)
        call_order: list[str] = []

        def track_xml(*_args, **_kwargs):
            call_order.append("xml")

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml", side_effect=track_xml),
            patch.object(
                document,
                "_convert_body_claims_to_structured_metadata",
                side_effect=lambda: call_order.append("convert"),
            ),
            patch.object(
                document,
                "_validate_metadata_for_save",
                side_effect=lambda: call_order.append("validate_metadata"),
            ),
            patch.object(
                document,
                "_validate_identifiers_for_save",
                side_effect=lambda: call_order.append("validate_identifiers"),
            ),
            patch.object(
                document,
                "_save_identifiers_to_marklogic",
                side_effect=lambda: call_order.append("save_identifiers"),
            ),
            patch.object(
                document,
                "_save_structured_metadata_to_marklogic",
                side_effect=lambda: call_order.append("save_metadata"),
            ),
        ):
            document.save(message="Changed document")

        assert call_order == [
            "convert",
            "validate_metadata",
            "validate_identifiers",
            "xml",
            "save_identifiers",
            "save_metadata",
        ]

    def test_save_writes_identifiers_and_structured_metadata_to_marklogic(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml"),
        ):
            document.save(message="Changed document")

        mock_api_client.set_property_as_node.assert_any_call(document.uri, "identifiers", ANY)
        mock_api_client.set_property_as_node.assert_any_call(document.uri, "metadata_fields", ANY)
        mock_api_client.set_property.assert_any_call(
            document.uri,
            LATEST_METADATA_MATERIALISATION_VERSION_PROPERTY,
            CURRENT_METADATA_MATERIALISATION_VERSION,
        )

    def test_save_rejects_invalid_identifiers_before_insert(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        with (
            patch.object(
                document.identifiers,
                "perform_all_validations",
                return_value=SuccessFailureMessageTuple(False, ["Identifier validation failed"]),
            ),
            patch.object(document.api_client, "insert_document_xml") as mock_insert,
            pytest.raises(IdentifierValidationException, match="Identifier validation failed"),
        ):
            document.save(message="Initial insert")

        mock_insert.assert_not_called()
        assert document.is_persisted is False

    def test_save_insert_path_for_ephemeral_document(self, mock_api_client):
        body = DocumentBodyFactory.build()
        document = Judgment.from_xml(body, mock_api_client, uri=DocumentURIString("d-new-doc"))
        mock_api_client.document_exists.return_value = False

        with patch.object(document.api_client, "insert_document_xml") as mock_insert:
            document.save(message="Initial insert")

        mock_insert.assert_called_once()
        call_args = mock_insert.call_args
        assert call_args[0][2] is Judgment
        assert document.is_persisted is True

    def test_save_raises_when_unpersisted_and_uri_already_exists(self, mock_api_client):
        document = Judgment.from_xml(
            DocumentBodyFactory.build(),
            mock_api_client,
            uri=DocumentURIString("d-new-doc"),
        )
        mock_api_client.document_exists.return_value = True

        with pytest.raises(DocumentAlreadyExistsError, match="already exists"):
            document.save(message="Initial insert")

    def test_save_rejects_mismatched_metadata_field_keys_before_insert(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)
        field_id = str(uuid4())
        document.metadata_fields["wrong-key"] = MetadataField(
            name="title",
            value="Bad key",
            source=MetadataSource.EDITOR,
            id=field_id,
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )

        with (
            patch.object(document.api_client, "insert_document_xml") as mock_insert,
            pytest.raises(MetadataFieldValidationException, match="wrong-key"),
        ):
            document.save(message="Initial insert")

        mock_insert.assert_not_called()
        assert document.is_persisted is False

    def test_is_persisted_false_after_from_xml(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        assert document.is_persisted is False

    def test_is_persisted_true_after_save(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)
        mock_api_client.document_exists.return_value = False

        with patch.object(document.api_client, "insert_document_xml"):
            document.save(message="Initial insert")

        assert document.is_persisted is True

    def test_is_persisted_true_on_init(self, mock_api_client):
        mock_api_client.document_exists.return_value = True
        mock_api_client.get_judgment_xml_bytestring.return_value = DocumentBodyFactory.build().content_as_xml.encode(
            "utf-8"
        )

        document = Judgment(DocumentURIString("test/2023/999"), mock_api_client)

        assert document.is_persisted is True

    def test_publish_on_ephemeral_raises(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        with pytest.raises(DocumentNotPersistedError):
            document.publish()

    def test_save_passes_custom_version_type_and_automated(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document, "_convert_body_claims_to_structured_metadata"),
            patch.object(document, "_validate_metadata_for_save"),
            patch.object(document, "_validate_identifiers_for_save"),
            patch.object(document, "_save_identifiers_to_marklogic"),
            patch.object(document, "_save_structured_metadata_to_marklogic"),
        ):
            document.save(
                message="Re-parsed",
                version_type=VersionType.SUBMISSION,
                automated=True,
            )

        annotation = mock_update.call_args[0][2]
        assert annotation.version_type == VersionType.SUBMISSION
        assert annotation.automated is True

    def test_partial_save_failure_leaves_document_persisted_after_insert(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)
        mock_api_client.document_exists.return_value = False

        with (
            patch.object(document.api_client, "insert_document_xml"),
            patch.object(
                document,
                "_save_structured_metadata_to_marklogic",
                side_effect=RuntimeError("metadata save failed"),
            ),
            pytest.raises(RuntimeError, match="metadata save failed"),
        ):
            document.save(message="Initial insert")

        assert document.is_persisted is True

    def test_save_retry_after_metadata_persist_failure_uses_update_path(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)
        mock_api_client.document_exists.return_value = False

        with (
            patch.object(document.api_client, "insert_document_xml"),
            patch.object(
                document,
                "_save_structured_metadata_to_marklogic",
                side_effect=RuntimeError("metadata save failed"),
            ),
            pytest.raises(RuntimeError, match="metadata save failed"),
        ):
            document.save(message="Initial insert")

        mock_api_client.document_exists.return_value = True

        with (
            patch.object(document.api_client, "update_document_xml") as mock_update,
            patch.object(document.api_client, "insert_document_xml") as mock_insert,
        ):
            document.save(message="Retry save")

        mock_update.assert_called_once()
        mock_insert.assert_not_called()
        assert document.is_persisted is True

    def test_reparse_body_swap_retains_existing_metadata_fields(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client)
        existing_claim = MetadataField(
            name="title",
            value="Existing editor title",
            source=MetadataSource.EDITOR,
            id="existing-claim-id",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
        )
        document.metadata_fields.add(existing_claim)

        document.body = DocumentBodyFactory.build(name="Updated title")

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml"),
        ):
            document.save(message="Re-parsed body")

        assert existing_claim in document.metadata_fields.values()
        title_claims = document.metadata_fields.by_name("title")
        assert any(claim.source is MetadataSource.EDITOR for claim in title_claims)
        assert any(claim.source is MetadataSource.DOCUMENT for claim in title_claims)
