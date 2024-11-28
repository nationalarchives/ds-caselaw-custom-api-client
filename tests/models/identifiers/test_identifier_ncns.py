import pytest

from caselawclient.models.identifiers import neutral_citation


class TestNeutralCitationSchemaImplementation:
    """
    This class tests that we have correctly implemented a schema describing Neutral Citations.
    """

    def test_ncn_schema_configuration(self):
        """
        Check that the basics of the schema have been set.
        """

        schema = neutral_citation.NeutralCitationNumberSchema

        assert schema.name == "Neutral Citation Number"
        assert schema.namespace == "ukncn"

    @pytest.mark.parametrize(
        "value",
        [
            "[2022] UKSC 1",
            "[1604] EWCA Crim 555",
            "[2022] EWHC 1 (Comm)",
            "[1999] EWCOP 7",
            "[2022] UKUT 1 (IAC)",
            "[2022] EAT 1",
            "[2022] UKFTT 1 (TC)",
            "[2022] UKFTT 1 (GRC)",
            "[2022] EWHC 1 (KB)",
        ],
    )
    def test_ncn_schema_validation_passes(self, value):
        schema = neutral_citation.NeutralCitationNumberSchema
        assert schema.validate_identifier(value) is True

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "bananas",
            "1604] EWCA Crim 555",
            "[2022 EWHC 1 Comm",
            "[1999] EWCOP",
            "[2022] UKUT B1 IAC",
            "[2022] EAT A",
            "[2022] EWCA Crim Civ 123",
        ],
    )
    def test_ncn_schema_validation_fails(self, value):
        schema = neutral_citation.NeutralCitationNumberSchema
        assert schema.validate_identifier(value) is False

    @pytest.mark.parametrize(
        ("value", "slug"),
        [
            ("[2022] UKSC 1", "uksc/2022/1"),
            ("[1604] EWCA Crim 555", "ewca/crim/1604/555"),
            ("[2022] EWHC 1 (Comm)", "ewhc/comm/2022/1"),
            ("[1999] EWCOP 7", "ewcop/1999/7"),
            ("[2022] UKUT 1 (IAC)", "ukut/iac/2022/1"),
            ("[2022] EAT 1", "eat/2022/1"),
            ("[2022] UKFTT 1 (TC)", "ukftt/tc/2022/1"),
            ("[2022] UKFTT 1 (GRC)", "ukftt/grc/2022/1"),
            ("[2022] EWHC 1 (KB)", "ewhc/kb/2022/1"),
        ],
    )
    def test_ncn_schema_compile_url_slug(self, value, slug):
        schema = neutral_citation.NeutralCitationNumberSchema
        assert schema.compile_identifier_url_slug(value) == slug
