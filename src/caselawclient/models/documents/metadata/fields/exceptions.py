class InvalidMetadataFieldXMLRepresentationException(Exception):
    """Raised when a metadata field cannot be unpacked from XML."""


class MetadataFieldException(Exception):
    """Base for metadata claim collection / mutation errors."""


class MetadataFieldRemovalNotAllowedException(MetadataFieldException):
    """Raised when attempting to hard-remove a non-editor metadata claim."""


class MetadataFieldIdCollisionException(MetadataFieldException):
    """Raised when adding a claim whose id is already used by a different payload."""


class MetadataFieldEmptyValueException(MetadataFieldException):
    """Raised when adding a claim whose value is empty / non-resolving."""


class MetadataFieldKeyMismatchException(MetadataFieldException):
    """Raised when a collection key does not match the claim's id."""
