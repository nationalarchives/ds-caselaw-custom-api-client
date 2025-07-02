from unittest.mock import patch

import pytest
from lxml import etree

from caselawclient.models.documents import Document
from caselawclient.models.identifiers import Identifier, IdentifierSchema
from caselawclient.models.identifiers.collection import IdentifiersCollection
from caselawclient.models.identifiers.exceptions import IdentifierValidationException, UUIDMismatchError
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber
from caselawclient.types import DocumentIdentifierSlug


class TestIdentifierSchema(IdentifierSchema):
    __test__ = False

    name = "Test Schema"
    namespace = "test"
    human_readable = True
    base_score_multiplier = 2.5

    @classmethod
    def compile_identifier_url_slug(cls, value: str) -> DocumentIdentifierSlug:
        return DocumentIdentifierSlug(value.lower())

    @classmethod
    def validate_identifier_value(cls, value):
        return value.startswith("TEST-")


class TestIdentifier(Identifier):
    __test__ = False

    schema = TestIdentifierSchema


@pytest.fixture
def identifiers():
    return IdentifiersCollection(
        {"id-1": TestIdentifier(uuid="id-1", value="TEST-111"), "id-2": TestIdentifier(uuid="id-2", value="TEST-222")}
    )


TEST_NCN_1701 = NeutralCitationNumber(value="[1701] UKSC 999", uuid="id-1701")
TEST_NCN_1234 = NeutralCitationNumber(value="[1234] UKSC 999", uuid="id-1234")
TEST_IDENTIFIER_999 = TestIdentifier("TEST-999")


@pytest.fixture
def mixed_identifiers():
    return IdentifiersCollection(
        {
            "id-A": TEST_NCN_1701,
            "id-B": TEST_IDENTIFIER_999,
            "id-C": TEST_NCN_1234,
        }
    )


@pytest.fixture
def id3():
    return TestIdentifier(uuid="id-3", value="TEST-333")


class TestIdentifierBase:
    def test_uuid_setting(self):
        """Ensure that if a UUID is provided when initialising an Identifier that it is properly stored."""
        identifier = TestIdentifier(uuid="2d80bf1d-e3ea-452f-965c-041f4399f2dd", value="TEST-123")
        assert identifier.uuid == "2d80bf1d-e3ea-452f-965c-041f4399f2dd"

    def test_xml_representation(self):
        """Ensure that an identifer generates the expected representation of itself as XML."""
        identifier = TestIdentifier(uuid="2d80bf1d-e3ea-452f-965c-041f4399f2dd", value="TEST-123")

        expected_xml = """
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
                <deprecated>false</deprecated>
                <url_slug>test-123</url_slug>
            </identifier>
        """
        assert etree.canonicalize(identifier.as_xml_tree, strip_text=True) == etree.canonicalize(
            etree.fromstring(expected_xml), strip_text=True
        )

    def test_validates_on_init(self):
        """Check that when you initialise a new identifier the schema.validate_identifier_value method is called to validate the value."""
        with patch.object(TestIdentifierSchema, "validate_identifier_value") as mock_validate_identifier_value:
            TestIdentifier(value="TEST-123")
            mock_validate_identifier_value.assert_called_once_with(value="TEST-123")

    def test_validate_on_init_raises_on_false(self):
        """Check that when you initialise a new identifier with an invalid value it raises an exception."""
        with pytest.raises(IdentifierValidationException):
            TestIdentifier(value="WRONG-123")

    def test_same_as_different_types(self):
        id_a = TestIdentifier("TEST-134")
        id_b = NeutralCitationNumber("[2025] UKSC 1")
        assert not id_a.same_as(id_b)

    def test_same_as_same_type_and_value(self):
        id_a = NeutralCitationNumber("[2025] UKSC 1")
        id_b = NeutralCitationNumber("[2025] UKSC 1")
        assert id_a.same_as(id_b)

    def test_same_as_different_values(self):
        id_a = NeutralCitationNumber("[2024] EWHC 1 (Pat)")
        id_b = NeutralCitationNumber("[2025] UKSC 1")
        assert not id_a.same_as(id_b)

    def test_str(self):
        assert f"{TEST_NCN_1234}" == "[1234] UKSC 999"

    def test_repr(self):
        assert f"{TEST_NCN_1234!r}" == "<Neutral Citation Number [1234] UKSC 999: id-1234>"


