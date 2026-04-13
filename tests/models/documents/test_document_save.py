"""Unit tests for Document.save() method and mutation + save workflows."""

import warnings

import pytest

from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.documents.versions import VersionAnnotation, VersionType


class TestDocumentSave:
    """Tests for Document.save() method."""

    MINIMAL_DOCUMENT_XML = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
    <judgment name="decision">
        <meta>
            <identification>
                <FRBRWork>
                    <FRBRname value="Test Case"/>
                    <FRBRdate date="2020-01-01"/>
                </FRBRWork>
            </identification>
            <proprietary>
                <uk:court>Test Court</uk:court>
            </proprietary>
        </meta>
        <header><p>Header</p></header>
        <judgmentBody><decision><p>Content</p></decision></judgmentBody>
    </judgment>
</akomaNtoso>"""

    def test_save_calls_api_client_update_document_xml(self, mock_api_client):
        """Test that save() calls api_client.update_document_xml with correct parameters."""
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        doc.save()

        mock_api_client.update_document_xml.assert_called_once()
        call_args = mock_api_client.update_document_xml.call_args
        assert call_args.kwargs["document_uri"] == "test/case/2020/1234"
        assert "annotation" in call_args.kwargs

    def test_save_creates_default_edit_annotation(self, mock_api_client):
        """Test that save() creates a default EDIT annotation when none is provided."""
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        doc.save()

        call_args = mock_api_client.update_document_xml.call_args
        annotation = call_args.kwargs["annotation"]

        assert isinstance(annotation, VersionAnnotation)
        assert annotation.version_type == VersionType.EDIT
        assert annotation.automated is False
        assert annotation.message is not None
        assert "Document updated via API client" in annotation.message

    def test_save_uses_provided_annotation(self, mock_api_client):
        """Test that save() uses a provided annotation instead of creating a default."""
        custom_annotation = VersionAnnotation(
            version_type=VersionType.EDIT,
            automated=False,
            message="Custom message",
        )

        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        doc.save(annotation=custom_annotation)

        call_args = mock_api_client.update_document_xml.call_args
        annotation = call_args.kwargs["annotation"]

        assert annotation is custom_annotation
        assert annotation.message == "Custom message"

    def test_save_with_from_version_issues_warning(self, mock_api_client):
        """Test that save() issues a FutureWarning when from_version is provided."""
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        with pytest.warns(FutureWarning, match="from_version parameter is not yet supported"):
            doc.save(from_version=1)

    def test_save_without_from_version_no_warning(self, mock_api_client):
        """Test that save() without from_version doesn't issue any warnings."""
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            doc.save()  # Should not raise

    def test_save_passes_xml_tree_to_api_client(self, mock_api_client):
        """Test that save() passes the document's XML tree to api_client."""
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        doc.save()

        call_args = mock_api_client.update_document_xml.call_args
        assert call_args.kwargs["document_xml"] is doc.body.xml_tree

    def test_save_with_annotation_and_from_version(self, mock_api_client):
        """Test that save() accepts both annotation and from_version parameters."""
        custom_annotation = VersionAnnotation(
            version_type=VersionType.EDIT,
            automated=False,
            message="Test",
        )

        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)
        with pytest.warns(FutureWarning):
            doc.save(annotation=custom_annotation, from_version=1)

        call_args = mock_api_client.update_document_xml.call_args
        assert call_args.kwargs["annotation"] is custom_annotation


class TestDocumentMutateAndSave:
    """Tests for the combined workflow: mutate document, then save."""

    FULL_DOCUMENT_XML = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
    <judgment name="decision">
        <meta>
            <identification>
                <FRBRWork>
                    <FRBRname value="Original Case Name"/>
                    <FRBRdate date="2020-01-01"/>
                </FRBRWork>
            </identification>
            <proprietary>
                <uk:court>Original Court</uk:court>
                <uk:jurisdiction>Original Jurisdiction</uk:jurisdiction>
            </proprietary>
        </meta>
        <header><p>Header</p></header>
        <judgmentBody><decision><p>Content</p></decision></judgmentBody>
    </judgment>
