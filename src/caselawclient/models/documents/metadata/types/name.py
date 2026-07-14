from caselawclient.models.documents.metadata.base import SingleMetadata


class NameMetadata(SingleMetadata[str]):
    key = "name"
    title = "Name"
    description = "The name of the document."

    @property
    def value(self) -> str:
        return self.document.body.name
