import io
import os
from unittest.mock import MagicMock, Mock, patch
from urllib import parse

import boto3
import ds_caselaw_utils
import pytest
from moto import mock_aws

from caselawclient.models.documents import DocumentURIString
from caselawclient.models.neutral_citation_mixin import NeutralCitationString
from caselawclient.models.utilities import aws as aws_utils
from caselawclient.models.utilities import extract_version, move, render_versions
from caselawclient.models.utilities.aws import (
    are_unpublished_assets_clean,
    build_new_key,
    check_docx_exists,
    copy_assets,
    delete_non_targz_from_bucket,
    generate_docx_url,
    generate_pdf_url,
    generate_signed_asset_url,
    upload_asset_to_private_bucket,
)


@pytest.fixture
def fake_bucket():
    with patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "bucket"}), mock_aws():
        s3 = boto3.resource("s3", region_name="us-east-1")
        yield s3.create_bucket(Bucket="bucket")


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

    @patch("caselawclient.models.utilities.aws.create_s3_client")
    def test_delete_non_tar_gz(self, client):
        client.return_value.list_objects.return_value = {
            "Contents": [{"Key": "uksc/2023/1/uksc_2023_1.docx"}, {"Key": "uksc/2023/1/TDR-2023-AAA.tar.gz"}]
        }
        delete_non_targz_from_bucket(DocumentURIString("uksc/2023/1"), "fake_bucket")
        client.return_value.list_objects.assert_called_with(Bucket="fake_bucket", Prefix="uksc/2023/1/")
        client.return_value.delete_objects.assert_called_with(
            Bucket="fake_bucket", Delete={"Objects": [{"Key": "uksc/2023/1/uksc_2023_1.docx"}]}
        )

    @mock_aws
    def test_upload(self, fake_bucket):
        upload_asset_to_private_bucket(b"%PDF", "s3/key.pdf")
        s3_object = fake_bucket.Object("s3/key.pdf").get()
        assert s3_object["Body"].read() == b"%PDF"


@patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
@mock_aws
class TestSignedLinks:
    def test_signed_link_direct(self):
        signed_link = generate_signed_asset_url("key.png")
        assert signed_link.startswith("https://s3.amazonaws.com/MY_BUCKET/key.png?")
        assert "response-content-disposition" not in signed_link

    def test_signed_link_docx_default(self):
        signed_link = generate_docx_url(DocumentURIString("d-a1"))
        assert signed_link.startswith(
            "https://s3.amazonaws.com/MY_BUCKET/d-a1/d-a1.docx?response-content-disposition=attachment%3Bfilename%3Dd-a1.docx&"
        )

    def test_signed_link_pdf_default(self):
        signed_link = generate_pdf_url(DocumentURIString("d-a1"))
        assert signed_link.startswith("https://s3.amazonaws.com/MY_BUCKET/d-a1/d-a1.pdf?")
        assert "response-content-disposition" not in signed_link

    def test_signed_link_pdf_force_download(self):
        signed_link = generate_pdf_url(DocumentURIString("d-a1"), force_download=True)
        assert signed_link.startswith(
            "https://s3.amazonaws.com/MY_BUCKET/d-a1/d-a1.pdf?response-content-disposition=attachment%3Bfilename%3Dd-a1.pdf&"
        )

    def test_signed_link_direct_custom_filename(self):
        signed_link = generate_signed_asset_url(
            "key.png", force_download=True, content_disposition_filename="filename.png"
        )
        assert signed_link.startswith(
            "https://s3.amazonaws.com/MY_BUCKET/key.png?response-content-disposition=attachment%3Bfilename%3Dfilename.png&"
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


class TestCheckCleaningTags:
    @pytest.fixture
    def bucket(self):
        with patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "bucket"}), mock_aws():
            s3 = boto3.resource("s3", region_name="us-east-1")
            yield s3.create_bucket(Bucket="bucket")

    @pytest.fixture
    def url(self):
        return DocumentURIString("ewhc/2023/1")

    def test_accepts_properly_tagged_files(self, bucket, url):
        """Files with correct tags should pass validation."""
        tags = parse.urlencode({"DOCUMENT_PROCESSOR_VERSION": "1.0.0"})
        bucket.upload_fileobj(
            Key="ewhc/2023/1/ewhc_2023_1.png", Fileobj=io.BytesIO(b"test file"), ExtraArgs={"Tagging": tags}
        )

        assert are_unpublished_assets_clean(url)

    def test_ignores_tar_gz_files(self, bucket, url):
        """Tar.gz archives should not require tags."""
        bucket.upload_fileobj(Key="ewhc/2023/1/TDR-2025-AAA.tar.gz", Fileobj=io.BytesIO(b"archive"))

        assert are_unpublished_assets_clean(url)

    def test_ignores_files_outside_document_path(self, bucket, url):
        """Files in unrelated S3 locations should be ignored."""
        bucket.upload_fileobj(Key="unrelated/file.docx", Fileobj=io.BytesIO(b"unrelated"))

        assert are_unpublished_assets_clean(url)

    def test_rejects_untagged_image_files(self, bucket, url):
        """Untagged image files should fail validation."""
        bucket.upload_fileobj(Key="ewhc/2023/1/ewhc_2023_1.jpg", Fileobj=io.BytesIO(b"image without tags"))

        assert not are_unpublished_assets_clean(url)

    def test_rejects_when_mix_of_tagged_and_untagged_files(self, bucket, url):
        """Should fail if ANY file is untagged, even if others are tagged."""
        # Tagged file - OK
        tags = parse.urlencode({"DOCUMENT_PROCESSOR_VERSION": "1.0.0"})
        irrelevant_tags = parse.urlencode({"IRRELEVANT_TAG": "YES"})
        bucket.upload_fileobj(
            Key="ewhc/2023/1/ewhc_2023_1.png", Fileobj=io.BytesIO(b"tagged"), ExtraArgs={"Tagging": tags}
        )

        # Untagged file - NOT OK
        bucket.upload_fileobj(
            Key="ewhc/2023/1/ewhc_2023_1.jpg", Fileobj=io.BytesIO(b"untagged"), ExtraArgs={"Tagging": irrelevant_tags}
        )

        assert not are_unpublished_assets_clean(url)


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
