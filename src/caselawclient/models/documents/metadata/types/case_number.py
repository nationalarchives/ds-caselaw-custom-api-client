from caselawclient.models.documents.metadata.base import SingleMetadata


class CaseNumberMetadata(SingleMetadata[str | None]):
    key = "case_number"
    title = "Case Number"
    description = "The case number of the document."

    @property
    def value(self) -> str | None:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.case_number
        if resolved.value is None:
            return None
        if not isinstance(resolved.value, str):
            raise TypeError(f"Expected string metadata value for '{self.key}', got {type(resolved.value).__name__}")
        return resolved.value
