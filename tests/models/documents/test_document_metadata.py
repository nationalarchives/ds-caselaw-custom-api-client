from caselawclient.factories import DocumentBodyFactory, DocumentFactory
from caselawclient.models.documents.metadata import DocumentMetadata
from caselawclient.models.identifiers.neutral_citation import NeutralCitationNumber
from caselawclient.types import DocumentCategory


class TestDocumentMetadata:
    def test_metadata(self):
        categories = [
            DocumentCategory(
                name="Breach of code of standards",
                subcategories=[
                    DocumentCategory(name="Standards not met"),
                ],
            ),
        ]

        body = DocumentBodyFactory.build()
        body.name = "Test Claimant v Test Defendant"
        body.court = "Court of Testing"
        body.jurisdiction = "SoftwareTesting"
        body.categories = categories
        body.case_number = "2010/1/dis"
        body.document_date_as_string = "2023-02-03"
        body.parties = ["Test Claimant", "Test Defendant"]
        body.judges = ["Lord Test", "Lady Example"]

        document = DocumentFactory.build(
            body=body,
            identifiers=[
                NeutralCitationNumber("[2023] UKSC 123"),
            ],
            source_name="Example Uploader",
            source_email="uploader@example.com",
            consignment_reference="TDR-12345",
        )
        document.annotation = "Test version annotation"

        assert isinstance(document.metadata, DocumentMetadata)
        assert document.metadata.name == "Test Claimant v Test Defendant"
        assert document.metadata.ncn == "[2023] UKSC 123"
        assert document.metadata.court == "Court of Testing"
        assert document.metadata.jurisdiction == "SoftwareTesting"
        assert document.metadata.categories == categories
        assert document.metadata.case_number == "2010/1/dis"
        assert document.metadata.date == "2023-02-03"
        assert document.metadata.parties == ["Test Claimant", "Test Defendant"]
        assert document.metadata.judges == ["Lord Test", "Lady Example"]
        assert document.metadata.uri == "test/2023/123"
        assert document.metadata.source_name == "Example Uploader"
        assert document.metadata.source_email == "uploader@example.com"
        assert document.metadata.consignment_reference == "TDR-12345"
        assert document.metadata.identifiers == document.identifiers
        assert document.metadata.version_annotation == "Test version annotation"

    def test_metadata_without_neutral_citation_number(self):
        document = DocumentFactory.build()

        assert document.metadata.ncn is None

    def test_metadata_as_dict(self):
        body = DocumentBodyFactory.build()
        body.name = "Test Claimant v Test Defendant"
        body.court = "Court of Testing"
        body.jurisdiction = ""
        body.categories = []
        body.case_number = ""
        body.document_date_as_string = "2023-02-03"
        body.parties = []
        body.judges = []

        document = DocumentFactory.build(body=body)
        document.annotation = ""

        assert document.metadata.as_dict() == {
            "name": "Test Claimant v Test Defendant",
            "ncn": None,
            "court": "Court of Testing",
            "jurisdiction": "",
            "categories": [],
            "case_number": "",
            "date": "2023-02-03",
            "parties": [],
            "judges": [],
            "uri": "test/2023/123",
            "source_name": "Example Uploader",
            "source_email": "uploader@example.com",
            "consignment_reference": "TDR-12345",
            "identifiers": document.identifiers,
            "version_annotation": "",
        }

    def test_metadata_as_dict_excluding_empty_values(self):
        body = DocumentBodyFactory.build()
        body.name = "Test Claimant v Test Defendant"
        body.court = "Court of Testing"
        body.jurisdiction = ""
        body.categories = []
        body.case_number = ""
        body.document_date_as_string = "2023-02-03"
        body.parties = []
        body.judges = []

        document = DocumentFactory.build(body=body)
        document.annotation = ""

        assert document.metadata.as_dict(exclude_empty=True) == {
            "name": "Test Claimant v Test Defendant",
            "court": "Court of Testing",
            "date": "2023-02-03",
            "uri": "test/2023/123",
            "source_name": "Example Uploader",
            "source_email": "uploader@example.com",
            "consignment_reference": "TDR-12345",
            "identifiers": document.identifiers,
        }
