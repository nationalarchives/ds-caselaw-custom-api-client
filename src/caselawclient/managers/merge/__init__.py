import caselawclient.managers.merge.checks as checks
from caselawclient.models.documents import Document
from caselawclient.types import SuccessFailureMessageTuple


class MergeFailure(Exception):
    pass


class MergeSourceIsUnsafe(MergeFailure):
    pass


class MergeTargetIsUnsafe(MergeFailure):
    pass


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

    @classmethod
    def merge_documents(cls, source_document: Document, target_document: Document) -> None:
        """
        Perform all the operations to actually merge documents.

        All failure states raise an exception, so reaching the end of this method indicates success.
        """

        # Perform document safety checks to make sure this is a sensible merge to perform

        source_safe = cls.check_document_is_safe_as_merge_source(source_document)
        if not source_safe:
            raise MergeSourceIsUnsafe(f"Document is unsafe to use as merge source: {', '.join(source_safe.messages)}")

        target_safe = cls.check_source_document_is_safe_to_merge_into_target(source_document, target_document)
        if not target_safe:
            raise MergeTargetIsUnsafe(f"Document is unsafe to use as merge target: {', '.join(target_safe.messages)}")

        # 2. Get the XML from the source document
        # 3. Get the history from the source document
        # 4. Begin atomic MarkLogic operations
        # 5. Unpublish the target document, if published
        # 6. Append the history of the source document to the history of the target document
        # 7. Add the XML of the source document as a new version to the target document
        #     1. The VersionAnnotation of the new version should record the fact that it's a merge operation

        # 8. Merge any document identifiers. If necessary, deprecate those of the target document.
        #     1. For all identifiers in the source document:
        #         1. Is there a matching identifier (type and value) in the target? If so, disregard this source identifier
        #         2. If the identifier doesn't match and the source identifier is deprecated, copy it over. Multiple deprecated identifiers are fine for all types.
        #         3. If the source identifier isn't deprecated, does this identifier type support multiple current (ie non-deprecated) identifiers? If so, copy the source identifier into the target identifiers
        #         4. If the existing identifier type doesn't support multiple current identifiers, deprecate the existing current one and copy the source identifier over
        # 9. Delete non-targz assets from the source target document (published and unpublished buckets)
        # 10. Copy over all unpublished assets from the source document to the prefix of the target document.
        # 11. Delete the source document
        # 12. End atomic MarkLogic operations

        pass
