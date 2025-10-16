import caselawclient.managers.merge.checks as checks
from caselawclient.models.documents import Document
from caselawclient.types import SuccessFailureMessageTuple


def _combine_list_of_successfailure_results(
    validations: list[SuccessFailureMessageTuple],
) -> SuccessFailureMessageTuple:
    """Given a list of SuccessFailureMessageTuples, combine the success/failure states and any messages into a single new object representing the overall success/failure state."""
    success = True
    messages: list[str] = []

    for validation in validations:
        if validation.success is False:
            success = False

        messages += validation.messages

    return SuccessFailureMessageTuple(success, messages)


class MergeManager:
    @classmethod
    def check_document_is_safe_as_merge_source(cls, source_document: Document) -> SuccessFailureMessageTuple:
        """
        Is the given document safe to be considered as a merge source?
        """

        return _combine_list_of_successfailure_results(
            [
                checks.check_document_is_not_version(source_document),
                checks.check_document_has_only_one_version(source_document),
                checks.check_document_has_never_been_published(source_document),
                checks.check_document_is_safe_to_delete(source_document),
            ]
        )

    @classmethod
    def check_source_document_is_safe_to_merge_into_target(
        cls, source_document: Document, target_document: Document
    ) -> SuccessFailureMessageTuple:
        """Is the given source document safe to merge into a given target?"""

        return _combine_list_of_successfailure_results(
            [
                checks.check_documents_are_not_same_document(source_document, target_document),
                checks.check_document_is_not_version(target_document),
                checks.check_documents_are_same_type(source_document, target_document),
                checks.check_source_document_is_newer_than_target(source_document, target_document),
            ]
        )
