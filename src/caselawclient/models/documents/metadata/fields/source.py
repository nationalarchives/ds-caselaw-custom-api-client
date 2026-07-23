from enum import Enum


class MetadataSource(str, Enum):
    """Origin of a metadata claim, ordered from lowest to highest precedence."""

    DOCUMENT = "document"
    EXTERNAL = "external"
    EDITOR = "editor"

    @property
    def precedence(self) -> int:
        """Higher numbers outrank lower ones when resolving a single-value field."""
        return {
            MetadataSource.DOCUMENT: 0,
            MetadataSource.EXTERNAL: 1,
            MetadataSource.EDITOR: 2,
        }[self]
