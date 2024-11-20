from lxml import etree

from caselawclient.factories import DocumentFactory
from tests.models.identifiers.test_identifiers import TestIdentifier


class TestDocumentIdentifiers:
    def test_add_identifiers(self):
        document = DocumentFactory.build()

        identifier_1 = TestIdentifier(uuid="e28e3ef1-85ed-4997-87ee-e7428a6cc02e", value="TEST-123")
        identifier_2 = TestIdentifier(uuid="14ce4b3b-03c8-44f9-a29e-e02ce35fe136", value="TEST-456")
        document.add_identifier(identifier_1)
        document.add_identifier(identifier_2)

        assert document.identifiers == {
            "e28e3ef1-85ed-4997-87ee-e7428a6cc02e": identifier_1,
            "14ce4b3b-03c8-44f9-a29e-e02ce35fe136": identifier_2,
        }

    def test_identifiers_as_etree(self):
        document = DocumentFactory.build()

        identifier_1 = TestIdentifier(uuid="e28e3ef1-85ed-4997-87ee-e7428a6cc02e", value="TEST-123")
        identifier_2 = TestIdentifier(uuid="14ce4b3b-03c8-44f9-a29e-e02ce35fe136", value="TEST-456")
        document.add_identifier(identifier_1)
        document.add_identifier(identifier_2)

        expected_xml = """
            <identifiers>
                <identifier>
                    <namespace>test</namespace>
                    <uuid>e28e3ef1-85ed-4997-87ee-e7428a6cc02e</uuid>
                    <value>TEST-123</value>
                </identifier>
                <identifier>
                    <namespace>test</namespace>
                    <uuid>14ce4b3b-03c8-44f9-a29e-e02ce35fe136</uuid>
                    <value>TEST-456</value>
                </identifier>
            </identifiers>
        """

        assert etree.canonicalize(document.identifiers_as_etree(), strip_text=True) == etree.canonicalize(
            etree.fromstring(expected_xml), strip_text=True
        )
