class CannotPublishUnpublishableDocument(Exception):
    """A document which has failed publication safety checks in `Document.is_publishable` cannot be published."""


class DocumentNotSafeForDeletion(Exception):
    """A document which is not safe for deletion cannot be deleted."""
