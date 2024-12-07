from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import uuid4

from lxml import etree

IDENTIFIER_PACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
    "url_slug",
]

IDENTIFIER_UNPACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
]


class InvalidIdentifierXMLRepresentationException(Exception):
    pass


class IdentifierSchema(ABC):
    """
    A base class which describes what an identifier schema should look like.
    """

    name: str
    namespace: str

    def __init_subclass__(cls: type["IdentifierSchema"], **kwargs: Any) -> None:
        """Ensure that subclasses have the required attributes set."""
        for required in (
            "name",
            "namespace",
        ):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate IdentifierSchema without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return self.name

    @classmethod
    @abstractmethod
    def validate_identifier(cls, value: str) -> bool:
        """Check that any given identifier value is valid for this schema."""
        pass

    @classmethod
    @abstractmethod
    def compile_identifier_url_slug(cls, value: str) -> str:
        """Convert an identifier into a precompiled URL slug."""
        pass


class Identifier(ABC):
    """A base class for subclasses representing a concrete identifier."""

    schema: type[IdentifierSchema]

    uuid: str
    value: str

    def __init_subclass__(cls: type["Identifier"], **kwargs: Any) -> None:
        """Ensure that subclasses have the required attributes set."""
        for required in ("schema",):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate Identifier without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return f"{self.uuid} ({self.schema.name}): {self.value}"

    def __init__(self, value: str, uuid: Optional[str] = None) -> None:
        self.value = value
        if uuid:
            self.uuid = uuid
        else:
            self.uuid = "id-" + str(uuid4())

    @property
    def as_xml_tree(self) -> etree._Element:
        """Convert this Identifier into a packed XML representation for storage."""
        identifier_root = etree.Element("identifier")

        namespace_attribute = etree.SubElement(identifier_root, "namespace")
        namespace_attribute.text = self.schema.namespace

        for attribute in IDENTIFIER_PACKABLE_ATTRIBUTES:
            packed_attribute = etree.SubElement(identifier_root, attribute)
            packed_attribute.text = getattr(self, attribute)

        return identifier_root

    @property
    def url_slug(self) -> str:
        return self.schema.compile_identifier_url_slug(self.value)
