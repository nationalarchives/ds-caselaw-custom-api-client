from __future__ import annotations

from .documents import Document


class ParserLog(Document):
    """
    A fundamentally different type of Document that is not part of the akomaNtoso spec
    """

    document_noun = "parser log"
    document_noun_plural = "parser logs"
    type_collection_name = "parser-log"
