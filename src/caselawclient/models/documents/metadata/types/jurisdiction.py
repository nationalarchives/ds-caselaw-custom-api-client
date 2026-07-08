from caselawclient.models.documents.metadata.base import SingleMetadata


class JurisdictionMetadata(SingleMetadata[str]):
    key = "jurisdiction"
    title = "Jurisdiction"
    description = "The jurisdiction of the document."

    @property
    def value(self) -> str:
        return self.document.body.jurisdiction
