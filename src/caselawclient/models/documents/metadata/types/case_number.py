from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataStringValue


class CaseNumberMetadata(SingleMetadata[str | None]):
    key = "case_number"
    title = "Case Number"
    description = "The case number of the document."

    @property
    def value(self) -> str | None:
        return self._optional_string_value(self.document.body.case_number)

    def materialise_body_claims(self) -> None:
        case_number = self.document.body.case_number
        if case_number is None:
            return
        self._materialise_document_values([MetadataStringValue(case_number)])
