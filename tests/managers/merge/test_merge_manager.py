from unittest.mock import patch

from pytest import raises

from caselawclient.managers.merge import (
    MergeManager,
    MergeSourceIsUnsafe,
    MergeTargetIsUnsafe,
    _combine_list_of_successfailure_results,
)
from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.types import SuccessFailureMessageTuple


class TestCombineListOfSuccessFailureResults:
    def test_combine_list_of_successfailure_results_when_all_successes(self):
        validation_results = [
            SuccessFailureMessageTuple(True, []),
            SuccessFailureMessageTuple(True, []),
        ]

        check_result = _combine_list_of_successfailure_results(validation_results)

        assert check_result.success is True
        assert check_result.messages == []

    def test_combine_list_of_successfailure_results_when_mixed(self):
        validation_results = [
            SuccessFailureMessageTuple(True, []),
            SuccessFailureMessageTuple(False, ["Validation message one"]),
        ]

        check_result = _combine_list_of_successfailure_results(validation_results)

        assert check_result.success is False
        assert check_result.messages == ["Validation message one"]

    def test_combine_list_of_successfailure_results_when_all_failures(self):
        validation_results = [
            SuccessFailureMessageTuple(False, ["Validation message one"]),
            SuccessFailureMessageTuple(False, ["Validation message two"]),
        ]

        check_result = _combine_list_of_successfailure_results(validation_results)

        assert check_result.success is False
        assert check_result.messages == ["Validation message one", "Validation message two"]


class TestMergeManagerClassMethods:
    """Check the class methods on MergeManager which we use to make sure documents are valid candidates for merging in the first place."""

    def test_check_is_safe_as_merge_source_runs_expected_checks(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.checks.check_document_is_not_version"
            ) as mock_check_document_is_not_version,
            patch(
                "caselawclient.managers.merge.checks.check_document_has_only_one_version"
            ) as mock_check_document_has_only_one_version,
            patch(
                "caselawclient.managers.merge.checks.check_document_has_never_been_published"
            ) as mock_check_document_has_never_been_published,
            patch(
                "caselawclient.managers.merge.checks.check_document_is_safe_to_delete"
            ) as mock_check_document_is_safe_to_delete,
        ):
            mock_check_document_is_not_version.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_document_has_only_one_version.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_document_has_never_been_published.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_document_is_safe_to_delete.return_value = SuccessFailureMessageTuple(True, [])

            MergeManager.check_document_is_safe_as_merge_source(document)

            mock_check_document_is_not_version.assert_called_once()
            mock_check_document_has_only_one_version.assert_called_once()
            mock_check_document_has_never_been_published.assert_called_once()
            mock_check_document_is_safe_to_delete.assert_called_once()


class TestDocumentSafeToMergeWithTarget:
    def test_check_is_safe_to_merge_into_runs_expected_checks(self, mock_api_client):
        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.checks.check_documents_are_not_same_document"
            ) as mock_check_documents_are_not_same_document,
            patch(
                "caselawclient.managers.merge.checks.check_document_is_not_version"
            ) as mock_check_document_is_not_version,
            patch(
                "caselawclient.managers.merge.checks.check_documents_are_same_type"
            ) as mock_check_documents_are_same_type,
            patch(
                "caselawclient.managers.merge.checks.check_source_document_is_newer_than_target"
            ) as mock_check_source_document_is_newer_than_target,
        ):
            mock_check_documents_are_not_same_document.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_document_is_not_version.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_documents_are_same_type.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_source_document_is_newer_than_target.return_value = SuccessFailureMessageTuple(True, [])

            MergeManager.check_source_document_is_safe_to_merge_into_target(source_document, target_document)

            mock_check_documents_are_not_same_document.assert_called_once_with(source_document, target_document)
            mock_check_document_is_not_version.assert_called_once_with(target_document)
            mock_check_documents_are_same_type.assert_called_once_with(source_document, target_document)
            mock_check_source_document_is_newer_than_target.assert_called_once_with(source_document, target_document)


class TestMergeDocuments:
    def test_merge_documents_raises_on_unsafe_source(self, mock_api_client):
        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.MergeManager.check_document_is_safe_as_merge_source"
            ) as mock_check_document_is_safe_as_merge_source,
            raises(
                MergeSourceIsUnsafe,
                match="Document is unsafe to use as merge source: Failure one, Failure two",
            ),
        ):
            mock_check_document_is_safe_as_merge_source.return_value = SuccessFailureMessageTuple(
                False, ["Failure one", "Failure two"]
            )
            MergeManager.merge_documents(source_document=source_document, target_document=target_document)

    def test_merge_documents_raises_on_unsafe_target(self, mock_api_client):
        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.MergeManager.check_document_is_safe_as_merge_source"
            ) as mock_check_document_is_safe_as_merge_source,
            patch(
                "caselawclient.managers.merge.MergeManager.check_source_document_is_safe_to_merge_into_target"
            ) as mock_check_source_document_is_safe_to_merge_into_target,
            raises(
                MergeTargetIsUnsafe,
                match="Document is unsafe to use as merge target: Failure one, Failure two",
            ),
        ):
            mock_check_document_is_safe_as_merge_source.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_source_document_is_safe_to_merge_into_target.return_value = SuccessFailureMessageTuple(
                False, ["Failure one", "Failure two"]
            )
            MergeManager.merge_documents(source_document=source_document, target_document=target_document)
