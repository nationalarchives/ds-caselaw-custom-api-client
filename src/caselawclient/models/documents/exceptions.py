class CannotPublishUnpublishableDocument(Exception):
    """A document which has failed publication safety checks in `Document.is_publishable` cannot be published."""


class CannotEnrichUnenrichableDocument(Exception):
    """A document which cannot be enriched (see `Document.can_enrich`) tried to be sent to enrichment"""


class DocumentNotSafeForDeletion(Exception):
    """A document which is not safe for deletion cannot be deleted."""


class DocumentDoesNotValidateWarning(UserWarning):
    """We tried to validate a document when attempting an operation expecting it to succeed and it failed."""
