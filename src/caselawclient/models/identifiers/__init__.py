from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from uuid import uuid4

from lxml import etree

from caselawclient.types import DocumentIdentifierSlug, DocumentIdentifierValue

from .exceptions import IdentifierValidationException, UUIDMismatchError

IDENTIFIER_PACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
    "url_slug",
]

IDENTIFIER_UNPACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
]


class IdentifierSchema(ABC):
    """
    A base class which describes what an identifier schema should look like.
    """

    name: str
    namespace: str

    human_readable: bool
    """ Should this identifier type be considered for display as a 'human readable' identifier? """

    base_score_multiplier: float = 1.0
    """ A multiplier used to adjust the relative ranking of this identifier when calculating preferred identifiers. """

    def __init_subclass__(cls: type["IdentifierSchema"], **kwargs: Any) -> None:
        """Ensure that subclasses have the required attributes set."""
        for required in (
            "name",
            "namespace",
            "human_readable",
        ):
            if not hasattr(cls, required):
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
    def compile_identifier_url_slug(cls, value: str) -> DocumentIdentifierSlug:
        """Convert an identifier into a precompiled URL slug."""
        pass


class Identifier(ABC):
    """A base class for subclasses representing a concrete identifier."""

    schema: type[IdentifierSchema]

    uuid: str
    value: DocumentIdentifierValue

    def __init_subclass__(cls: type["Identifier"], **kwargs: Any) -> None:
        """Ensure that subclasses have the required attributes set."""
        for required in ("schema",):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate Identifier without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        return f"<{self.schema.name} {self.value}: {self.uuid}>"

    def __str__(self) -> str:
        return self.value

    def __init__(self, value: str, uuid: Optional[str] = None) -> None:
        if not self.schema.validate_identifier(value=value):
            raise IdentifierValidationException(
                f'Identifier value "{value}" is not valid according to the {self.schema.name} schema.'
            )

        self.value = DocumentIdentifierValue(value)
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

    @property
    def score(self) -> float:
        """Return the score of this identifier, used to calculate the preferred identifier for a document."""
        return 1 * self.schema.base_score_multiplier

    def same_as(self, other: "Identifier") -> bool:
        "Is this the same as another identifier (in value and schema)?"
        return self.value == other.value and self.schema == other.schema


class Identifiers(dict[str, Identifier]):
    def validate(self) -> None:
        for uuid, identifier in self.items():
            if uuid != identifier.uuid:
                msg = "Key of {identifier} in Identifiers is {uuid} not {identifier.uuid}"
                raise UUIDMismatchError(msg)

    def contains(self, other_identifier: Identifier) -> bool:
        "Do the identifier's value and namespace already exist in this group?"
        return any(other_identifier.same_as(identifier) for identifier in self.values())

    def add(self, identifier: Identifier) -> None:
        if not self.contains(identifier):
            self[identifier.uuid] = identifier

    def __delitem__(self, key: Union[Identifier, str]) -> None:
        if isinstance(key, Identifier):
            super().__delitem__(key.uuid)
        else:
            super().__delitem__(key)

    def of_type(self, identifier_type: type[Identifier]) -> list[Identifier]:
        """Return a list of all identifiers of a given type."""
        uuids = self.keys()
        return [self[uuid] for uuid in list(uuids) if isinstance(self[uuid], identifier_type)]

    def delete_type(self, deleted_identifier_type: type[Identifier]) -> None:
        "For when we want an identifier to be the only valid identifier of that type, delete the others first"
        uuids = self.keys()
        for uuid in list(uuids):
            # we could use compare to .schema instead, which would have diffferent behaviour for subclasses
            if isinstance(self[uuid], deleted_identifier_type):
                del self[uuid]

    @property
    def as_etree(self) -> etree._Element:
        """Return an etree representation of all the Document's identifiers."""
        identifiers_root = etree.Element("identifiers")

        for identifier in self.values():
            identifiers_root.append(identifier.as_xml_tree)

        return identifiers_root

    def by_score(self, type: Optional[type[Identifier]] = None) -> list[Identifier]:
        """
        :param type: Optionally, an identifier type to constrain this list to.

        :return: Return a list of identifiers, sorted by their score in descending order.
        """
        identifiers = self.of_type(type) if type else list(self.values())
        return sorted(identifiers, key=lambda v: v.score, reverse=True)

    def preferred(self, type: Optional[type[Identifier]] = None) -> Optional[Identifier]:
        """
        :param type: Optionally, an identifier type to constrain the results to.

        :return: Return the highest scoring identifier of the given type (or of any type, if none is specified). Returns `None` if no identifier is available.
        """
        if len(self.by_score(type)) == 0:
            return None
        return self.by_score(type)[0]
