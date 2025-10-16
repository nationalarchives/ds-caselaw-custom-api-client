from caselawclient.models.documents import Document
from caselawclient.types import SuccessFailureMessageTuple


def check_document_is_not_version(document: Document) -> SuccessFailureMessageTuple:
    """Check that the document URI isn't a specific version"""
    if document.is_version:
        return SuccessFailureMessageTuple(
            False,
            ["This document is a specific version, and cannot be used as a merge source"],
        )

    return SuccessFailureMessageTuple(True, [])


def check_document_has_only_one_version(document: Document) -> SuccessFailureMessageTuple:
    """Make sure the document has exactly one version."""
    if len(document.versions) > 1:
        return SuccessFailureMessageTuple(
            False,
            ["This document has more than one version"],
        )

    return SuccessFailureMessageTuple(True, [])


def check_document_has_never_been_published(document: Document) -> SuccessFailureMessageTuple:
    """Make sure the document has never been published."""
    if document.has_ever_been_published:
        return SuccessFailureMessageTuple(
            False,
            ["This document has previously been published"],
        )

    return SuccessFailureMessageTuple(True, [])


def check_document_is_safe_to_delete(document: Document) -> SuccessFailureMessageTuple:
    """Make sure the document is safe to delete."""
    if not document.safe_to_delete:
        return SuccessFailureMessageTuple(
            False,
            ["This document cannot be deleted because it is published"],
        )

    return SuccessFailureMessageTuple(True, [])


def check_documents_are_not_same_document(document_one: Document, document_two: Document) -> SuccessFailureMessageTuple:
    """Check that two documents aren't actually the same"""
    if document_one.uri == document_two.uri:
        return SuccessFailureMessageTuple(
            False,
            ["You cannot merge a document with itself"],
        )
    return SuccessFailureMessageTuple(True, [])


def check_documents_are_same_type(document_one: Document, document_two: Document) -> SuccessFailureMessageTuple:
    """Check to see if this document is the same type as a target document."""
    if type(document_one) is not type(document_two):
        return SuccessFailureMessageTuple(
            False,
            [
                f"The type of {document_one.uri} ({type(document_one).document_noun}) does not match the type of {document_two.uri} ({type(document_two).document_noun})"
            ],
        )
    return SuccessFailureMessageTuple(True, [])


def check_source_document_is_newer_than_target(
    source_document: Document, target_document: Document
) -> SuccessFailureMessageTuple:
    """Check to see if the created datetime of the latest version of this document is newer than the created datetime of the latest version of a target document."""
    if source_document.version_created_datetime < target_document.version_created_datetime:
        return SuccessFailureMessageTuple(
            False, [f"The document at {source_document.uri} is older than the latest version of {target_document.uri}"]
        )
    return SuccessFailureMessageTuple(True, [])
