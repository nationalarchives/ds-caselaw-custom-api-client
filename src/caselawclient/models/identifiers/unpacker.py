from lxml import etree

from . import Identifier, InvalidIdentifierXMLRepresentationException
from .neutral_citation import NeutralCitationNumber

IDENTIFIER_NAMESPACE_MAP: dict[str, type[Identifier]] = {
    "ukncn": NeutralCitationNumber,
}


def unpack_identifier_from_etree(identifier_xml: etree._Element) -> Identifier:
    """Given an etree representation of an identifier, unpack it into an appropriate instance of an Identifier."""

    namespace_element = identifier_xml.find("namespace")
    uuid_element = identifier_xml.find("uuid")
    value_element = identifier_xml.find("value")

    if namespace_element is None or not namespace_element.text:
        raise InvalidIdentifierXMLRepresentationException(
            "Identifer XML representation is not valid: namespace not present or empty"
        )

    if uuid_element is None or not uuid_element.text:
        raise InvalidIdentifierXMLRepresentationException(
            "Identifer XML representation is not valid: UUID not present or empty"
        )

    if value_element is None or not value_element.text:
        raise InvalidIdentifierXMLRepresentationException(
            "Identifer XML representation is not valid: value not present or empty"
        )

    return IDENTIFIER_NAMESPACE_MAP[namespace_element.text](uuid=uuid_element.text, value=value_element.text)
