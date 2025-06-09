class InvalidIdentifierXMLRepresentationException(Exception):
    pass


class UUIDMismatchError(Exception):
    pass


class IdentifierValidationException(Exception):
    pass


class IdentifierConstraintException(Exception):
    pass


class GlobalDuplicateIdentifierException(IdentifierConstraintException):
    pass


class IdentifierNotValidForDocumentTypeException(IdentifierConstraintException):
    pass
