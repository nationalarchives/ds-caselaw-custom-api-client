from dataclasses import dataclass, field


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


class SuccessFailureMessageTuple(tuple[bool, list[str]]):
    """
    Return whether an operation has succeeded or failed
    (and optionally a list of messages associated with that operation).
    Typically the messages will be exposed to the end-user.
    Use only where a failure is a routine event (such as during validation).
    """

    def __new__(cls, success: bool, messages: list[str]) -> "SuccessFailureMessageTuple":
        return super().__new__(cls, [success, messages])

    @property
    def success(self) -> bool:
        return self[0]

    @property
    def messages(self) -> list[str]:
        return self[1]

    def __repr__(self) -> str:
        return f"SuccessFailureMessageTuple({self.success!r}, {self.messages!r})"

    def __bool__(self) -> bool:
        return self.success

    def __or__(self, other: "SuccessFailureMessageTuple") -> "SuccessFailureMessageTuple":
        """Allows us to write combined_tuple = first_tuple | second_tuple"""
        return SuccessFailureMessageTuple(self.success and other.success, self.messages + other.messages)


def SuccessTuple() -> SuccessFailureMessageTuple:
    return SuccessFailureMessageTuple(True, [])


def FailureTuple(message: str | list[str]) -> SuccessFailureMessageTuple:
    messages = message if isinstance(message, list) else [message]
    return SuccessFailureMessageTuple(success=False, messages=messages)
