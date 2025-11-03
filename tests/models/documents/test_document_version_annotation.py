import json

import pytest

from caselawclient.models.documents import Document, DocumentURIString


class TestAnnotations:
    def test_annotation(self, mock_api_client):
        """Check that getting a document's annotation string performs as expected."""
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        mock_api_client.get_version_annotation.return_value = "Test simple annotation string"

        assert document.annotation == "Test simple annotation string"

        mock_api_client.get_version_annotation.assert_called_once_with("test/1234")

    def test_structured_annotation_with_simple_string(self, mock_api_client):
        """Check that if you try to pull structured annotation on a document with a naive string you get an exception."""
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        document.annotation = "Test simple annotation string"

        with pytest.raises(ValueError, match="Test simple annotation string"):
            document.structured_annotation

    def test_structured_annotation_with_invalid_json(self, mock_api_client):
        """Check that if you try to pull structured annotation on a document with an incorrect JSON structure you get an exception."""
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        document.annotation = '{"value":"Unexpected JSON structure"}'

        with pytest.raises(ValueError, match="{'value': 'Unexpected JSON structure'}"):
            document.structured_annotation

    def test_structured_annotation_with_valid_json(self, mock_api_client):
        """Check that if you try to pull structured annotation on a document with correct JSON you get the values as expected."""
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        version_annotation_json = """{
    "type": "submission",
    "calling_function": "insert_document_xml",
    "calling_agent": "ds-caselaw-ingester/unknown ds-caselaw-marklogic-api-client/41.1.3",
    "automated": false,
    "message": "New document submitted by TDR user",
    "payload": {
        "tre_raw_metadata": {
            "parameters": {
                "TRE": {
                    "reference": "TRE-TDR-2025-ABCD",
                    "payload": {
                        "filename": "Vedanta Resources plc and another (Appellants) v Lungowe and others (Respondents) PS.docx",
                        "xml": "TDR-2025-ABCD.xml",
                        "metadata": "TRE-TDR-2025-ABCD-metadata.json",
                        "images": [
                            "image1.png"
                        ],
                        "log": "parser.log"
                    }
                },
                "PARSER": {
                    "documentType": "pressSummary",
                    "uri": "https://caselaw.nationalarchives.gov.uk/id/uksc/2025/1234/press-summary/1",
                    "court": "UKSC",
                    "cite": null,
                    "date": "2019-04-10",
                    "name": "Press Summary of Test Case",
                    "extensions": null,
                    "attachments": [],
                    "error-messages": []
                },
                "TDR": {
                    "Consignment-Type": "judgment",
                    "Bag-Creator": "TDRExportv0.0.348",
                    "Consignment-Start-Datetime": "2025-10-11T09:44:36Z",
                    "Consignment-Series": null,
                    "Source-Organization": "HM Courts and Tribunals Service",
                    "Contact-Name": "Test User",
                    "Consignment-Include-Top-Level-Folder": "false",
                    "Internal-Sender-Identifier": "TDR-2025-ABCD",
                    "Consignment-Completed-Datetime": "2025-10-11T09:48:00Z",
                    "Consignment-Export-Datetime": "2025-10-11T09:48:49Z",
                    "Contact-Email": "user@example.com",
                    "Payload-Oxum": "55460.1",
                    "Bagging-Date": "2025-10-11",
                    "Document-Checksum-sha256": "6328e91281a605b0098a12e919c8893a66e15d49c61905cebee04d3dc7ee9544",
                    "File-Reference": "A1B2C",
                    "UUID": "e66a5dda-427e-4f56-9885-ca9255303812",
                    "Judgment-Type": null,
                    "Judgment-Update": null,
                    "Judgment-Update-Type": null,
                    "Judgment-Update-Details": null,
                    "Judgment-Neutral-Citation": null,
                    "Judgment-No-Neutral-Citation": null,
                    "Judgment-Reference": null
                }
            }
        },
        "tdr_reference": "TDR-2025-ABCD",
        "submitter": {
            "name": "Test User",
            "email": "user@example.com"
        }
    }
}"""

        document.annotation = version_annotation_json

        assert document.structured_annotation == json.loads(version_annotation_json)