class TestIdentifiersCRUD:
    def test_delete(self, identifiers: IdentifiersCollection):
        del identifiers["id-1"]
        assert len(identifiers) == 1
        assert "id-2" in identifiers

    def test_delete_identifier(self, identifiers: IdentifiersCollection):
        id1 = identifiers["id-1"]
        del identifiers[id1]
        assert len(identifiers) == 1
        assert "id-2" in identifiers

    def test_add_identifier(self, identifiers: IdentifiersCollection, id3: TestIdentifier):
        identifiers.add(id3)
        assert identifiers["id-3"] == id3
        assert len(identifiers) == 3

    def test_contains(self, identifiers: IdentifiersCollection):
        assert identifiers.contains(TestIdentifier(value="TEST-111"))
        assert not identifiers.contains(TestIdentifier(value="TEST-333"))

    def test_of_type(self, mixed_identifiers: IdentifiersCollection):
        only_ncns = mixed_identifiers.of_type(NeutralCitationNumber)
        assert "TEST-999" not in str(only_ncns)
        assert "[1701] UKSC 999" in str(only_ncns)
        assert "[1234] UKSC 999" in str(only_ncns)

    def test_delete_type(self, mixed_identifiers: IdentifiersCollection):
        mixed_identifiers.delete_type(NeutralCitationNumber)
        assert "TEST-999" in str(mixed_identifiers)
        assert "[1701] UKSC 999" not in str(mixed_identifiers)
        assert "[1234] UKSC 999" not in str(mixed_identifiers)


class TestIdentifierScoring:
    def test_base_scoring(self):
        identifier = TestIdentifier(value="TEST-123")
        assert identifier.score == 2.5

    def test_sorting(self, mixed_identifiers: IdentifiersCollection):
        assert mixed_identifiers.by_score() == [TEST_IDENTIFIER_999, TEST_NCN_1701, TEST_NCN_1234]

    def test_preferred_identifier(self, mixed_identifiers: IdentifiersCollection):
        assert mixed_identifiers.preferred() == TEST_IDENTIFIER_999

    def test_sorting_with_type(self, mixed_identifiers: IdentifiersCollection):
        assert mixed_identifiers.by_score(type=NeutralCitationNumber) == [TEST_NCN_1701, TEST_NCN_1234]

    def test_preferred_identifier_with_type(self, mixed_identifiers: IdentifiersCollection):
        assert mixed_identifiers.preferred(type=NeutralCitationNumber) == TEST_NCN_1701


class TestIdentifierValidation:
    def test_validate_uuids_match_keys(self):
        identifiers = IdentifiersCollection({"id-1": TestIdentifier(uuid="id-2", value="TEST-123")})
        with pytest.raises(UUIDMismatchError):
            identifiers.validate_uuids_match_keys()

    def test_perform_all_validations_runs_expected_validations(self, mock_api_client):
        """Check that when we try to validate an entire set of Identifiers we do what is expected"""
        identifier_1 = TestIdentifier(uuid="id-1", value="TEST-123")
        identifier_2 = TestIdentifier(uuid="id-2", value="TEST-456")
        identifiers = IdentifiersCollection(
            {
                "id-1": identifier_1,
                "id-2": identifier_2,
            }
        )
        with (
            patch.object(identifiers, "validate_uuids_match_keys") as mock_validate_uuids_match_keys,
            patch.object(identifier_1, "perform_all_validations") as mock_identifier_1_validate,
            patch.object(identifier_2, "perform_all_validations") as mock_identifier_2_validate,
        ):
            identifiers.perform_all_validations(document_type=Document, api_client=mock_api_client)
            mock_validate_uuids_match_keys.assert_called_once()
            mock_identifier_1_validate.assert_called_once_with(document_type=Document, api_client=mock_api_client)
            mock_identifier_2_validate.assert_called_once_with(document_type=Document, api_client=mock_api_client)
