import datetime
import warnings
from unittest.mock import PropertyMock, patch

import pytest

from caselawclient.errors import (
    DocumentNotFoundError,
    NotSupportedOnVersion,
    OnlySupportedOnVersion,
)
from caselawclient.factories import DocumentBodyFactory, DocumentFactory
from caselawclient.models.documents import (
    DOCUMENT_STATUS_HOLD,
    DOCUMENT_STATUS_IN_PROGRESS,
    DOCUMENT_STATUS_NEW,
    DOCUMENT_STATUS_PUBLISHED,
    Document,
    DocumentURIString,
)
from caselawclient.models.documents.exceptions import InvalidDocumentURIException
from caselawclient.models.judgments import Judgment
from tests.test_helpers import MockMultipartResponse


class TestDocument:
    def test_has_sensible_repr_with_name_and_judgment(self, mock_api_client):
        document = Judgment(DocumentURIString("test/1234"), mock_api_client)
        document.body.name = "Document Name"
        assert str(document) == "<judgment test/1234: Document Name>"

    def test_has_sensible_repr_without_name_or_subclass(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        assert str(document) == "<document test/1234: un-named>"

    def test_public_uri(self, mock_api_client):
        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.public_uri == "https://caselaw.nationalarchives.gov.uk/test/1234"

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
            {"uri": "test/1234_xml_versions/2-1234", "version": 2},
            {"uri": "test/1234_xml_versions/1-1234", "version": 1},
        ]
        version_document.versions_as_documents[0].uri = "test/1234_xml_versions/2-1234.xml"

    def test_document_version_number_when_not_version(self, mock_api_client):
        base_document = Document(DocumentURIString("test/1234"), mock_api_client)
        with pytest.raises(OnlySupportedOnVersion):
            base_document.version_number
        assert not base_document.is_version

    def test_document_version_number_when_is_version(self, mock_api_client):
        version_document = Document(DocumentURIString("test/1234_xml_versions/9-1234"), mock_api_client)
        assert version_document.version_number == 9
        assert version_document.is_version

    def test_number_of_mentions_when_no_mentions(self, mock_api_client):
        mock_api_client.eval_xslt.return_value = MockMultipartResponse(
            b"""
            <article>
                <p>An article with no mark elements.</p>
            </article>
        """,
        )

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.number_of_mentions("some") == 0

    def test_number_of_mentions_when_mentions(self, mock_api_client):
        mock_api_client.eval_xslt.return_value = MockMultipartResponse(
            b"""
            <article>
                <p>
                    An article with <mark id="mark_0">some</mark> mark elements, and <mark id="mark_1">some</mark> more.
                </p>
            </article>
        """,
        )

        document = Document(DocumentURIString("test/1234"), mock_api_client)

        assert document.number_of_mentions("some") == 2

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


class TestCanEnrich:
    @pytest.mark.parametrize(
        "enriched_recently, validates_against_schema, can_enrich",
        [
            (
                True,
                True,
                False,
            ),  # Enriched recently and validates against schema - Can't enrich
            (
                True,
                False,
                False,
            ),  # Enriched recently and does not validate against schema - Can't enrich
            (
                False,
                False,
                False,
            ),  # Not enriched recently and does not validate against schema - Can't enrich
            (
                False,
                True,
                True,
            ),  # Not Enriched recently and validates against schema - Can enrich
        ],
    )
    def test_returns_true_when_enriched_recently_is_true_and_validates_against_schema_is_true(
        self,
        mock_api_client,
        enriched_recently,
        validates_against_schema,
        can_enrich,
    ):
        document = Document(DocumentURIString("test/1234"), mock_api_client)
        with (
            patch.object(
                Document,
                "enriched_recently",
                new_callable=PropertyMock,
            ) as mock_enriched_recently,
            patch.object(
                Document,
                "validates_against_schema",
                new_callable=PropertyMock,
            ) as mock_validates_against_schema,
        ):
            mock_enriched_recently.return_value = enriched_recently
            mock_validates_against_schema.return_value = validates_against_schema

            assert document.can_enrich is can_enrich

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
