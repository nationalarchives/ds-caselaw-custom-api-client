import pytest
from lxml import etree

from caselawclient.models.identifiers import Identifier, Identifiers, IdentifierSchema
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber


@pytest.fixture
def identifiers():
    return Identifiers(
        {"id-1": TestIdentifier(uuid="id-1", value="TEST-111"), "id-2": TestIdentifier(uuid="id-2", value="TEST-222")}
    )


@pytest.fixture
def mixed_identifiers():
    return Identifiers(
        {
            "id-A": NeutralCitationNumber(value="[1701] UKSC 999"),
            "id-B": TestIdentifier("TEST-999"),
            "id-C": NeutralCitationNumber(value="[1234] UKSC 999"),
        }
    )


@pytest.fixture
def id3():
    return TestIdentifier(uuid="id-3", value="TEST-333")


class TestIdentifierSchema(IdentifierSchema):
    __test__ = False

    name = "Test Schema"
    namespace = "test"

    @classmethod
    def compile_identifier_url_slug(cls, value: str) -> str:
        return value.lower()


class TestIdentifier(Identifier):
    __test__ = False

    schema = TestIdentifierSchema


class TestIdentifierBase:
    def test_uuid_setting(self):
        """Ensure that if a UUID is provided when initialising an Identifier that it is properly stored."""
        identifier = Identifier(uuid="2d80bf1d-e3ea-452f-965c-041f4399f2dd", value="TEST-123")
        assert identifier.uuid == "2d80bf1d-e3ea-452f-965c-041f4399f2dd"

    def test_xml_representation(self):
        """Ensure that an identifer generates the expected representation of itself as XML."""
        identifier = TestIdentifier(uuid="2d80bf1d-e3ea-452f-965c-041f4399f2dd", value="TEST-123")

        expected_xml = """
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
                <url_slug>test-123</url_slug>
            </identifier>
        """
        assert etree.canonicalize(identifier.as_xml_tree, strip_text=True) == etree.canonicalize(
            etree.fromstring(expected_xml), strip_text=True
        )

    def test_same_as_different_types(self):
        id_a = TestIdentifier("X")
        id_b = NeutralCitationNumber("X")
        assert not id_a.same_as(id_b)

    def test_same_as_same_type_and_value(self):
        id_a = NeutralCitationNumber("X")
        id_b = NeutralCitationNumber("X")
        assert id_a.same_as(id_b)

    def test_same_as_different_values(self):
        id_a = NeutralCitationNumber("Y")
        id_b = NeutralCitationNumber("X")
        assert not id_a.same_as(id_b)


class TestIdentifiersCRUD:
    def test_delete(self, identifiers):
        del identifiers["id-1"]
        assert len(identifiers) == 1
        assert "id-2" in identifiers

    def test_delete_identifier(self, identifiers):
        id1 = identifiers["id-1"]
        del identifiers[id1]
        assert len(identifiers) == 1
        assert "id-2" in identifiers

    def test_add_identifier(self, identifiers, id3):
        identifiers.add(id3)
        assert identifiers["id-3"] == id3
        assert len(identifiers) == 3

    def test_contains(self, identifiers):
        assert identifiers.contains(TestIdentifier(value="TEST-111"))
        assert not identifiers.contains(TestIdentifier(value="TEST-333"))
        assert not identifiers.contains(NeutralCitationNumber(value="TEST-111"))

    def test_of_type(self, mixed_identifiers):
        only_ncns = mixed_identifiers.of_type(NeutralCitationNumber)
        assert "TEST-999" not in str(only_ncns)
        assert "[1701] UKSC 999" in str(only_ncns)
        assert "[1234] UKSC 999" in str(only_ncns)

    def test_delete_type(self, mixed_identifiers):
        mixed_identifiers.delete_type(NeutralCitationNumber)
        assert "TEST-999" in str(mixed_identifiers)
        assert "[1701] UKSC 999" not in str(mixed_identifiers)
        assert "[1234] UKSC 999" not in str(mixed_identifiers)
