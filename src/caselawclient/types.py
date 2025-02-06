class InvalidDocumentURIException(Exception):
    """The document URI is not valid."""


class MarkLogicDocumentURIString(str):
    pass


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
