from caselawclient.models.documents.metadata.base import SingleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataStringValue


class CaseNumberMetadata(SingleMetadata[str | None]):
    key = "case_number"
    title = "Case Number"
    description = "The case number of the document."
    LOGIC_VERSION = 2

    @property
    def value(self) -> str | None:
        raw = self.document.body.case_number
        body_value = raw if raw else None
        return self._optional_string_value(body_value)

    def materialise_body_claims(self) -> None:
        case_number = self.document.body.case_number
        if not case_number:
            return
        self._materialise_document_values([MetadataStringValue(case_number)])

    def write_resolved_to_body(self) -> None:
        case_number = self.value
        if case_number is None:
            self.document.body.write_case_numbers([])
            return
        self.document.body.write_case_numbers([case_number])
