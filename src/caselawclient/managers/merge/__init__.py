import caselawclient.managers.merge.checks as checks
from caselawclient.Client import MarklogicApiClient
from caselawclient.models.documents import Document
from caselawclient.models.documents.versions import AnnotationDataDict, VersionAnnotation, VersionType
from caselawclient.types import DocumentURIString, SuccessFailureMessageTuple


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


def _convert_structured_source_version_annotation_to_target(
    source_uri: DocumentURIString, source_annotation: AnnotationDataDict, automated: bool, calling_agent: str
) -> VersionAnnotation:
    """Given an annotation from an existing (source) version, adjust it to the annotation to append to the merged version on the target."""
    merge_annotation = VersionAnnotation(
        version_type=VersionType.MERGE,
        automated=automated,
        message="Version created by merging another document into this one.",
        payload=source_annotation.get("payload", {}) | {"merge_source": source_uri},
    )

    merge_annotation.set_calling_agent(calling_agent)
    merge_annotation.set_calling_function("caselawclient.managers.merge.MergeManager.merge")

    return merge_annotation


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
    def merge_documents(
        cls,
        source_document: Document,
        target_document: Document,
        api_client: MarklogicApiClient,
        automated: bool = False,
    ) -> None:
        """
        Perform all the operations to actually merge documents.

        :param source_document: The document to use as the merge source, ie the one which will become the latest version.
        :param target_document: The document to use as the merge target, ie the one which will persist after the merge is complete.
        :param api_client: The API Client instance to use to perform these operations.
        :param automated: Has this merge happened as the result of an automated process?

        All failure states raise an exception, so reaching the end of this method indicates success.
        """

        # Perform document safety checks to make sure this is a sensible merge to perform

        source_safe = cls.check_document_is_safe_as_merge_source(source_document)
        if not source_safe:
            raise MergeSourceIsUnsafe(f"Document is unsafe to use as merge source: {', '.join(source_safe.messages)}")

        target_safe = cls.check_source_document_is_safe_to_merge_into_target(source_document, target_document)
        if not target_safe:
            raise MergeTargetIsUnsafe(f"Document is unsafe to use as merge target: {', '.join(target_safe.messages)}")

        # Acquire document locks on both source and target so nothing untoward can happen whilst we're working on things.
        # We acquire locks for five minutes; this _should_ all be done well within that time.

        api_client.checkout_judgment(source_document.uri, annotation="Checked out as merge source", timeout_seconds=300)
        api_client.checkout_judgment(target_document.uri, annotation="Checked out as merge target", timeout_seconds=300)

        # At this point both the source and target should be locked; they're ours to play with.

        # Unpublish the target document, if published. This will lead to an interruption in availability whilst we're performing merge operations, but prevents users from being able to access a document in an inconsistent state.
        target_document_published: bool = target_document.is_published
        if target_document_published:
            target_document.unpublish()

        # We build a new history annotation to go with the new version, pulling the payload (with TDR/TRE/Parser metadata) from the previous one

        merged_version_annotation = _convert_structured_source_version_annotation_to_target(
            source_uri=source_document.uri,
            source_annotation=source_document.structured_annotation,
            automated=automated,
            calling_agent=api_client.user_agent,
        )

        # Add the XML of the source document as a new version to the target document, with appropriate annotation
        api_client.update_document_xml(
            target_document.uri, source_document.body.content_as_xml, merged_version_annotation
        )

        # 8. Merge any document identifiers. If necessary, deprecate those of the target document.
        #     1. For all identifiers in the source document:
        #         1. Is there a matching identifier (type and value) in the target? If so, disregard this source identifier
        #         2. If the identifier doesn't match and the source identifier is deprecated, copy it over. Multiple deprecated identifiers are fine for all types.
        #         3. If the source identifier isn't deprecated, does this identifier type support multiple current (ie non-deprecated) identifiers? If so, copy the source identifier into the target identifiers
        #         4. If the existing identifier type doesn't support multiple current identifiers, deprecate the existing current one and copy the source identifier over
        # 9. Delete non-targz assets from the source target document (published and unpublished buckets)
        # 10. Copy over all unpublished assets from the source document to the prefix of the target document.
        # 11. Delete the source document

        # Re-publish target document (if it was originally published) so it's available for the public again
        if target_document_published:
            target_document.publish()

        # Finally, unlock the target document so it's available for routine editing processes
        api_client.checkin_judgment(target_document.uri)
