from datetime import datetime

from caselawclient.managers.merge import checks
from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary


class TestCheckDocumentIsNotVersion:
    def test_when_not_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        check_result = checks.check_document_is_not_version(document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234/xml_versions/1-"), mock_api_client)

        check_result = checks.check_document_is_not_version(document)

        assert check_result.success is False
        assert check_result.messages == ["This document is a specific version, and cannot be used as a merge source"]


class TestCheckDocumentHasOnlyOneVersion:
    def test_when_only_one_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.versions = [
            {
                "uri": DocumentURIString("test/1234/1"),
                "version": 1,
            }
        ]

        check_result = checks.check_document_has_only_one_version(document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_multiple_versions(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.versions = [
            {
                "uri": DocumentURIString("test/1234/1"),
                "version": 1,
            },
            {
                "uri": DocumentURIString("test/1234/2"),
                "version": 2,
            },
        ]

        check_result = checks.check_document_has_only_one_version(document)

        assert check_result.success is False
        assert check_result.messages == ["This document has more than one version"]


class TestCheckDocumentHasNeverBeenPublished:
    def test_when_never_published(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.has_ever_been_published = False

        check_result = checks.check_document_has_never_been_published(document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_previously_published(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.has_ever_been_published = True

        check_result = checks.check_document_has_never_been_published(document)

        assert check_result.success is False
        assert check_result.messages == ["This document has previously been published"]


class TestCheckDocumentIsSafeToDelete:
    def test_when_safe(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = True

        check_result = checks.check_document_is_safe_to_delete(document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_unsafe(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = False

        check_result = checks.check_document_is_safe_to_delete(document)

        assert check_result.success is False
        assert check_result.messages == ["This document cannot be deleted because it is published"]


class TestCheckDocumentsAreNotSameDocument:
    def test_when_documents_differ(self, mock_api_client):
        document_one = Judgment(DocumentURIString("test/1234"), mock_api_client)
        document_two = Judgment(DocumentURIString("test/5678"), mock_api_client)

        check_result = checks.check_documents_are_not_same_document(document_one, document_two)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_documents_match(self, mock_api_client):
        document_one = Judgment(DocumentURIString("test/1234"), mock_api_client)

        check_result = checks.check_documents_are_not_same_document(document_one, document_one)

        assert check_result.success is False
        assert check_result.messages == ["You cannot merge a document with itself"]


class TestCheckDocumentsAreSameType:
    def test_when_types_match(self, mock_api_client):
        document_one = Judgment(DocumentURIString("test/1234"), mock_api_client)
        document_two = Judgment(DocumentURIString("test/5678"), mock_api_client)

        check_result = checks.check_documents_are_same_type(document_one, document_two)

        assert check_result.success is True
        assert check_result.messages == []

    def test_when_types_mismatch(self, mock_api_client):
        document_one = Judgment(DocumentURIString("test/1234"), mock_api_client)
        document_two = PressSummary(DocumentURIString("test/5678"), mock_api_client)

        check_result = checks.check_documents_are_same_type(document_one, document_two)

        assert check_result.success is False
        assert check_result.messages == [
            "The type of test/1234 (judgment) does not match the type of test/5678 (press summary)"
        ]


class TestCheckSourceDocumentIsNewerThanTarget:
    def test_check_is_newer_than_when_source_is_newer(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        source_document.version_created_datetime = datetime(2025, 2, 1, 12, 34, 56)
        target_document.version_created_datetime = datetime(2025, 1, 1, 12, 34, 56)

        check_result = checks.check_source_document_is_newer_than_target(source_document, target_document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_is_newer_than_when_source_is_older(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        source_document.version_created_datetime = datetime(2025, 1, 1, 12, 34, 56)
        target_document.version_created_datetime = datetime(2025, 2, 1, 12, 34, 56)

        check_result = checks.check_source_document_is_newer_than_target(source_document, target_document)

        assert check_result.success is False
        assert check_result.messages == ["The document at test/1234 is older than the latest version of test/5678"]
