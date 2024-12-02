import pytest
from lxml import etree

from caselawclient.models.identifiers import Identifier, Identifiers, IdentifierSchema


@pytest.fixture
def identifiers():
    return Identifiers(
        {"id-1": Identifier(uuid="id-1", value="TEST-111"), "id-2": Identifier(uuid="id-2", value="TEST-222")}
    )


@pytest.fixture
def id3():
    return Identifier(uuid="id-3", value="TEST-333")


class TestIdentifierSchema(IdentifierSchema):
    __test__ = False

    name = "Test Schema"
    namespace = "test"


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
            </identifier>
        """
        assert etree.canonicalize(identifier.as_xml_tree, strip_text=True) == etree.canonicalize(
            etree.fromstring(expected_xml), strip_text=True
        )


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
