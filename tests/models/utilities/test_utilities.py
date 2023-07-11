import os
from unittest.mock import Mock, patch

from caselawclient.models.utilities import (
    extract_version,
    get_judgment_root,
    render_versions,
)
from caselawclient.models.utilities.aws import build_new_key, copy_assets


class TestUtils:
    def test_get_judgment_root_error(self):
        xml = "<error>parser.log contents</error>"
        assert get_judgment_root(xml) == "error"

    def test_get_judgment_root_akomantoso(self):
        xml = (
            "<akomaNtoso xmlns:uk='https://caselaw.nationalarchives.gov.uk/akn' "
            "xmlns='http://docs.oasis-open.org/legaldocml/ns/akn/3.0'>judgment</akomaNtoso>"
        )
        assert (
            get_judgment_root(xml)
            == "{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}akomaNtoso"
        )

    def test_get_judgment_root_malformed_xml(self):
        # Should theoretically never happen but test anyway
        xml = "<error>malformed xml"
        assert get_judgment_root(xml) == "error"


class TestVersionUtils:
    def test_extract_version_uri(self):
        uri = "/ewhc/ch/2022/1178_xml_versions/2-1178.xml"
        assert extract_version(uri) == 2

    def test_extract_version_failure(self):
        uri = "/failures/TDR-2022-DBF_xml_versions/1-TDR-2022-DBF.xml"
        assert extract_version(uri) == 1

    def test_extract_version_not_found(self):
        uri = "some-other-string"
        assert extract_version(uri) == 0

    def test_render_versions(self):
        version_parts = [
            Mock(text="/ewhc/ch/2022/1178_xml_versions/3-1178.xml"),
            Mock(text="/ewhc/ch/2022/1178_xml_versions/2-1178.xml"),
            Mock(text="/ewhc/ch/2022/1178_xml_versions/1-1178.xml"),
        ]
        requests_toolbelt = Mock()
        requests_toolbelt.multipart.decoder.BodyPart.return_value = version_parts

        expected_result = [
            {"uri": "/ewhc/ch/2022/1178_xml_versions/3-1178", "version": 3},
            {"uri": "/ewhc/ch/2022/1178_xml_versions/2-1178", "version": 2},
            {"uri": "/ewhc/ch/2022/1178_xml_versions/1-1178", "version": 1},
        ]

        assert render_versions(version_parts) == expected_result


class TestAWSUtils:
    def test_build_new_key_docx(self):
        old_key = "failures/TDR-2022-DNWR/failures_TDR-2022-DNWR.docx"
        new_uri = "ukpc/2023/120"
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/ukpc_2023_120.docx"

    def test_build_new_key_pdf(self):
        old_key = "failures/TDR-2022-DNWR/failures_TDR-2022-DNWR.pdf"
        new_uri = "ukpc/2023/120"
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/ukpc_2023_120.pdf"

    def test_build_new_key_image(self):
        old_key = "failures/TDR-2022-DNWR/image1.jpg"
        new_uri = "ukpc/2023/120"
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/image1.jpg"

    @patch("caselawclient.models.utilities.aws.create_s3_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    def test_copy_assets(self, client):
        """
        Copy *unpublished* assets from one path to another,
        renaming DOCX and PDF files as appropriate.
        """

        client.return_value.list_objects.return_value = {
            "Contents": [{"Key": "uksc/2023/1/uksc_2023_1.docx"}]
        }
        copy_assets("uksc/2023/1", "ukpc/1999/9")
        client.return_value.copy.assert_called_with(
            {"Bucket": "MY_BUCKET", "Key": "uksc/2023/1/uksc_2023_1.docx"},
            "MY_BUCKET",
            "ukpc/1999/9/ukpc_1999_9.docx",
        )
