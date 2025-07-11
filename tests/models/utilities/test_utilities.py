import io
import os
from unittest.mock import MagicMock, Mock, patch

import boto3
import ds_caselaw_utils
import pytest
from moto import mock_aws

from caselawclient.models.documents import DocumentURIString
from caselawclient.models.neutral_citation_mixin import NeutralCitationString
from caselawclient.models.utilities import aws as aws_utils
from caselawclient.models.utilities import extract_version, move, render_versions
from caselawclient.models.utilities.aws import (
    build_new_key,
    check_docx_exists,
    copy_assets,
)


class TestVersionUtils:
    def test_extract_version_ncn_based_uri(self):
        uri = "/ewhc/ch/2022/1178_xml_versions/2-1178.xml"
        assert extract_version(uri) == 2

    def test_extract_version_uuid_based_uri(self):
        uri = "/d-24e29b2e-9264-43f9-b0de-31c4605cb500_xml_versions/2-d-24e29b2e-9264-43f9-b0de-31c4605cb500.xml"
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
            {"uri": "ewhc/ch/2022/1178_xml_versions/3-1178", "version": 3},
            {"uri": "ewhc/ch/2022/1178_xml_versions/2-1178", "version": 2},
            {"uri": "ewhc/ch/2022/1178_xml_versions/1-1178", "version": 1},
        ]

        assert render_versions(version_parts) == expected_result


class TestAWSUtils:
    def test_build_new_key_docx(self):
        old_key = "failures/TDR-2022-DNWR/failures_TDR-2022-DNWR.docx"
        new_uri = DocumentURIString("ukpc/2023/120")
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/ukpc_2023_120.docx"

    def test_build_new_key_pdf(self):
        old_key = "failures/TDR-2022-DNWR/failures_TDR-2022-DNWR.pdf"
        new_uri = DocumentURIString("ukpc/2023/120")
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/ukpc_2023_120.pdf"

    def test_build_new_key_image(self):
        old_key = "failures/TDR-2022-DNWR/image1.jpg"
        new_uri = DocumentURIString("ukpc/2023/120")
        assert build_new_key(old_key, new_uri) == "ukpc/2023/120/image1.jpg"

    @patch("caselawclient.models.utilities.aws.create_s3_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    def test_copy_assets(self, client):
        """
        Copy *unpublished* assets from one path to another,
        renaming DOCX and PDF files as appropriate.
        """

        client.return_value.list_objects.return_value = {
            "Contents": [{"Key": "uksc/2023/1/uksc_2023_1.docx"}],
        }
        copy_assets(DocumentURIString("uksc/2023/1"), DocumentURIString("ukpc/1999/9"))
        client.return_value.copy.assert_called_with(
            {"Bucket": "MY_BUCKET", "Key": "uksc/2023/1/uksc_2023_1.docx"},
            "MY_BUCKET",
            "ukpc/1999/9/ukpc_1999_9.docx",
        )


class TestMove:
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch("boto3.session.Session.client")
    @patch("caselawclient.models.utilities.move.set_metadata")
    @patch("caselawclient.models.utilities.move.copy_assets")
    def test_move_judgment_success(
        self,
        fake_copy,
        fake_metadata,
        fake_boto3_client,
    ):
        """Given the target judgment does not exist,
        we continue to move the judgment to the new location
        (where moving is copy + delete)"""
        # fake_judgment.return_value = JudgmentFactory.build()
        ds_caselaw_utils.neutral_url = MagicMock(return_value="new/uri")
        fake_api_client = MagicMock()
        fake_api_client.document_exists.return_value = False
        move.update_document_uri(DocumentURIString("old/uri"), NeutralCitationString("[2023] EAT 1"), fake_api_client)

        fake_api_client.copy_document.assert_called_with("old/uri", "new/uri")
        fake_metadata.assert_called_with("old/uri", "new/uri", fake_api_client)
        fake_copy.assert_called_with("old/uri", "new/uri")
        fake_api_client.set_judgment_this_uri.assert_called_with("new/uri")
        fake_api_client.delete_judgment.assert_called_with("old/uri")


class TestCheckDocx:
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "bucket"})
    @mock_aws
    def test_check_docx(aws):
        """Make a fake docx, then check if it exists, and for one that doesn't"""
        url = DocumentURIString("ewhc/2023/1")
        docx = "ewhc/2023/1/ewhc_2023_1.docx"
        s3 = boto3.resource("s3", region_name="us-east-1")
        bucket = s3.create_bucket(Bucket="bucket")
        fobj = io.BytesIO(b"placeholder docx")
        bucket.upload_fileobj(Key=docx, Fileobj=fobj)
        assert check_docx_exists(url)
        assert not (check_docx_exists(DocumentURIString("not/the/url")))


class TestS3Prefix:
    def test_appends_slash(self):
        assert str(aws_utils.uri_for_s3(DocumentURIString("a/sample/url"))) == "a/sample/url/"


class TestS3TrailingSlash:
    @patch("caselawclient.models.utilities.aws.create_s3_client")
    def test_delete(self, fake_s3):
        aws_utils.delete_from_bucket(DocumentURIString("a/sample/uri"), "bucket")
        fake_s3.return_value.list_objects.assert_called_with(Bucket="bucket", Prefix="a/sample/uri/")

    @patch("caselawclient.models.utilities.aws.create_s3_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    def test_copy(self, fake_s3):
        aws_utils.copy_assets(DocumentURIString("from"), DocumentURIString("to"))
        fake_s3.return_value.list_objects.assert_called_with(Bucket="MY_BUCKET", Prefix="from/")

    @patch("caselawclient.models.utilities.aws.create_s3_client")
    @patch.dict(os.environ, {"PUBLIC_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "PRIVATE_BUCKET"})
    def test_publish(self, fake_s3):
        aws_utils.publish_documents(DocumentURIString("a/sample/uri"))
        fake_s3.return_value.list_objects.assert_called_with(Bucket="PRIVATE_BUCKET", Prefix="a/sample/uri/")

    def test_s3_prefix_string_no_slash_error(self):
        with pytest.raises(RuntimeError):
            aws_utils.S3PrefixString("cat")

    def test_s3_prefix_string_slash_ok(self):
        aws_utils.S3PrefixString("cat/")
