import datetime
from unittest.mock import Mock, patch

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import DocumentNotFoundError
from caselawclient.models.documents import (
    DOCUMENT_STATUS_HOLD,
    DOCUMENT_STATUS_IN_PROGRESS,
    DOCUMENT_STATUS_PUBLISHED,
    CannotPublishUnpublishableDocument,
    Document,
)


@pytest.fixture
def mock_api_client():
    return Mock(spec=MarklogicApiClient)


class TestDocument:
    def test_uri_strips_slashes(self, mock_api_client):
        document = Document("////test/1234/////", mock_api_client)

        assert document.uri == "test/1234"

    def test_public_uri(self, mock_api_client):
        document = Document("test/1234", mock_api_client)

        assert (
            document.public_uri == "https://caselaw.nationalarchives.gov.uk/test/1234"
        )

    def test_document_exists_check(self, mock_api_client):
        mock_api_client.document_exists.return_value = False
        with pytest.raises(DocumentNotFoundError):
            Document("not_a_real_judgment", mock_api_client)

    def test_judgment_name(self, mock_api_client):
        mock_api_client.get_judgment_name.return_value = (
            "Test Judgment v Test Judgement"
        )

        document = Document("test/1234", mock_api_client)

        assert document.name == "Test Judgment v Test Judgement"
        mock_api_client.get_judgment_name.assert_called_once_with("test/1234")

    def test_judgment_court(self, mock_api_client):
        mock_api_client.get_judgment_court.return_value = "Court of Testing"

        document = Document("test/1234", mock_api_client)

        assert document.court == "Court of Testing"
        mock_api_client.get_judgment_court.assert_called_once_with("test/1234")

    def test_judgment_date_as_string(self, mock_api_client):
        mock_api_client.get_judgment_work_date.return_value = "2023-02-03"

        document = Document("test/1234", mock_api_client)

        assert document.judgment_date_as_string == "2023-02-03"
        assert document.judgment_date_as_date == datetime.date(2023, 2, 3)
        mock_api_client.get_judgment_work_date.assert_called_once_with("test/1234")

    def test_judgment_is_published(self, mock_api_client):
        mock_api_client.get_published.return_value = True

        document = Document("test/1234", mock_api_client)

        assert document.is_published is True
        mock_api_client.get_published.assert_called_once_with("test/1234")

    def test_judgment_is_held(self, mock_api_client):
        mock_api_client.get_property.return_value = False

        document = Document("test/1234", mock_api_client)

        assert document.is_held is False
        mock_api_client.get_property.assert_called_once_with("test/1234", "editor-hold")

    def test_judgment_is_sensitive(self, mock_api_client):
        mock_api_client.get_sensitive.return_value = True

        document = Document("test/1234", mock_api_client)

        assert document.is_sensitive is True
        mock_api_client.get_sensitive.assert_called_once_with("test/1234")

    def test_judgment_is_anonymised(self, mock_api_client):
        mock_api_client.get_anonymised.return_value = True

        document = Document("test/1234", mock_api_client)

        assert document.is_anonymised is True
        mock_api_client.get_anonymised.assert_called_once_with("test/1234")

    def test_judgment_has_supplementary_materials(self, mock_api_client):
        mock_api_client.get_supplemental.return_value = True

        document = Document("test/1234", mock_api_client)

        assert document.has_supplementary_materials is True
        mock_api_client.get_supplemental.assert_called_once_with("test/1234")

    def test_judgment_source_name(self, mock_api_client):
        mock_api_client.get_property.return_value = "Test Name"

        document = Document("test/1234", mock_api_client)

        assert document.source_name == "Test Name"
        mock_api_client.get_property.assert_called_once_with("test/1234", "source-name")

    def test_judgment_source_email(self, mock_api_client):
        mock_api_client.get_property.return_value = "testemail@example.com"

        document = Document("test/1234", mock_api_client)

        assert document.source_email == "testemail@example.com"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234", "source-email"
        )

    def test_judgment_consignment_reference(self, mock_api_client):
        mock_api_client.get_property.return_value = "TDR-2023-ABC"

        document = Document("test/1234", mock_api_client)

        assert document.consignment_reference == "TDR-2023-ABC"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234", "transfer-consignment-reference"
        )

    @patch("caselawclient.models.documents.generate_docx_url")
    def test_judgment_docx_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.docx"

        document = Document("test/1234", mock_api_client)

        assert document.docx_url == "https://example.com/mock.docx"
        mock_url_generator.assert_called_once

    @patch("caselawclient.models.documents.generate_pdf_url")
    def test_judgment_pdf_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.pdf"

        document = Document("test/1234", mock_api_client)

        assert document.pdf_url == "https://example.com/mock.pdf"
        mock_url_generator.assert_called_once

    def test_judgment_assigned_to(self, mock_api_client):
        mock_api_client.get_property.return_value = "testuser"

        document = Document("test/1234", mock_api_client)

        assert document.assigned_to == "testuser"
        mock_api_client.get_property.assert_called_once_with("test/1234", "assigned-to")

    def test_judgment_content_as_xml(self, mock_api_client):
        mock_api_client.get_judgment_xml.return_value = "<xml></xml>"

        document = Document("test/1234", mock_api_client)

        assert document.content_as_xml() == "<xml></xml>"
        mock_api_client.get_judgment_xml.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    def test_DOCUMENT_STATUS(self, mock_api_client):
        in_progress_document = Document("test/1234", mock_api_client)
        in_progress_document.is_held = False
        in_progress_document.is_published = False
        assert in_progress_document.status == DOCUMENT_STATUS_IN_PROGRESS

        on_hold_document = Document("test/1234", mock_api_client)
        on_hold_document.is_held = True
        on_hold_document.is_published = False
        assert on_hold_document.status == DOCUMENT_STATUS_HOLD

        published_document = Document("test/1234", mock_api_client)
        published_document.is_held = False
        published_document.is_published = True
        assert published_document.status == DOCUMENT_STATUS_PUBLISHED


