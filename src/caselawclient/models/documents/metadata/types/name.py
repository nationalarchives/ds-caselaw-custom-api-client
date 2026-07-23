from caselawclient.models.documents.metadata.base import SingleMetadata


class NameMetadata(SingleMetadata[str]):
    key = "title"
    title = "Title"
    description = "The title of the document."

    @property
    def value(self) -> str:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.name
        if resolved.value is None:
            return ""
        if not isinstance(resolved.value, str):
            raise TypeError(f"Expected string metadata value for '{self.key}', got {type(resolved.value).__name__}")
        return resolved.value
