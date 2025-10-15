from datetime import datetime
from unittest.mock import patch

from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary
from caselawclient.types import SuccessFailureMessageTuple


class TestDocumentSafeAsMergeSource:
    def test_check_has_only_one_version_if_only_one_version(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.versions = [
            {
                "uri": DocumentURIString("test/1234/1"),
                "version": 1,
            }
        ]

        check_result = document.check_has_only_one_version()

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_has_only_one_version_if_multiple_versions(self, mock_api_client):
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

        check_result = document.check_has_only_one_version()

        assert check_result.success is False
        assert check_result.messages == ["This document has more than one version"]

    def test_check_has_never_been_published_if_never_published(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.has_ever_been_published = False

        check_result = document.check_has_never_been_published()

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_has_never_been_published_if_previously_published(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.has_ever_been_published = True

        check_result = document.check_has_never_been_published()

        assert check_result.success is False
        assert check_result.messages == ["This document has previously been published"]

    def test_check_is_safe_to_delete_if_safe(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = True

        check_result = document.check_is_safe_to_delete()

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_is_safe_to_delete_if_unsafe(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = False

        check_result = document.check_is_safe_to_delete()

        assert check_result.success is False
        assert check_result.messages == ["This document cannot be deleted because it is published"]

    def test_check_is_safe_as_merge_source_runs_expected_checks(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(document, "check_has_only_one_version") as mock_check_has_only_one_version,
            patch.object(document, "check_has_never_been_published") as mock_check_has_never_been_published,
            patch.object(document, "check_is_safe_to_delete") as mock_check_is_safe_to_delete,
        ):
            mock_check_has_only_one_version.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_has_never_been_published.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_is_safe_to_delete.return_value = SuccessFailureMessageTuple(True, [])

            document.check_is_safe_as_merge_source()

            mock_check_has_only_one_version.assert_called_once()
            mock_check_has_never_been_published.assert_called_once()
            mock_check_is_safe_to_delete.assert_called_once()

    def test_check_is_safe_as_merge_source_bubbles_success_or_failure_on_single_failure(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.has_ever_been_published = False
        document.safe_to_delete = True

        with (
            patch.object(document, "check_has_only_one_version") as mock_check_has_only_one_version,
        ):
            mock_check_has_only_one_version.return_value = SuccessFailureMessageTuple(
                False, ["This document has more than one version"]
            )

            check_result = document.check_is_safe_as_merge_source()

            assert check_result.success is False
            assert check_result.messages == ["This document has more than one version"]

    def test_check_is_safe_as_merge_source_bubbles_success_or_failure_on_multiple_failures(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.safe_to_delete = True

        with (
            patch.object(document, "check_has_only_one_version") as mock_check_has_only_one_version,
            patch.object(document, "check_has_never_been_published") as mock_check_has_never_been_published,
        ):
            mock_check_has_only_one_version.return_value = SuccessFailureMessageTuple(
                False, ["This document has more than one version"]
            )
            mock_check_has_never_been_published.return_value = SuccessFailureMessageTuple(
                False, ["This document has previously been published"]
            )

            check_result = document.check_is_safe_as_merge_source()

            assert check_result.success is False
            assert check_result.messages == [
                "This document has more than one version",
                "This document has previously been published",
            ]


class TestDocumentSafeToMergeWithTarget:
    def test_check_is_not_same_document_as_when_documents_differ(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        check_result = source_document.check_is_not_same_document_as(target_document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_is_not_same_document_as_when_documents_match(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)

        check_result = source_document.check_is_not_same_document_as(source_document)

        assert check_result.success is False
        assert check_result.messages == ["You cannot merge a document with itself"]

    def test_check_target_is_not_version_when_not_version(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        check_result = source_document.check_target_is_not_version(target_document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_target_is_not_version_when_version(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678/xml_versions/1-"), mock_api_client)

        check_result = source_document.check_target_is_not_version(target_document)

        assert check_result.success is False
        assert check_result.messages == [
            "The document at test/5678/xml_versions/1- is a specific version, and cannot be merged into"
        ]

    def test_check_is_same_type_as_when_types_match(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        check_result = source_document.check_is_same_type_as(target_document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_is_same_type_as_when_types_mismatch(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = PressSummary(DocumentURIString("test/5678"), mock_api_client)

        check_result = source_document.check_is_same_type_as(target_document)

        assert check_result.success is False
        assert check_result.messages == [
            "The type of test/1234 (judgment) does not match the type of test/5678 (press summary)"
        ]

    def test_check_is_newer_than_when_source_is_newer(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        source_document.version_created_datetime = datetime(2025, 2, 1, 12, 34, 56)
        target_document.version_created_datetime = datetime(2025, 1, 1, 12, 34, 56)

        check_result = source_document.check_is_newer_than(target_document)

        assert check_result.success is True
        assert check_result.messages == []

    def test_check_is_newer_than_when_source_is_older(self, mock_api_client):
        source_document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        target_document = Judgment(DocumentURIString("test/5678"), mock_api_client)

        source_document.version_created_datetime = datetime(2025, 1, 1, 12, 34, 56)
        target_document.version_created_datetime = datetime(2025, 2, 1, 12, 34, 56)

        check_result = source_document.check_is_newer_than(target_document)

        assert check_result.success is False
        assert check_result.messages == ["The document at test/1234 is older than the latest version of test/5678"]

    def test_check_is_safe_to_merge_into_runs_expected_checks(self, mock_api_client):
        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch.object(source_document, "check_is_not_same_document_as") as mock_check_is_not_same_document_as,
            patch.object(source_document, "check_target_is_not_version") as mock_check_target_is_not_version,
            patch.object(source_document, "check_is_same_type_as") as mock_check_is_same_type_as,
            patch.object(source_document, "check_is_newer_than") as mock_check_is_newer_than,
        ):
            mock_check_is_not_same_document_as.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_target_is_not_version.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_is_same_type_as.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_is_newer_than.return_value = SuccessFailureMessageTuple(True, [])

            source_document.check_is_safe_to_merge_into(target_document)

            mock_check_is_not_same_document_as.assert_called_once_with(target_document)
            mock_check_target_is_not_version.assert_called_once_with(target_document)
            mock_check_is_same_type_as.assert_called_once_with(target_document)
            mock_check_is_newer_than.assert_called_once_with(target_document)
