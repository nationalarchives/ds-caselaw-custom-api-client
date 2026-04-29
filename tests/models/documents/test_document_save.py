"""Tests for Document.save() method."""

from unittest.mock import patch

from caselawclient.factories import DocumentFactory
from caselawclient.models.documents import DocumentURIString
from caselawclient.models.documents.versions import VersionAnnotation, VersionType


class TestDocumentSave:
    """Tests for the Document.save() method."""

    def test_save_calls_update_document_xml(self):
        """Test that save() calls update_document_xml exactly once."""
        uri = DocumentURIString("test/2023/101")
        document = DocumentFactory.build(uri=uri)

        with patch.object(document.api_client, "update_document_xml") as mock_update:
            document.save(message="Changed document")

            mock_update.assert_called_once()

    def test_save_creates_edit_annotation(self):
        """Test that save() creates an EDIT annotation with automated=False."""
        uri = DocumentURIString("test/2023/123")
        document = DocumentFactory.build(uri=uri)

        with patch.object(document.api_client, "update_document_xml") as mock_update:
            document.save(message="Changed document")

            # Verify the annotation was created correctly
            call_args = mock_update.call_args
            annotation = call_args[0][2]
            assert isinstance(annotation, VersionAnnotation)
            assert annotation.version_type == VersionType.EDIT
            assert annotation.automated is False

    def test_save_passes_uri_and_xml_to_api(self):
        """Test that save() passes the correct URI and XML to the API."""
        uri = DocumentURIString("test/2023/456")
        document = DocumentFactory.build(uri=uri)
        expected_xml = document.body.content_as_xml_tree

        with patch.object(document.api_client, "update_document_xml") as mock_update:
            document.save(message="Changed document")

            # Verify the correct URI and XML are passed
            call_args = mock_update.call_args
            assert call_args[0][0] == uri
            assert call_args[0][1] is expected_xml

    def test_save_with_message_includes_message_in_annotation(self):
        """Test that save() includes the message in the annotation."""
        uri = DocumentURIString("test/2023/789")
        document = DocumentFactory.build(uri=uri)
        test_message = "Fixed typo in court name"

        with patch.object(document.api_client, "update_document_xml") as mock_update:
            document.save(message=test_message)

            call_args = mock_update.call_args
            annotation = call_args[0][2]
            assert annotation.message == test_message
