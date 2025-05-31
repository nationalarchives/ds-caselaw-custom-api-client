import pytest
from lxml import etree

from caselawclient.factories import DocumentFactory
from caselawclient.models.identifiers import Identifiers, UUIDMismatchError
from tests.models.identifiers.test_identifiers import TestIdentifier


class TestDocumentIdentifiers:
    def test_add_identifiers(self):
        document = DocumentFactory.build(identifiers=[])

        identifier_1 = TestIdentifier(uuid="id-1", value="TEST-123")
        identifier_2 = TestIdentifier(uuid="id-2", value="TEST-456")
        document.identifiers.add(identifier_1)
        document.identifiers.add(identifier_2)

        assert document.identifiers == {
            "id-1": identifier_1,
            "id-2": identifier_2,
        }

    def test_validate(self):
        identifiers = Identifiers({"id-1": TestIdentifier(uuid="id-2", value="TEST-123")})
        with pytest.raises(UUIDMismatchError):
            identifiers.validate()

    def test_identifiers_as_etree(self):
        document = DocumentFactory.build(identifiers=[])

        identifier_1 = TestIdentifier(uuid="e28e3ef1-85ed-4997-87ee-e7428a6cc02e", value="TEST-123")
        identifier_2 = TestIdentifier(uuid="14ce4b3b-03c8-44f9-a29e-e02ce35fe136", value="TEST-456", deprecated=True)
        document.identifiers.add(identifier_1)
        document.identifiers.add(identifier_2)

        expected_xml = """
            <identifiers>
                <identifier>
                    <namespace>test</namespace>
                    <uuid>e28e3ef1-85ed-4997-87ee-e7428a6cc02e</uuid>
                    <value>TEST-123</value>
                    <deprecated>false</deprecated>
                    <url_slug>test-123</url_slug>
                </identifier>
                <identifier>
                    <namespace>test</namespace>
                    <uuid>14ce4b3b-03c8-44f9-a29e-e02ce35fe136</uuid>
                    <value>TEST-456</value>
                    <deprecated>true</deprecated>
                    <url_slug>test-456</url_slug>
                </identifier>
            </identifiers>
        """

        assert etree.canonicalize(document.identifiers.as_etree, strip_text=True) == etree.canonicalize(
            etree.fromstring(expected_xml), strip_text=True
        )
