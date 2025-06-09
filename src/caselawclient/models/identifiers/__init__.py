from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Optional, Union
from uuid import uuid4

from lxml import etree

from caselawclient.types import DocumentIdentifierSlug, DocumentIdentifierValue

from .exceptions import (
    GlobalDuplicateIdentifierException,
    IdentifierNotValidForDocumentTypeException,
    IdentifierValidationException,
    UUIDMismatchError,
)

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient
    from caselawclient.models.documents import Document

IDENTIFIER_PACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
    "deprecated",
    "url_slug",
]
"""A list of attributes of an Identifier to pack into an XML representation."""

IDENTIFIER_UNPACKABLE_ATTRIBUTES: list[str] = [
    "uuid",
    "value",
    "deprecated",
]
"""A list of attributes to unpack from an XML representation."""


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

    allow_editing: bool = True
    """ Should editors be allowed to manually manipulate identifiers under this schema? """

    require_globally_unique: bool = True
    """ Must this identifier be globally unique? """

    document_types: Optional[list[str]] = None
    """
    If present, a list of the names of document classes which can have this identifier.

    If `None`, this identifier is valid for all document types.
    """

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
    def validate_identifier_value(cls, value: str) -> bool:
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

    deprecated: bool
    """Should this identifier be considered deprecated, ie although we know it refers to a particular document its usage should be discouraged?"""

    def __init_subclass__(cls: type["Identifier"], **kwargs: Any) -> None:
        """Ensure that subclasses have the required attributes set."""
        for required in ("schema",):
            if not getattr(cls, required, False):
                raise NotImplementedError(f"Can't instantiate Identifier without {required} attribute.")
        super().__init_subclass__(**kwargs)

    def __repr__(self) -> str:
        representation = f"{self.schema.name} {self.value}: {self.uuid}"

        if self.deprecated:
            return f"<{representation} (deprecated)> "
        return f"<{representation}>"

    def __str__(self) -> str:
        return self.value

    def __init__(self, value: str, uuid: Optional[str] = None, deprecated: bool = False) -> None:
        if not self.schema.validate_identifier_value(value=value):
            raise IdentifierValidationException(
                f'Identifier value "{value}" is not valid according to the {self.schema.name} schema.'
            )

        self.value = DocumentIdentifierValue(value)
        if uuid:
            self.uuid = uuid
        else:
            self.uuid = "id-" + str(uuid4())

        self.deprecated = deprecated

    @property
    def as_xml_tree(self) -> etree._Element:
        """Convert this Identifier into a packed XML representation for storage."""
        identifier_root = etree.Element("identifier")

        namespace_attribute = etree.SubElement(identifier_root, "namespace")
        namespace_attribute.text = self.schema.namespace

        for attribute_name in IDENTIFIER_PACKABLE_ATTRIBUTES:
            packed_attribute = etree.SubElement(identifier_root, attribute_name)
            attribute_value = getattr(self, attribute_name)
            if type(attribute_value) is bool:
                packed_attribute.text = str(attribute_value).lower()
            else:
                packed_attribute.text = getattr(self, attribute_name)

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

    def validate_require_globally_unique(self, api_client: "MarklogicApiClient") -> None:
        """
        Check against the list of identifiers in the database that this value does not currently exist.

        nb: We don't need to check that the identifier value is unique within a parent `Identifiers` object, because `Identifiers.add()` will only allow one value per namespace.
        """
        resolutions = [
            resolution
            for resolution in api_client.resolve_from_identifier_value(identifier_value=self.value)
            if resolution.identifier_namespace == self.schema.namespace
        ]
        if len(resolutions) > 0:
            raise GlobalDuplicateIdentifierException(
                f'Identifiers in scheme {self.schema.namespace} must be unique; "{self.value}" already exists!'
            )

    def validate_valid_for_document_type(self, document_type: type["Document"]) -> None:
        document_type_classname = document_type.__name__

        if self.schema.document_types and document_type_classname not in self.schema.document_types:
            raise IdentifierNotValidForDocumentTypeException(
                f"Document type {document_type_classname} is not accepted for identifier schema {self.schema.name}"
            )

    def perform_all_validations(self, document_type: type["Document"], api_client: "MarklogicApiClient") -> None:
        self.validate_require_globally_unique(api_client=api_client)
        self.validate_valid_for_document_type(document_type=document_type)


class Identifiers(dict[str, Identifier]):
    def validate_uuids_match_keys(self) -> None:
        for uuid, identifier in self.items():
            if uuid != identifier.uuid:
                msg = "Key of {identifier} in Identifiers is {uuid} not {identifier.uuid}"
                raise UUIDMismatchError(msg)

    def perform_all_validations(self, document_type: type["Document"], api_client: "MarklogicApiClient") -> None:
        self.validate_uuids_match_keys()
        for _, identifier in self.items():
            identifier.perform_all_validations(document_type=document_type, api_client=api_client)

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
