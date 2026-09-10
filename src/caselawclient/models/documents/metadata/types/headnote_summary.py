from caselawclient.models.documents.metadata.base import SingleMetadata


class HeadnoteSummaryMetadata(SingleMetadata[str | None]):
    key = "headnote_summary"
    title = "Headnote Summary"
    description = "A short summary of the headnote for the document."
    editable = True
    LOGIC_VERSION = 1

    @property
    def value(self) -> str | None:
        return self._optional_string_value(None)

    def materialise_body_claims(self) -> None:
        """No body equivalent yet; claims come from EXTERNAL/EDITOR sources."""
        return
