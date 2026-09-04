"""Tests for Document.from_xml() and document_from_xml()."""

from unittest.mock import patch

import pytest

from caselawclient.client_helpers import document_from_xml
from caselawclient.factories import DocumentBodyFactory, DocumentFactory, JudgmentFactory
from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.exceptions import DocumentAlreadyExistsError, DocumentNotPersistedError
from caselawclient.models.judgments import Judgment
from caselawclient.models.parser_logs import ParserLog
from caselawclient.models.press_summaries import PressSummary


@pytest.fixture(autouse=True)
def document_does_not_exist_in_marklogic(mock_api_client):
    mock_api_client.document_exists.return_value = False


class TestDocumentFromXml:
    def test_from_xml_checks_document_does_not_exist(self, mock_api_client):
        body = DocumentBodyFactory.build()

        with patch.object(mock_api_client, "get_judgment_xml_bytestring") as mock_get_xml:
            document = Judgment.from_xml(body, mock_api_client)

        mock_api_client.document_exists.assert_called_once()
        mock_get_xml.assert_not_called()
        assert document.is_persisted is False

    def test_from_xml_raises_when_uri_already_exists(self, mock_api_client):
        body = DocumentBodyFactory.build()
        uri = DocumentURIString("test/2023/123")
        mock_api_client.document_exists.return_value = True

        with pytest.raises(DocumentAlreadyExistsError, match="already exists"):
            Judgment.from_xml(body, mock_api_client, uri=uri)

    def test_from_xml_mints_uri_when_omitted(self, mock_api_client):
        body = DocumentBodyFactory.build()
        document = Judgment.from_xml(body, mock_api_client)

        assert str(document.uri).startswith("d-")
        assert len(str(document.uri)) > 2

    def test_from_xml_uses_provided_uri(self, mock_api_client):
        body = DocumentBodyFactory.build()
        uri = DocumentURIString("d-abc123")

        document = Judgment.from_xml(body, mock_api_client, uri=uri)

        assert document.uri == uri

    def test_from_xml_initialises_in_memory_state(self, mock_api_client):
        body = DocumentBodyFactory.build()
        document = Judgment.from_xml(body, mock_api_client)

        assert document.body is body
        assert len(document.identifiers) == 0
        assert len(document.metadata_fields) == 0
        assert document.metadata.title.value == "Judgment v Judgement"

    def test_from_xml_initialises_ncn_validation(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        validation_names = [name for name, _, _ in document.attributes_to_validate]
        assert "has_valid_ncn" in validation_names

    def test_linked_document_on_ephemeral_judgment_raises(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        with pytest.raises(DocumentNotPersistedError):
            _ = document.linked_document

    def test_linked_document_on_ephemeral_press_summary_raises(self, mock_api_client):
        body = DocumentBody(
            b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <doc name="pressSummary">
                <meta><identification><FRBRWork><FRBRname value="Summary"/></FRBRWork></identification></meta>
                <mainBody><p>Summary text</p></mainBody>
            </doc>
            </akomaNtoso>"""
        )
        document = PressSummary.from_xml(body, mock_api_client)

        with pytest.raises(DocumentNotPersistedError):
            _ = document.linked_document

    def test_press_summary_from_xml(self, mock_api_client):
        xml = b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
            xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <doc name="pressSummary">
                <meta><identification><FRBRWork><FRBRname value="Summary"/></FRBRWork></identification></meta>
                <mainBody><p>Summary text</p></mainBody>
            </doc>
            </akomaNtoso>"""
        body = DocumentBody(xml)

        document = PressSummary.from_xml(body, mock_api_client)

        assert isinstance(document, PressSummary)
        assert document.is_persisted is False

    def test_parser_log_from_xml(self, mock_api_client):
        body = DocumentBody(b"<error>parser failed</error>")

        document = ParserLog.from_xml(body, mock_api_client)

        assert isinstance(document, ParserLog)
        assert document.is_persisted is False

    def test_document_from_xml_helper_returns_parser_log(self, mock_api_client):
        body = DocumentBody(b"<error>parser failed</error>")

        document = document_from_xml(body, mock_api_client)

        assert isinstance(document, ParserLog)

    def test_document_from_xml_helper_returns_judgment(self, mock_api_client):
        body = DocumentBodyFactory.build()

        document = document_from_xml(body, mock_api_client)

        assert isinstance(document, Judgment)

    def test_base_document_from_xml_raises(self, mock_api_client):
        body = DocumentBodyFactory.build()

        with pytest.raises(TypeError, match="document_from_xml"):
            Document.from_xml(body, mock_api_client)

    def test_base_document_save_raises(self, mock_api_client):
        body = DocumentBodyFactory.build()
        assemble = Document._assemble_from_body  # noqa: SLF001
        document = assemble(body, mock_api_client)

        with pytest.raises(TypeError, match="concrete document class"):
            document.save(message="test")

    def test_publish_on_ephemeral_document_raises(self, mock_api_client):
        document = Judgment.from_xml(DocumentBodyFactory.build(), mock_api_client)

        with pytest.raises(DocumentNotPersistedError):
            document.publish()

    def test_document_factory_sets_persisted(self, mock_api_client):
        document = DocumentFactory.build(api_client=mock_api_client)

        assert document.is_persisted is True

    def test_judgment_factory_sets_persisted(self, mock_api_client):
        document = JudgmentFactory.build(api_client=mock_api_client)

        assert document.is_persisted is True


class TestParserLogSaveInsert:
    def test_parser_log_save_inserts_into_parser_log_collection(self, mock_api_client):
        body = DocumentBody(b"<error>parser failed</error>")
        document = ParserLog.from_xml(body, mock_api_client, uri=DocumentURIString("d-parser-test"))
        mock_api_client.document_exists.return_value = False

        with patch.object(document.api_client, "insert_document_xml") as mock_insert:
            document.save(message="Initial parser log")

        mock_insert.assert_called_once()
        call_args = mock_insert.call_args
        assert call_args[0][0] == DocumentURIString("d-parser-test")
        assert call_args[0][2] is ParserLog
        assert document.is_persisted is True
