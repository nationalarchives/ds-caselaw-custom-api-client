import pytest

from caselawclient.models.identifiers import press_summary_ncn


class TestPressSummaryRelatedNCNIdentifierSchemaSchemaImplementation:
    """
    This class tests that we have correctly implemented a schema describing Neutral Citations.
    """

    def test_ncn_schema_configuration(self):
        """
        Check that the basics of the schema have been set.
        """

        schema = press_summary_ncn.PressSummaryRelatedNCNIdentifierSchema

        assert schema.name == "Press Summary relates to NCN"
        assert schema.namespace == "uksummaryofncn"

    @pytest.mark.parametrize(
        ("value", "slug"),
        [
            ("[2022] UKSC 1", "uksc/2022/1/press-summary"),
            ("[1604] EWCA Crim 555", "ewca/crim/1604/555/press-summary"),
            ("[2022] EWHC 1 (Comm)", "ewhc/comm/2022/1/press-summary"),
            ("[1999] EWCOP 7", "ewcop/1999/7/press-summary"),
            ("[2022] UKUT 1 (IAC)", "ukut/iac/2022/1/press-summary"),
            ("[2022] EAT 1", "eat/2022/1/press-summary"),
            ("[2022] UKFTT 1 (TC)", "ukftt/tc/2022/1/press-summary"),
            ("[2022] UKFTT 1 (GRC)", "ukftt/grc/2022/1/press-summary"),
            ("[2022] EWHC 1 (KB)", "ewhc/kb/2022/1/press-summary"),
        ],
    )
    def test_ncn_schema_compile_url_slug(self, value, slug):
        schema = press_summary_ncn.PressSummaryRelatedNCNIdentifierSchema
        assert schema.compile_identifier_url_slug(value) == slug
