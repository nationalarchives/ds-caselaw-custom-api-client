import unittest
from unittest.mock import patch

from lxml import etree
from test_identifiers import TestIdentifier

from caselawclient.models.identifiers.collection import IdentifiersCollection
from caselawclient.models.identifiers.unpacker import (
    IDENTIFIER_NAMESPACE_MAP,
    unpack_all_identifiers_from_etree,
    unpack_an_identifier_from_etree,
)


class TestIdentifierNamespaceMapping:
    def test_identifier_consistency_in_namespace_map(self):
        """Sense-check that identifiers in the namespace map actually match those in the identifier class."""
        for namespace, identifier in IDENTIFIER_NAMESPACE_MAP.items():
            assert namespace == identifier.schema.namespace


class TestIdentifierUnpacking(unittest.TestCase):
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

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_identifier_deprecated(self):
        xml_tree = etree.fromstring("""
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
                <deprecated>true</deprecated>
            </identifier>
        """)

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.deprecated is True

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_identifier_undeprecated_without_value(self):
        xml_tree = etree.fromstring("""
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
            </identifier>
        """)

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.deprecated is False

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_identifier_undeprecated_with_value(self):
        xml_tree = etree.fromstring("""
            <identifier>
                <namespace>test</namespace>
                <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                <value>TEST-123</value>
                <deprecated>false</deprecated>
            </identifier>
        """)

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.deprecated is False

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_unknown_identifier(self):
        xml_tree = etree.fromstring("""
            <identifier>
                <namespace>unknown</namespace>
                <uuid>86888618-a9a0-44e3-af4a-5b10dbb910c0</uuid>
                <value>UK-123</value>
            </identifier>
        """)

        with self.assertWarnsRegex(Warning, "Identifier type unknown is not known."):
            unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert unpacked_identifier is None

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_unpack_multiple_identifiers(self):
        """Validate that unpacking a list of identifiers where some are known and some are unknown behaves as expected."""
        xml_tree = etree.fromstring("""
            <identifiers>
                <identifier>
                    <namespace>test</namespace>
                    <uuid>2d80bf1d-e3ea-452f-965c-041f4399f2dd</uuid>
                    <value>TEST-123</value>
                </identifier>
                <identifier>
                    <namespace>unknown</namespace>
                    <uuid>86888618-a9a0-44e3-af4a-5b10dbb910c0</uuid>
                    <value>UK-123</value>
                </identifier>
            </identifiers>
        """)

        with self.assertWarnsRegex(Warning, "Identifier type unknown is not known."):
            unpacked_identifiers = unpack_all_identifiers_from_etree(xml_tree)

        assert type(unpacked_identifiers) is IdentifiersCollection
        assert len(unpacked_identifiers) == 1
        assert type(unpacked_identifiers["2d80bf1d-e3ea-452f-965c-041f4399f2dd"]) is TestIdentifier
        assert "86888618-a9a0-44e3-af4a-5b10dbb910c0" not in unpacked_identifiers


class TestIdentifierPackUnpackRoundTrip:
    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_roundtrip_identifier(self):
        """Check that if we convert a single Identifier to XML and back again we get the same thing out at the far end."""

        original_identifier = TestIdentifier(value="TEST-123")

        xml_tree = original_identifier.as_xml_tree

        unpacked_identifier = unpack_an_identifier_from_etree(xml_tree)

        assert type(unpacked_identifier) is TestIdentifier
        assert unpacked_identifier.uuid == original_identifier.uuid
        assert unpacked_identifier.value == "TEST-123"

    @patch("caselawclient.models.identifiers.unpacker.IDENTIFIER_NAMESPACE_MAP", {"test": TestIdentifier})
    def test_roundtrip_identifiers(self):
        """Check that if we convert multiple identifiers to XML and back again we get the same things out at the far end."""
        original_identifiers = IdentifiersCollection()
        original_identifiers.add(TestIdentifier(uuid="id-a1", value="TEST-123"))
        original_identifiers.add(TestIdentifier(uuid="id-b2", value="TEST-456", deprecated=True))

        xml_tree = original_identifiers.as_etree

        unpacked_identifiers = unpack_all_identifiers_from_etree(xml_tree)

        unpacked_identifier_1 = unpacked_identifiers["id-a1"]
        unpacked_identifier_2 = unpacked_identifiers["id-b2"]

        assert type(unpacked_identifier_1) is TestIdentifier
        assert unpacked_identifier_1.uuid == "id-a1"
        assert unpacked_identifier_1.value == "TEST-123"
        assert unpacked_identifier_1.deprecated is False

        assert type(unpacked_identifier_1) is TestIdentifier
        assert unpacked_identifier_2.uuid == "id-b2"
        assert unpacked_identifier_2.value == "TEST-456"
        assert unpacked_identifier_2.deprecated is True
