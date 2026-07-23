from caselawclient.models.documents.metadata.base import MultipleMetadata
from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue, MetadataFieldValue
from caselawclient.types import DocumentCategory


def document_categories_from_field_values(values: list[MetadataFieldValue]) -> list[DocumentCategory]:
    """Build a ``DocumentCategory`` tree from flat category metadata claim values.

    Duplicate category names (e.g. the same category claimed by multiple sources)
    are de-duplicated with first-seen order winning.
    """
    category_values = [value for value in values if isinstance(value, MetadataCategoryValue)]

    categories: dict[str, DocumentCategory] = {}
    children_map: dict[str, list[DocumentCategory]] = {}
    top_level_order: list[str] = []

    for category_value in category_values:
        if category_value.name in categories:
            continue

        category = DocumentCategory(name=category_value.name)
        categories[category_value.name] = category

        if category_value.parent:
            children_map.setdefault(category_value.parent, []).append(category)
        else:
            top_level_order.append(category_value.name)

    for parent, subcategories in children_map.items():
        if parent in categories:
            categories[parent].subcategories.extend(subcategories)

    return [categories[name] for name in top_level_order]


class CategoriesMetadata(MultipleMetadata[DocumentCategory]):
    key = "category"
    title = "Category"
    description = "The categories assigned to the document."

    @property
    def values(self) -> list[DocumentCategory]:
        resolved = self._resolve_claims()
        if not resolved.has_any_claims:
            return self.document.body.categories
        return document_categories_from_field_values(resolved.values)
