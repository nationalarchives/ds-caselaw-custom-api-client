import re
from typing import TYPE_CHECKING

from sqids import Sqids

from caselawclient.types import DocumentIdentifierSlug

from . import Identifier, IdentifierSchema

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient


VALID_FCLID_PATTERN = re.compile(r"^[bcdfghjkmnpqrstvwxyz23456789]{4,}$")

FCLID_MINIMUM_LENGTH = 8
FCLID_ALPHABET = "bcdfghjkmnpqrstvwxyz23456789"

sqids = Sqids(
    min_length=FCLID_MINIMUM_LENGTH,
    alphabet=FCLID_ALPHABET,
)


class FindCaseLawIdentifierSchema(IdentifierSchema):
    """
    Identifier schema describing a Find Case Law Identifier.
    """

    name = "Find Case Law Identifier"
    namespace = "fclid"
    human_readable = False
    base_score_multiplier = 0.6

    @classmethod
    def validate_identifier(cls, value: str) -> bool:
        return bool(VALID_FCLID_PATTERN.match(value))

    @classmethod
    def compile_identifier_url_slug(cls, value: str) -> DocumentIdentifierSlug:
        return DocumentIdentifierSlug("tna." + value)

    @classmethod
    def mint(cls, api_client: "MarklogicApiClient") -> "FindCaseLawIdentifier":
        """Generate a totally new Find Case Law identifier."""
        next_sequence_number = api_client.get_next_document_sequence_number()
        new_identifier = sqids.encode([next_sequence_number])
        return FindCaseLawIdentifier(value=new_identifier)


class FindCaseLawIdentifier(Identifier):
    schema = FindCaseLawIdentifierSchema
