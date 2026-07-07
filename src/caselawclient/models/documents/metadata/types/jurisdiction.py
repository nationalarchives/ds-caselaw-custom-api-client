from functools import cached_property

from caselawclient.models.documents.metadata.base import SingleMetadata


class JurisdictionMetadata(SingleMetadata[str]):
    key = "jurisdiction"
    title = "Jurisdiction"
    description = "The jurisdiction of the document."

    @cached_property
    def value(self) -> str:
        return self.document.body.jurisdiction
