from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.types import DocumentCategory


class CategoriesMetadata(MultipleMetadata[DocumentCategory]):
    key = "categories"
    title = "Categories"
    description = "The categories assigned to the document."

    @property
    def values(self) -> list[DocumentCategory]:
        return self.document.body.categories
