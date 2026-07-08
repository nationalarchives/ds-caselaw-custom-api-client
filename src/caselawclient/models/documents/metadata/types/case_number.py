from caselawclient.models.documents.metadata.base import SingleMetadata


class CaseNumberMetadata(SingleMetadata[str | None]):
    key = "case_number"
    title = "Case Number"
    description = "The case number of the document."

    @property
    def value(self) -> str | None:
        return self.document.body.case_number
