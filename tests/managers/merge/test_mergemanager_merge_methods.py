from unittest.mock import patch

import pytest

from caselawclient.managers.merge import (
    MergeManager,
    MergeSourceIsUnsafe,
    MergeTargetIsUnsafe,
    _convert_structured_source_version_annotation_to_target,
)
from caselawclient.models.documents import Document, DocumentURIString
from caselawclient.models.documents.versions import AnnotationDataDict, VersionType
from caselawclient.types import SuccessFailureMessageTuple


class TestConvertSourceAnnotationToTarget:
    @pytest.mark.parametrize("automated", [True, False])
    def test_convert_structured_source_version_annotation_to_target(self, automated):
        """Check that given the version annotation of the source document we correctly turn it into one for the merge target"""
        source_annotation: AnnotationDataDict = {
            "type": VersionType.SUBMISSION.value,
            "calling_function": "test_convert",
            "calling_agent": "test",
            "automated": False,  # This is intentionally False for the source annotation because this will usually be the result of ingest, which is the result of a manual submission action.
            "payload": {"test_payload": "value"},
        }

        merge_annotation = _convert_structured_source_version_annotation_to_target(
            source_uri=DocumentURIString("test/1234"),
            source_annotation=source_annotation,
            automated=automated,
            calling_agent="test agent",
        )

        assert merge_annotation.message == "Version created by merging another document into this one."
        assert merge_annotation.automated is automated
        assert merge_annotation.payload == {"test_payload": "value", "merge_source": "test/1234"}

        assert merge_annotation.version_type == VersionType.MERGE
        assert merge_annotation.calling_agent == "test agent"
        assert merge_annotation.calling_function == "caselawclient.managers.merge.MergeManager.merge"


class TestMergeDocuments:
    def test_merge_documents_raises_on_unsafe_source(self, mock_api_client):
        """Check that merging a document fails when its source document is in an unsafe state."""

        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.MergeManager.check_document_is_safe_as_merge_source"
            ) as mock_check_document_is_safe_as_merge_source,
            pytest.raises(
                MergeSourceIsUnsafe,
                match="Document is unsafe to use as merge source: Failure one, Failure two",
            ),
        ):
            mock_check_document_is_safe_as_merge_source.return_value = SuccessFailureMessageTuple(
                False, ["Failure one", "Failure two"]
            )
            MergeManager.merge_documents(
                source_document=source_document, target_document=target_document, api_client=mock_api_client
            )

    def test_merge_documents_raises_on_unsafe_target(self, mock_api_client):
        """Check that merging a document fails when its target document is in an unsafe state."""

        source_document = Document(DocumentURIString("test/1234"), mock_api_client)
        target_document = Document(DocumentURIString("test/5678"), mock_api_client)

        with (
            patch(
                "caselawclient.managers.merge.MergeManager.check_document_is_safe_as_merge_source"
            ) as mock_check_document_is_safe_as_merge_source,
            patch(
                "caselawclient.managers.merge.MergeManager.check_source_document_is_safe_to_merge_into_target"
            ) as mock_check_source_document_is_safe_to_merge_into_target,
            pytest.raises(
                MergeTargetIsUnsafe,
                match="Document is unsafe to use as merge target: Failure one, Failure two",
            ),
        ):
            mock_check_document_is_safe_as_merge_source.return_value = SuccessFailureMessageTuple(True, [])
            mock_check_source_document_is_safe_to_merge_into_target.return_value = SuccessFailureMessageTuple(
                False, ["Failure one", "Failure two"]
            )
            MergeManager.merge_documents(
                source_document=source_document, target_document=target_document, api_client=mock_api_client
            )
