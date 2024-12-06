import json
from typing import NamedTuple

from caselawclient.models.documents import DocumentURIString
from caselawclient.xquery_type_dicts import MarkLogicDocumentURIString


class IdentifierResolutions(list["IdentifierResolution"]):
    """
    A list of candidate MarkLogic documents which correspond to a Public UI uri

    MarkLogic returns a list of dictionaries; IdentifierResolution handles a single dictionary
    which corresponds to a single identifier to MarkLogic document mapping.

    see `xquery/resolve_from_identifier.xqy` and `resolve_from_identifier` in `Client.py`
    """

    @staticmethod
    def from_marklogic_output(table: list[str]) -> "IdentifierResolutions":
        return IdentifierResolutions(list(IdentifierResolution.from_marklogic_output(row) for row in table))

    def published(self) -> "IdentifierResolutions":
        "Filter the list so that only published documents are returned"
        return IdentifierResolutions(list(x for x in self if x.document_published))


class IdentifierResolution(NamedTuple):
    """A single response from MarkLogic about a single identifier / document mapping"""

    identifier_uuid: str
    document_uri: MarkLogicDocumentURIString
    identifier_slug: DocumentURIString
    document_published: bool

    @staticmethod
    def from_marklogic_output(raw_row: str) -> "IdentifierResolution":
        row = json.loads(raw_row)
        return IdentifierResolution(
            identifier_uuid=row["documents.compiled_url_slugs.identifier_uuid"],
            document_uri=MarkLogicDocumentURIString(row["documents.compiled_url_slugs.document_uri"]),
            identifier_slug=DocumentURIString(row["documents.compiled_url_slugs.identifier_slug"]),
            document_published=row["documents.compiled_url_slugs.document_published"] == "true",
        )
