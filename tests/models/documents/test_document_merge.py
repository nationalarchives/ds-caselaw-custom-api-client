from unittest.mock import patch

from caselawclient.models.documents import Document, DocumentURIString
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
