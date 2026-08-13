from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataStringValue


class CourtMetadata(SingleMetadata[str]):
    key = "court"
    title = "Court"
    description = "The court that issued the document."

    @property
    def value(self) -> str:
        return self._string_value(self.document.body.court)

    def materialise_body_claims(self) -> None:
        self._materialise_document_values([MetadataStringValue(self.document.body.court)])
