from unittest.mock import patch

from lxml import etree
from test_identifiers import TestIdentifier

from caselawclient.models.identifiers import Identifiers
from caselawclient.models.identifiers.unpacker import unpack_all_identifiers_from_etree, unpack_an_identifier_from_etree


class TestIdentifierUnpacking:
    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_identifier(self):
        xml_tree = etree.fromstring("""
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
            </identifier>
        """)

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.uuid == "2d80bf1d-e3ea-452f-965c-041f4399f2dd"
        assert unpacked_identifier.value == "TEST-123"


class TestIdentifierPackUnpackRoundTrip:
    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_roundtrip_identifier(self):
        """Check that if we convert an Identifier to XML and back again we get the same thing out at the far end."""

        original_identifier = TestIdentifier(value="TEST-123")

        xml_tree = original_identifier.as_xml_tree

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.uuid == original_identifier.uuid
        assert unpacked_identifier.value == "TEST-123"

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_roundtrip_identifiers(self):
        """Check that if we convert an Identifier to XML and back again we get the same thing out at the far end."""
        uuid = "id-1"
        original_identifiers = Identifiers()
        original_identifiers.add(TestIdentifier(uuid=uuid, value="TEST-123"))

        xml_tree = original_identifiers.as_etree

        unpacked_identifiers = unpack_all_identifiers_from_etree(xml_tree)
        unpacked_identifier = unpacked_identifiers[uuid]

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.uuid == uuid
        assert unpacked_identifier.value == "TEST-123"