</akomaNtoso>"""

    def test_set_name_then_save_persists_mutation(self, mock_api_client):
        """Test that set_name() mutation is persisted when save() is called."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        # Get original name
        original_name = doc.body.name
        assert original_name == "Original Case Name"

        # Mutate name
        doc.body.set_name("Updated Case Name")

        # Verify mutation
        assert doc.body.name == "Updated Case Name"

        # Save
        doc.save()

        # Verify save was called with the mutated XML
        mock_api_client.update_document_xml.assert_called_once()
        call_args = mock_api_client.update_document_xml.call_args

        # Get the XML tree that was passed to the API
        xml_tree = call_args.kwargs["document_xml"]

        # Parse it and verify the name was actually updated
        from lxml import etree

        xml_string = etree.tostring(xml_tree).decode()
        assert "Updated Case Name" in xml_string

    def test_set_date_then_save_persists_mutation(self, mock_api_client):
        """Test that set_date() mutation is persisted when save() is called."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        original_date = doc.body.document_date_as_string
        assert original_date == "2020-01-01"

        doc.body.set_date("2024-06-15")
        assert doc.body.document_date_as_string == "2024-06-15"

        doc.save()

        call_args = mock_api_client.update_document_xml.call_args
        xml_tree = call_args.kwargs["document_xml"]

        from lxml import etree

        xml_string = etree.tostring(xml_tree).decode()
        assert "2024-06-15" in xml_string

    def test_set_court_then_save_persists_mutation(self, mock_api_client):
        """Test that set_court() mutation is persisted when save() is called."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        original_court = doc.body.court
        assert original_court == "Original Court"

        doc.body.set_court("Appeal Court")
        assert doc.body.court == "Appeal Court"

        doc.save()

        call_args = mock_api_client.update_document_xml.call_args
        xml_tree = call_args.kwargs["document_xml"]

        from lxml import etree

        xml_string = etree.tostring(xml_tree).decode()
        assert "Appeal Court" in xml_string

    def test_set_jurisdiction_then_save_persists_mutation(self, mock_api_client):
        """Test that set_jurisdiction() mutation is persisted when save() is called."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        original_jurisdiction = doc.body.jurisdiction
        assert original_jurisdiction == "Original Jurisdiction"

        doc.body.set_jurisdiction("Northern Ireland")
        assert doc.body.jurisdiction == "Northern Ireland"

        doc.save()

        call_args = mock_api_client.update_document_xml.call_args
        xml_tree = call_args.kwargs["document_xml"]

        from lxml import etree

        xml_string = etree.tostring(xml_tree).decode()
        assert "Northern Ireland" in xml_string

    def test_multiple_mutations_then_save(self, mock_api_client):
        """Test that multiple mutations are all persisted when save() is called."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        # Apply multiple mutations
        doc.body.set_name("New Name")
        doc.body.set_date("2024-12-25")
        doc.body.set_court("New Court")

        # Save
        doc.save()

        # Verify all mutations are in the XML that was passed to the API
        call_args = mock_api_client.update_document_xml.call_args
        xml_tree = call_args.kwargs["document_xml"]

        from lxml import etree

        xml_string = etree.tostring(xml_tree).decode()
        assert "New Name" in xml_string
        assert "2024-12-25" in xml_string
        assert "New Court" in xml_string

    def test_save_with_custom_annotation_after_mutations(self, mock_api_client):
        """Test that custom annotation is used even after mutations."""
        mock_api_client.get_judgment_xml_bytestring.return_value = self.FULL_DOCUMENT_XML
        doc = Document(DocumentURIString("test/case/2020/1234"), mock_api_client)

        custom_annotation = VersionAnnotation(
            version_type=VersionType.EDIT,
            automated=False,
            message="Metadata edited by editor",
        )

        doc.body.set_name("Edited Name")
        doc.save(annotation=custom_annotation)

        call_args = mock_api_client.update_document_xml.call_args
        annotation = call_args.kwargs["annotation"]

        assert annotation is custom_annotation
        assert annotation.message == "Metadata edited by editor"
