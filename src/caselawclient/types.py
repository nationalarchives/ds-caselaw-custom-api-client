from dataclasses import dataclass, field
from typing import NamedTuple


@dataclass
class DocumentCategory:
    name: str
    subcategories: list["DocumentCategory"] = field(default_factory=list)


class InvalidDocumentURIException(Exception):
    """The document URI is not valid."""


class InvalidMarkLogicDocumentURIException(Exception):
    """The MarkLogic document URI is not valid."""


class MarkLogicDocumentURIString(str):
    def __new__(cls, content: str) -> "MarkLogicDocumentURIString":
        # Check that the URI begins with a slash
        if content[0] != "/":
            raise InvalidMarkLogicDocumentURIException(
                f'"{content}" is not a valid MarkLogic document URI; URIs must begin with a slash.'
            )

        # Check that the URI ends with ".xml"
        if not content.endswith(".xml"):
            raise InvalidMarkLogicDocumentURIException(
                f'"{content}" is not a valid MarkLogic document URI; URIs must end with ".xml". '
            )

        # If everything is good, return as usual
        return str.__new__(cls, content)

    def as_document_uri(self) -> "DocumentURIString":
        return DocumentURIString(self.lstrip("/").rstrip(".xml"))


class DocumentURIString(str):
    """
    This class checks that the string is actually a valid Document URI on creation. It does _not_ manipulate the string.
    """

    def __new__(cls, content: str) -> "DocumentURIString":
        # Check that the URI doesn't begin or end with a slash
        if content[0] == "/" or content[-1] == "/":
            raise InvalidDocumentURIException(
                f'"{content}" is not a valid document URI; URIs cannot begin or end with slashes.'
            )

        # Check that the URI doesn't contain a full stop
        if "." in content:
            raise InvalidDocumentURIException(
                f'"{content}" is not a valid document URI; URIs cannot contain full stops.'
            )

        # If everything is good, return as usual
        return str.__new__(cls, content)

    def as_marklogic(self) -> MarkLogicDocumentURIString:
        return MarkLogicDocumentURIString(f"/{self}.xml")


class DocumentIdentifierSlug(str):
    pass


class DocumentIdentifierValue(str):
    pass


SuccessFailureMessageTuple = NamedTuple("SuccessFailureMessageTuple", [("success", bool), ("messages", list[str])])
"""
A tuple used to return if an operation has succeeded or failed (and optionally a list of messages associated with that operation).

This should only be used where a failure is considered a routine part of the application (eg during validation options); where an unexpected action has led to a failure the application should raise an appropriate exception.
"""
