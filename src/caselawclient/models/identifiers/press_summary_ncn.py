from .neutral_citation import NeutralCitationNumber, NeutralCitationNumberSchema


class PressSummaryRelatedNCNIdentifierSchema(NeutralCitationNumberSchema):
    """
    Identifier schema for relating a Press Summary to a Judgment with a given NCN
    """

    name = "Press Summary relates to NCN"
    namespace = "uksummaryofncn"
    human_readable = True
    base_score_multiplier = 0.5

    @classmethod
    def compile_identifier_url_slug(cls, value: str) -> str:
        return super().compile_identifier_url_slug(value) + "/press-summary"


class PressSummaryRelatedNCNIdentifier(NeutralCitationNumber):
    schema = NeutralCitationNumberSchema
