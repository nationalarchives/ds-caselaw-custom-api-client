class InvalidMetadataFieldXMLRepresentationException(Exception):
    """Raised when a metadata field cannot be unpacked from XML."""


class MetadataFieldRemovalNotAllowedException(Exception):
    """Raised when attempting to hard-remove a non-editor metadata claim."""


class MetadataFieldValidationException(Exception):
    """Raised when metadata fields fail validation before save."""
