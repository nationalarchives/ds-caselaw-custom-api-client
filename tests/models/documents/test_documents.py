import datetime
import os
import warnings
from unittest.mock import Mock, patch

import pytest
from lxml import etree

from caselawclient.errors import (
    DocumentNotFoundError,
    NotSupportedOnVersion,
    OnlySupportedOnVersion,
)
from caselawclient.factories import (
    DocumentBodyFactory,
    DocumentFactory,
    IdentifierResolutionFactory,
    IdentifierResolutionsFactory,
    JudgmentFactory,
)
from caselawclient.models.documents import (
    DOCUMENT_STATUS_HOLD,
    DOCUMENT_STATUS_IN_PROGRESS,
    DOCUMENT_STATUS_NEW,
    DOCUMENT_STATUS_PUBLISHED,
    Document,
    DocumentURIString,
)
from caselawclient.models.judgments import Judgment
from caselawclient.types import InvalidDocumentURIException
from caselawclient.xml_helpers import DEFAULT_NAMESPACES


class TestDocument:
    def test_is_publishable_false_with_multiple_failures(self, mock_api_client):
        # Simulate a document with non-unique content hash and missing name
        mock_api_client.has_unique_content_hash.return_value = False
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        # Force the body.name to be empty (missing name)
        document.body.name = ""
        # Patch has_name to False
        document.has_name = False
        # is_publishable should be False
        assert document.is_publishable is False
        # The failure messages should mention both unique content hash and missing name
        messages = document.validation_failure_messages
        assert any("There is another document with identical content" in msg for msg in messages)
        assert any("no name" in msg for msg in messages)

    def test_has_unique_content_hash_true(self, mock_api_client):
        mock_api_client.has_unique_content_hash.return_value = True
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        assert document.has_unique_content_hash is True
        mock_api_client.has_unique_content_hash.assert_called_once_with("test/1234")

    def test_has_unique_content_hash_false(self, mock_api_client):
        mock_api_client.has_unique_content_hash.return_value = False
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        assert document.has_unique_content_hash is False

    def test_validation_failure_message_for_nonunique_content_hash(self, mock_api_client):
        mock_api_client.has_unique_content_hash.return_value = False
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        messages = document.validation_failure_messages
        assert any("There is another document with identical content" in msg for msg in messages)

    def test_has_sensible_repr_with_name_and_judgment(self, mock_api_client):
        document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        document.body.name = "Document Name"
        assert str(document) == "<judgment test/1234: Document Name>"

    def test_has_sensible_repr_without_name_or_subclass(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        assert str(document) == "<document test/1234: un-named>"

    def test_public_uri(self):
        document = DocumentFactory.build()
        assert document.public_uri == "https://caselaw.nationalarchives.gov.uk/tna.tn4t35ts"

    def test_document_exists_check(self, mock_api_client):
        mock_api_client.document_exists.return_value = False
        with pytest.raises(DocumentNotFoundError):
            Document(DocumentURIString("not_a_real_judgment"), mock_api_client)

    def test_judgment_is_published(self, mock_api_client):
        mock_api_client.get_published.return_value = True

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.is_published is True
        mock_api_client.get_published.assert_called_once_with("test/1234")

    def test_judgment_is_held(self, mock_api_client):
        mock_api_client.get_property.return_value = False

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.is_held is False
        mock_api_client.get_property.assert_called_once_with("test/1234", "editor-hold")

    def test_judgment_is_locked(self, mock_api_client):
        mock_api_client.get_judgment_checkout_status_message.return_value = "Judgment locked"
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.is_locked is True

    def test_judgment_is_not_locked(self, mock_api_client):
        mock_api_client.get_judgment_checkout_status_message.return_value = None
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.is_locked is False

    def test_judgment_source_name(self, mock_api_client):
        mock_api_client.get_property.return_value = "Test Name"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.source_name == "Test Name"
        mock_api_client.get_property.assert_called_once_with("test/1234", "source-name")

    def test_judgment_source_email(self, mock_api_client):
        mock_api_client.get_property.return_value = "testemail@example.com"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.source_email == "testemail@example.com"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234",
            "source-email",
        )

    def test_judgment_consignment_reference(self, mock_api_client):
        mock_api_client.get_property.return_value = "TDR-2023-ABC"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.consignment_reference == "TDR-2023-ABC"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234",
            "transfer-consignment-reference",
        )

    @patch("caselawclient.models.documents.generate_docx_url")
    def test_judgment_docx_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.docx"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.docx_url == "https://example.com/mock.docx"
        mock_url_generator.assert_called_once

    @patch("caselawclient.models.documents.generate_pdf_url")
    def test_judgment_pdf_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.pdf"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.pdf_url == "https://example.com/mock.pdf"
        mock_url_generator.assert_called_once

    def test_judgment_assigned_to(self, mock_api_client):
        mock_api_client.get_property.return_value = "testuser"

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.assigned_to == "testuser"
        mock_api_client.get_property.assert_called_once_with("test/1234", "assigned-to")

    def test_document_status(self, mock_api_client):
        new_document = Document(DocumentURIString("test/1234"), mock_api_client)
        new_document.is_held = False
        new_document.is_published = False
        new_document.assigned_to = ""
        assert new_document.status == DOCUMENT_STATUS_NEW

        in_progress_document = Document(DocumentURIString("test/1234"), mock_api_client)
        in_progress_document.is_held = False
        in_progress_document.is_published = False
        in_progress_document.assigned_to = "duck"
        assert in_progress_document.status == DOCUMENT_STATUS_IN_PROGRESS

        on_hold_document = Document(DocumentURIString("test/1234"), mock_api_client)
        on_hold_document.is_held = True
        on_hold_document.is_published = False
        on_hold_document.assigned_to = "duck"
        assert on_hold_document.status == DOCUMENT_STATUS_HOLD

        published_document = Document(DocumentURIString("test/1234"), mock_api_client)
        published_document.is_held = False
        published_document.is_published = True
        published_document.assigned_to = "duck"
        assert published_document.status == DOCUMENT_STATUS_PUBLISHED

    def test_document_first_published_datetime(self, mock_api_client):
        mock_api_client.get_datetime_property.return_value = datetime.datetime(
            2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc
        )

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.first_published_datetime == datetime.datetime(
            2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc
        )
        mock_api_client.get_datetime_property.assert_called_once_with("test/1234", "first_published_datetime")

    def test_document_first_published_datetime_display(self, mock_api_client):
        mock_api_client.get_datetime_property.return_value = datetime.datetime(
            2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc
        )

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.first_published_datetime_display == datetime.datetime(
            2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc
        )
        mock_api_client.get_datetime_property.assert_called_once_with("test/1234", "first_published_datetime")

    def test_document_first_published_datetime_display_sentinel(self, mock_api_client):
        """We expect that our sentinel value will return `None`."""
        mock_api_client.get_datetime_property.return_value = datetime.datetime(
            1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
        )

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.first_published_datetime_display is None
        mock_api_client.get_datetime_property.assert_called_once_with("test/1234", "first_published_datetime")

    @pytest.mark.parametrize(
        "is_published, first_published_datetime, expected_outcome",
        [
            (False, None, False),
            (True, None, True),
            (False, datetime.datetime(2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc), True),
            (True, datetime.datetime(2025, 8, 19, 12, 5, 53, 398214, tzinfo=datetime.timezone.utc), True),
            (False, datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), True),
            (True, datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc), True),
        ],
    )
    def test_document_has_ever_been_published(
        self, mock_api_client, is_published, first_published_datetime, expected_outcome
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.is_published = is_published
        document.first_published_datetime = first_published_datetime

        assert document.has_ever_been_published is expected_outcome

    def test_document_best_identifier(self, mock_api_client):
        example_document = Document(DocumentURIString("uri"), mock_api_client)
        assert example_document.best_human_identifier is None

    def test_document_version_of_a_version_fails(self, mock_api_client):
        version_document = Document(DocumentURIString("test/1234_xml_versions/9-1234"), mock_api_client)
        with pytest.raises(NotSupportedOnVersion):
            version_document.versions_as_documents

    def test_document_versions_happy_case(self, mock_api_client):
        version_document = Document(DocumentURIString("test/1234"), mock_api_client)
        version_document.versions = [
            {"uri": DocumentURIString("test/1234_xml_versions/2-1234"), "version": 2},
            {"uri": DocumentURIString("test/1234_xml_versions/1-1234"), "version": 1},
        ]
        version_document.versions_as_documents[0].uri = DocumentURIString("test/1234_xml_versions/2-1234")

    def test_document_version_number_when_not_version(self, mock_api_client):
        base_document = Document(DocumentURIString("test/1234"), mock_api_client)
        with pytest.raises(OnlySupportedOnVersion):
            base_document.version_number
        assert not base_document.is_version

    def test_document_version_number_when_is_version(self, mock_api_client):
        version_document = Document(DocumentURIString("test/1234_xml_versions/9-1234"), mock_api_client)
        assert version_document.version_number == 9
        assert version_document.is_version

    def test_validates_against_schema(self, mock_api_client):
        mock_api_client.validate_document.return_value = True

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.validates_against_schema is True

        mock_api_client.validate_document.assert_called_with(document.uri)

    def test_document_initialises_with_search_query_string(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client, search_query="test search query")

        mock_api_client.get_judgment_xml_bytestring.assert_called_with(
            document.uri, show_unpublished=True, search_query="test search query"
        )


class TestDocumentEnrichedRecently:
    def test_enriched_recently_returns_false_when_never_enriched(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        mock_api_client.get_property.return_value = ""

        assert document.enriched_recently is False

    def test_enriched_recently_returns_true_within_cooldown(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.body.enrichment_datetime = datetime.datetime.now(
            tz=datetime.timezone.utc,
        ) - datetime.timedelta(seconds=30)

        assert document.enriched_recently is True

    def test_enriched_recently_returns_false_outside_cooldown(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        document.body.enrichment_datetime = datetime.datetime.now(
            tz=datetime.timezone.utc,
        ) - datetime.timedelta(days=2)

        assert document.enriched_recently is False

    class TestMethodMissing:
        def test_attribute_on_body(self, mock_api_client):
            doc = DocumentFactory.build(
                uri=DocumentURIString("test/1234"), body=DocumentBodyFactory.build(name="docname")
            )
            with pytest.deprecated_call():
                name = doc.name

            assert name == "docname"

        def test_real_attribute(self, mock_api_client):
            doc = DocumentFactory.build(
                uri=DocumentURIString("test/1234"), body=DocumentBodyFactory.build(name="docname")
            )
            with warnings.catch_warnings():
                identifier = doc.best_human_identifier
            assert identifier is None

        def test_absent_item(self, mock_api_client):
            doc = DocumentFactory.build(
                uri=DocumentURIString("test/1234"), body=DocumentBodyFactory.build(name="docname")
            )
            with pytest.raises(
                AttributeError, match="Neither 'Document' nor 'DocumentBody' objects have an attribute 'x'"
            ):
                doc.x


class TestDocumentURIString:
    def test_accepts_two_element_uri(self):
        DocumentURIString("test/1234")

    def test_accepts_three_element_uri(self):
        DocumentURIString("test/b/1234")

    def test_rejects_uri_with_leading_slash(self):
        with pytest.raises(InvalidDocumentURIException):
            DocumentURIString("/test/1234")

    def test_rejects_uri_with_trailing_slash(self):
        with pytest.raises(InvalidDocumentURIException):
            DocumentURIString("test/1234/")

    def test_rejects_uri_with_leading_and_trailing_slash(self):
        with pytest.raises(InvalidDocumentURIException):
            DocumentURIString("/test/1234/")

    def test_rejects_uri_with_dot(self):
        with pytest.raises(InvalidDocumentURIException):
            DocumentURIString("test/1234.xml")


class TestLinkedDocumentResolutions:
    def test_base(self, mock_api_client):
        resolutions = IdentifierResolutionsFactory.build(
            [
                IdentifierResolutionFactory.build(namespace="ukncn", resolution_uuid="okay-pub"),
                IdentifierResolutionFactory.build(namespace="ukncn", resolution_uuid="okay-multi"),
                IdentifierResolutionFactory.build(published=False, namespace="ukncn", resolution_uuid="maybe-unpub"),
                IdentifierResolutionFactory.build(namespace="fclid", resolution_uuid="not-diff-namespace"),
                IdentifierResolutionFactory.build(
                    namespace="ukncn", document_uri="/thisone.xml", resolution_uuid="not-this"
                ),
            ]
        )
        mock_api_client.resolve_from_identifier_value.return_value = resolutions
        doc = JudgmentFactory.build(neutral_citation="[2003] UKSC 1", uri=DocumentURIString("thisone"))
        doc.api_client = mock_api_client
        resolutions = doc.linked_document_resolutions(["ukncn"], only_published=True)
        match_uuids = [x.identifier_uuid for x in resolutions]
        assert match_uuids == ["okay-pub", "okay-multi"]

        resolutions_unpub = doc.linked_document_resolutions(["ukncn"], only_published=False)
        unpub_uuids = [x.identifier_uuid for x in resolutions_unpub]
        assert unpub_uuids == ["okay-pub", "okay-multi", "maybe-unpub"]

    @patch.dict(os.environ, {"XSLT_IMAGE_LOCATION": "imagepath"}, clear=True)
    class TestDocumentContentAsHtml:
        def test_document_content_as_html_calls_with_uri(self):
            doc = DocumentFactory.build(
                uri=DocumentURIString("test/1234"), body=DocumentBodyFactory.build(name="docname")
            )
            doc.body.content_html = Mock()
            doc.content_as_html()
            doc.body.content_html.assert_called_with("imagepath/test/1234")


class TestDocumentXMLWithCorrectFRBR:
    def test_add_live_data(self):
        with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "xslt", "test_standard_judgment.xml"), "r"
        ) as file:
            xml_string = file.read()
            doc = DocumentFactory.build(
                uri=DocumentURIString("d-1234"), body=DocumentBodyFactory.build(name="docname", xml_string=xml_string)
            )

        assert "akn:" not in xml_string
        root = etree.fromstring(doc.xml_with_correct_frbr())
        assert b"akn:" not in etree.tostring(root, method="c14n")

        assert root.xpath("//akn:FRBRWork/akn:FRBRthis/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/id/doc/tn4t35ts"
        ]
        assert root.xpath("//akn:FRBRWork/akn:FRBRuri/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/id/doc/tn4t35ts"
        ]
        assert root.xpath("//akn:FRBRExpression/akn:FRBRthis/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/d-1234"
        ]
        assert root.xpath("//akn:FRBRExpression/akn:FRBRuri/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/d-1234"
        ]
        assert root.xpath("//akn:FRBRManifestation/akn:FRBRthis/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/d-1234/data.xml"
        ]
        assert root.xpath("//akn:FRBRManifestation/akn:FRBRuri/@value", namespaces=DEFAULT_NAMESPACES) == [
            "https://caselaw.nationalarchives.gov.uk/d-1234/data.xml"
        ]

        assert b"<FRBRthis" in etree.tostring(root, method="c14n")
