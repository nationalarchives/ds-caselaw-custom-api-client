from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataStringValue


class JurisdictionMetadata(SingleMetadata[str]):
    key = "jurisdiction"
    title = "Jurisdiction"
    description = "The jurisdiction of the document."

    @property
    def value(self) -> str:
        return self._string_value(self.document.body.jurisdiction)

    def materialise_body_claims(self) -> None:
        self._materialise_document_values([MetadataStringValue(self.document.body.jurisdiction)])
