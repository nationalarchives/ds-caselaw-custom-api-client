from lxml import etree

from caselawclient.xml_helpers import DEFAULT_NAMESPACES

from ..models.documents import Document
from ..models.judgments import Judgment
from ..models.parser_logs import ParserLog
from ..models.press_summaries import PressSummary


class CannotDetermineDocumentType(Exception):
    pass


def get_document_type_class(xml: bytes) -> type[Document]:
    """Attempt to get the type of the document based on the top-level structure of the XML document."""

    node = etree.fromstring(xml)

    # If the main node is `<judgment>`, it's a judgment
    if node.xpath("/akn:akomaNtoso/akn:judgment", namespaces=DEFAULT_NAMESPACES):
        return Judgment

    # If the main node is `<doc name='pressSummary'>`, it's a press summary
    if node.xpath("/akn:akomaNtoso/akn:doc[@name='pressSummary']", namespaces=DEFAULT_NAMESPACES):
        return PressSummary

    # If the document is a parser error with a root element of `error`, it's not of a special type.
    if node.xpath("/error", namespaces=DEFAULT_NAMESPACES):
        return ParserLog

    # Otherwise, we don't know for sure. Fail out.
    raise CannotDetermineDocumentType(
        "Unable to determine the Document type by its XML",
    )
