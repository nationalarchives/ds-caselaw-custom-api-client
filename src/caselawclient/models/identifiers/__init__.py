from abc import ABC, abstractmethod
from typing import Any, Optional
from uuid import uuid4

from lxml import etree


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
            self.uuid = str(uuid4())

    @property
    def as_xml_tree(self) -> etree._Element:
        identifier_root = etree.Element("identifier")

        identifier_namespace = etree.SubElement(identifier_root, "namespace")
        identifier_namespace.text = self.schema.namespace

        identifier_uuid = etree.SubElement(identifier_root, "uuid")
        identifier_uuid.text = self.uuid

        identifier_value = etree.SubElement(identifier_root, "value")
        identifier_value.text = self.value

        return identifier_root
