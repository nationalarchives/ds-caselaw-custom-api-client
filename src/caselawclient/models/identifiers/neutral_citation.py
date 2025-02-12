import re

from ds_caselaw_utils import neutral_url
from ds_caselaw_utils.types import NeutralCitationString

from caselawclient.types import DocumentIdentifierSlug

from . import Identifier, IdentifierSchema

VALID_NCN_PATTERN = re.compile(r"(^\[([0-9]{4})\] ([a-zA-Z]+)(?: ([a-zA-Z]+))? ([0-9]+)(?: \(([a-zA-Z]+)\))?$)")
"""
This is a catch-all pattern for anything which looks like a Neutral Citation, even if the court itself isn't valid. Checking that an NCN is plausibly correct is handled elsewhere.

This pattern also defines five capture groups to standardise how we interface with the elements:

- `0`: The year of the decision
- `1`: The court
- `2`: (Optionally) the jurisdiction or division, depending on the court
- `3`: The sequence number of the decision
- `4`: (Optionally) the jurisdiction or division, depending on the court

TODO: When these capture groups are being used in anger (eg to build URL slugs) you should go through and name the groups.
"""


class NeutralCitationNumberSchema(IdentifierSchema):
    """
    Identifier schema describing a Neutral Citation Number.

    https://www.iclr.co.uk/knowledge/case-law/neutral-citations/
    """

    name = "Neutral Citation Number"
    namespace = "ukncn"
    human_readable = True
    base_score_multiplier = 1.5

    @classmethod
    def validate_identifier(cls, value: str) -> bool:
        return bool(VALID_NCN_PATTERN.match(value))

    @classmethod
    def compile_identifier_url_slug(cls, value: str) -> DocumentIdentifierSlug:
        ncn_based_uri_string = neutral_url(
            NeutralCitationString(value)
        )  # TODO: At some point this should move out of utils and into this class.
        if not ncn_based_uri_string:
            raise Exception(f"Unable to convert NCN {value} into NCN-based URL slug")
        return DocumentIdentifierSlug(ncn_based_uri_string)


class NeutralCitationNumber(Identifier):
    schema = NeutralCitationNumberSchema
