from functools import cached_property

from caselawclient.models.documents.metadata.base import SingleMetadata


class NameMetadata(SingleMetadata[str]):
    key = "name"
    title = "Name"
    description = "The name of the document."

    @cached_property
    def value(self) -> str:
        return self.document.body.name
