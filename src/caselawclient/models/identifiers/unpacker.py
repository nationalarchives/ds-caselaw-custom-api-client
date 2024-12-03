from lxml import etree

from . import IDENTIFIER_UNPACKABLE_ATTRIBUTES, Identifier, InvalidIdentifierXMLRepresentationException
from .neutral_citation import NeutralCitationNumber

IDENTIFIER_NAMESPACE_MAP: dict[str, type[Identifier]] = {
    "ukncn": NeutralCitationNumber,
}


def unpack_identifier_from_etree(identifier_xml: etree._Element) -> Identifier:
    """Given an etree representation of an identifier, unpack it into an appropriate instance of an Identifier."""

    namespace_element = identifier_xml.find("namespace")

    if namespace_element is None or not namespace_element.text:
        raise InvalidIdentifierXMLRepresentationException(
            "Identifer XML representation is not valid: namespace not present or empty"
        )

    kwargs: dict[str, str] = {}

    for attribute in IDENTIFIER_UNPACKABLE_ATTRIBUTES:
        element = identifier_xml.find(attribute)
        if element is None or not element.text:
            raise InvalidIdentifierXMLRepresentationException(
                f"Identifer XML representation is not valid: {element} not present or empty"
            )
        kwargs[attribute] = element.text

    return IDENTIFIER_NAMESPACE_MAP[namespace_element.text](**kwargs)
