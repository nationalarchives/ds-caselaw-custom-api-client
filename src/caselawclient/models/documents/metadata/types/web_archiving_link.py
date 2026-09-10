from caselawclient.models.documents.metadata.base import SingleMetadata


class WebArchivingLinkMetadata(SingleMetadata[str | None]):
    key = "web_archiving_link"
    title = "Web Archiving Link"
    description = "A URL for a web-archived copy of the document or related material."
    editable = True
    LOGIC_VERSION = 1

    @property
    def value(self) -> str | None:
        return self._optional_string_value(None)

    def materialise_body_claims(self) -> None:
        """No body equivalent yet; claims come from EXTERNAL/EDITOR sources."""
        return
