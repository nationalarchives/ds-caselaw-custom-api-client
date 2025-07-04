from typing import Optional
from warnings import warn

from lxml import etree

from . import IDENTIFIER_UNPACKABLE_ATTRIBUTES, Identifier
from .collection import SUPPORTED_IDENTIFIER_TYPES, IdentifiersCollection
from .exceptions import InvalidIdentifierXMLRepresentationException

IDENTIFIER_NAMESPACE_MAP: dict[str, type[Identifier]] = {
    identifier_type.schema.namespace: identifier_type for identifier_type in SUPPORTED_IDENTIFIER_TYPES
}


def unpack_all_identifiers_from_etree(identifiers_etree: Optional[etree._Element]) -> IdentifiersCollection:
    """This expects the entire <identifiers> tag, and unpacks all Identifiers inside it"""
    identifiers = IdentifiersCollection()
    if identifiers_etree is None:
        return identifiers
    for identifier_etree in identifiers_etree.findall("identifier"):
        identifier = unpack_an_identifier_from_etree(identifier_etree)
        if identifier:
            identifiers.add(identifier)
    return identifiers


def unpack_an_identifier_from_etree(identifier_xml: etree._Element) -> Optional[Identifier]:
    """Given an etree representation of a single identifier, unpack it into an appropriate instance of an Identifier if the type is known (otherwise return `None`)."""

    namespace_element = identifier_xml.find("namespace")

    if namespace_element is None or not namespace_element.text:
        raise InvalidIdentifierXMLRepresentationException(
            "Identifer XML representation is not valid: namespace not present or empty"
        )

    # If the identifier namespace isn't known, fail out
    if namespace_element.text not in IDENTIFIER_NAMESPACE_MAP:
        warn(f"Identifier type {namespace_element.text} is not known.")
        return None

    str_kwargs: dict[str, str] = {}
    deprecated = False

    for attribute in IDENTIFIER_UNPACKABLE_ATTRIBUTES:
        element = identifier_xml.find(attribute)

        # Special case for unpacking deprecation state into a boolean
        if attribute == "deprecated":
            if element is not None and element.text is not None and element.text.lower() == "true":
                deprecated = True

        else:
            # Case for unpacking all other element types
            if element is None or not element.text:
                raise InvalidIdentifierXMLRepresentationException(
                    f"Identifer XML representation is not valid: {element} not present or empty"
                )
            str_kwargs[attribute] = element.text

    return IDENTIFIER_NAMESPACE_MAP[namespace_element.text](deprecated=deprecated, **str_kwargs)
