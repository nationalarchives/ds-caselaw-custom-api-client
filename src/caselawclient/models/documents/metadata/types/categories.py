from functools import cached_property
from typing import TYPE_CHECKING

from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.types import DocumentCategory

if TYPE_CHECKING:
    from caselawclient.models.documents.body import DocumentBody

CATEGORIES_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category"


def read_categories(body: "DocumentBody") -> list[DocumentCategory]:
    nodes = body.get_xpath_nodes(CATEGORIES_XPATH)

    categories: dict[str, DocumentCategory] = {}
    children_map: dict[str, list[DocumentCategory]] = {}

    for node in nodes:
        name = node.text
        if name is None or not name.strip():
            continue

        category = DocumentCategory(name=name)
        categories[name] = category

        parent = node.get("parent")

        if parent:
            children_map.setdefault(parent, []).append(category)

    for parent, subcategories in children_map.items():
        if parent in categories:
            categories[parent].subcategories.extend(subcategories)

    return [
        categories[name] for node in nodes if node.get("parent") is None if (name := node.text) and name in categories
    ]


class CategoriesMetadata(MultipleMetadata[DocumentCategory]):
    key = "categories"
    title = "Categories"
    description = "The categories assigned to the document."

    @cached_property
    def values(self) -> list[DocumentCategory]:
        return read_categories(self.document.body)
