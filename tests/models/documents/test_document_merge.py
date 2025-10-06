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

    def test_check_is_safe_as_merge_source_runs_expected_checks(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(document, "check_has_only_one_version") as mock_check_has_only_one_version,
        ):
            mock_check_has_only_one_version.return_value = SuccessFailureMessageTuple(True, [])

            document.check_is_safe_as_merge_source()

            mock_check_has_only_one_version.assert_called_once()

    def test_check_is_safe_as_merge_source_bubbles_success_or_failure_on_single_failure(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        with (
            patch.object(document, "check_has_only_one_version") as mock_check_has_only_one_version,
        ):
            mock_check_has_only_one_version.return_value = SuccessFailureMessageTuple(
                False, ["This document has more than one version"]
            )

            check_result = document.check_is_safe_as_merge_source()

            assert check_result.success is False
            assert check_result.messages == ["This document has more than one version"]
