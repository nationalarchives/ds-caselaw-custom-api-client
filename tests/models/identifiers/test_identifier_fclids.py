from caselawclient.models.identifiers import fclid


class TestFCLIDSchemaImplementation:
    """
    This class tests that we have correctly implemented a schema describing FCLIDs.
    """

    def test_fclid_schema_configuration(self):
        """
        Check that the basics of the schema have been set.

        nb: FCLIDs are a bit of a special case within the system, so you should exercise caution before changing anything in the schema.
        """

        schema = fclid.FindCaseLawIdentifierSchema

        assert schema.name == "Find Case Law Identifier"
        assert schema.namespace == "fclid"
        assert schema.allow_editing is False
        assert schema.require_globally_unique is True

    def test_fclid_schema_compile_url_slug(self):
        schema = fclid.FindCaseLawIdentifierSchema
        assert schema.compile_identifier_url_slug("a1b2c3d4") == "tna.a1b2c3d4"
