from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataStringValue


class NameMetadata(SingleMetadata[str]):
    key = "title"
    title = "Title"
    description = "The title of the document."
    LOGIC_VERSION = 3

    @property
    def value(self) -> str:
        return self._string_value(self.document.body.name)

    def materialise_body_claims(self) -> None:
        if self._resolve_claims().has_any_claims:
            return
        self._materialise_document_values([MetadataStringValue(self.document.body.name)])

    def write_resolved_to_body(self) -> None:
        self.document.body.write_title(self.value)
