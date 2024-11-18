import re

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
"""


class NeutralCitationNumberSchema(IdentifierSchema):
    """
    Identifier schema describing a Neutral Citation Number.

    https://www.iclr.co.uk/knowledge/case-law/neutral-citations/
    """

    name = "Neutral Citation Number"
    namespace = "ukncn"

    @classmethod
    def validate_identifier(cls, value: str) -> bool:
        return bool(VALID_NCN_PATTERN.match(value))


class NeutralCitationNumber(Identifier):
    schema = NeutralCitationNumberSchema