class TestDocumentValidation:
    def test_judgment_is_failure(self, mock_api_client):
        successful_document = Document("test/1234", mock_api_client)
        failing_document = Document("failures/test/1234", mock_api_client)

        assert successful_document.is_failure is False
        assert failing_document.is_failure is True

    def test_judgment_is_parked(self, mock_api_client):
        normal_document = Document("test/1234", mock_api_client)
        parked_document = Document("parked/a1b2c3d4", mock_api_client)

        assert normal_document.is_parked is False
        assert parked_document.is_parked is True

    def test_has_name(self, mock_api_client):
        document_with_name = Document("test/1234", mock_api_client)
        document_with_name.name = "Judgment v Judgement"

        document_without_name = Document("test/1234", mock_api_client)
        document_without_name.name = ""

        assert document_with_name.has_name is True
        assert document_without_name.has_name is False

    def test_has_court_is_covered_by_has_valid_court(self, mock_api_client):
        document_with_court = Document("test/1234", mock_api_client)
        document_with_court.court = "UKSC"

        document_without_court = Document("test/1234", mock_api_client)
        document_without_court.court = ""

        assert document_with_court.has_valid_court is True
        assert document_without_court.has_valid_court is False

    @pytest.mark.parametrize(
        "is_parked, is_held, has_name, has_valid_court, publishable",
        [
            (False, False, True, True, True),  # Publishable
            (False, True, True, True, False),  # Held
            (True, False, True, True, False),  # Parked
            (False, False, False, True, False),  # No name
            (False, False, True, False, False),  # Invalid court
        ],
    )
    def test_document_is_publishable_conditions(
        self,
        mock_api_client,
        is_held,
        is_parked,
        has_name,
        has_valid_court,
        publishable,
    ):
        document = Document("test/1234", mock_api_client)
        document.is_parked = is_parked
        document.is_held = is_held
        document.has_name = has_name
        document.has_valid_court = has_valid_court

        assert document.is_publishable is publishable

    def test_document_validation_failure_messages_if_no_messages(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_parked = False
        document.is_held = False
        document.has_valid_court = True

        assert document.validation_failure_messages == []

    def test_judgment_validation_failure_messages_if_failing(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_parked = True
        document.is_held = True
        document.has_name = False
        document.has_valid_court = False

        assert document.validation_failure_messages == sorted(
            [
                "This document is currently parked at a temporary URI",
                "This document is currently on hold",
                "This document has no name",
                "The court for this document is not valid",
            ]
        )


class TestDocumentPublication:
    def test_publish_fails_if_not_publishable(self, mock_api_client):
        with pytest.raises(CannotPublishUnpublishableDocument):
            document = Document("test/1234", mock_api_client)
            document.is_publishable = False
            document.publish()
            mock_api_client.set_published.assert_not_called()

    @patch("caselawclient.models.documents.notify_changed")
    @patch("caselawclient.models.documents.publish_documents")
    def test_publish(
        self, mock_publish_documents, mock_notify_changed, mock_api_client
    ):
        document = Document("test/1234", mock_api_client)
        document.is_publishable = True
        document.publish()
        mock_publish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", True)
        mock_notify_changed.assert_called_once_with(
            uri="test/1234", status="published", enrich=True
        )

    @patch("caselawclient.models.documents.notify_changed")
    @patch("caselawclient.models.documents.unpublish_documents")
    def test_unpublish(
        self, mock_unpublish_documents, mock_notify_changed, mock_api_client
    ):
        document = Document("test/1234", mock_api_client)
        document.unpublish()
        mock_unpublish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", False)
        mock_api_client.break_checkout.assert_called_once_with("test/1234")
        mock_notify_changed.assert_called_once_with(
            uri="test/1234", status="not published", enrich=False
        )


class TestDocumentHold:
    def test_hold(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.hold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234", "editor-hold", "true"
        )

    def test_unhold(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.unhold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234", "editor-hold", "false"
        )