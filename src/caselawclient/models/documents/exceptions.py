class CannotPublishUnpublishableDocument(Exception):
    """A document which has failed publication safety checks in `Document.is_publishable` cannot be published."""


class CannotRestoreDocument(Exception):
    """Base class for reasons why a previous version of a document cannot be restored."""


class CannotRestorePublishedDocument(CannotRestoreDocument):
    """A document which is currently published cannot have a previous version restored."""


class CannotRestoreDocumentWithoutConsignmentReference(CannotRestoreDocument):
    """A document cannot be restored when no TDR consignment reference is available, as its S3 assets cannot be located."""


class CannotEnrichUnenrichableDocument(Exception):
    """A document which cannot be enriched (see `Document.can_enrich`) tried to be sent to enrichment"""


class DocumentNotSafeForDeletion(Exception):
    """A document which is not safe for deletion cannot be deleted."""
