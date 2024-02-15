import datetime
import json
import os
from unittest.mock import PropertyMock, patch

import pytest
import time_machine

from caselawclient.errors import (
    DocumentNotFoundError,
    NotSupportedOnVersion,
    OnlySupportedOnVersion,
)
from caselawclient.models.documents import (
    DOCUMENT_STATUS_HOLD,
    DOCUMENT_STATUS_IN_PROGRESS,
    DOCUMENT_STATUS_NEW,
    DOCUMENT_STATUS_PUBLISHED,
    CannotPublishUnpublishableDocument,
    Document,
    DocumentNotSafeForDeletion,
    UnparsableDate,
)
from caselawclient.models.judgments import Judgment
from tests.factories import JudgmentFactory
from tests.test_helpers import MockMultipartResponse


class TestDocument:
    def test_has_sensible_repr_with_name_and_judgment(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork><FRBRname value="Document Name"/></FRBRWork>
                            <FRBRManifestation>
                            </FRBRManifestation>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )
        document = Judgment("test/1234", mock_api_client)
        assert str(document) == "<judgment test/1234: Document Name>"

    def test_has_sensible_repr_without_name_or_subclass(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        assert str(document) == "<document test/1234: un-named>"

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

    def test_document_failed_to_parse(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <error>Parsing failed</error>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.failed_to_parse is True

    def test_document_parsed(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso>Parsing succeeded</akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.failed_to_parse is False

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

    def test_judgment_is_locked(self, mock_api_client):
        mock_api_client.get_judgment_checkout_status_message.return_value = (
            "Judgment locked"
        )
        document = Document("test/1234", mock_api_client)

        assert document.is_locked is True

    def test_judgment_is_not_locked(self, mock_api_client):
        mock_api_client.get_judgment_checkout_status_message.return_value = None
        document = Document("test/1234", mock_api_client)

        assert document.is_locked is False

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

    def test_document_status(self, mock_api_client):
        new_document = Document("test/1234", mock_api_client)
        new_document.is_held = False
        new_document.is_published = False
        new_document.assigned_to = ""
        assert new_document.status == DOCUMENT_STATUS_NEW

        in_progress_document = Document("test/1234", mock_api_client)
        in_progress_document.is_held = False
        in_progress_document.is_published = False
        in_progress_document.assigned_to = "duck"
        assert in_progress_document.status == DOCUMENT_STATUS_IN_PROGRESS

        on_hold_document = Document("test/1234", mock_api_client)
        on_hold_document.is_held = True
        on_hold_document.is_published = False
        on_hold_document.assigned_to = "duck"
        assert on_hold_document.status == DOCUMENT_STATUS_HOLD

        published_document = Document("test/1234", mock_api_client)
        published_document.is_held = False
        published_document.is_published = True
        published_document.assigned_to = "duck"
        assert published_document.status == DOCUMENT_STATUS_PUBLISHED

    def test_document_best_identifier(self, mock_api_client):
        example_document = Document("uri", mock_api_client)
        assert example_document.best_human_identifier is None

    def test_document_version_of_a_version_fails(self, mock_api_client):
        version_document = Document("test/1234_xml_versions/9-1234", mock_api_client)
        with pytest.raises(NotSupportedOnVersion):
            version_document.versions_as_documents

    def test_document_versions_happy_case(self, mock_api_client):
        version_document = Document("test/1234", mock_api_client)
        version_document.versions = [
            {"uri": "test/1234_xml_versions/2-1234.xml"},
            {"uri": "test/1234_xml_versions/1-1234.xml"},
        ]
        version_document.versions_as_documents[0].uri = (
            "test/1234_xml_versions/2-1234.xml"
        )

    def test_document_version_number_when_not_version(self, mock_api_client):
        base_document = Document("test/1234", mock_api_client)
        with pytest.raises(OnlySupportedOnVersion):
            base_document.version_number
        assert not base_document.is_version

    def test_document_version_number_when_is_version(self, mock_api_client):
        version_document = Document("test/1234_xml_versions/9-1234", mock_api_client)
        assert version_document.version_number == 9
        assert version_document.is_version

    def test_number_of_mentions_when_no_mentions(self, mock_api_client):
        mock_api_client.eval_xslt.return_value = MockMultipartResponse(
            """
            <article>
                <p>An article with no mark elements.</p>
            </article>
        """.encode(
                "utf-8"
            )
        )

        document = Document("test/1234", mock_api_client)

        assert document.number_of_mentions("some") == 0

    def test_number_of_mentions_when_mentions(self, mock_api_client):
        mock_api_client.eval_xslt.return_value = MockMultipartResponse(
            """
            <article>
                <p>
                    An article with <mark id="mark_0">some</mark> mark elements, and <mark id="mark_1">some</mark> more.
                </p>
            </article>
        """.encode(
                "utf-8"
            )
        )

        document = Document("test/1234", mock_api_client)

        assert document.number_of_mentions("some") == 2

    def test_validates_against_schema(self, mock_api_client):
        mock_api_client.validate_document.return_value = True

        document = Document("test/1234", mock_api_client)

        assert document.validates_against_schema is True

        mock_api_client.validate_document.assert_called_with(document.uri)


class TestDocumentValidation:
    def test_judgment_is_failure(self, mock_api_client):
        successful_document = Document("test/1234", mock_api_client)
        failing_document = Document("failures/test/1234", mock_api_client)

        successful_document.failed_to_parse = False
        failing_document.failed_to_parse = True

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

        document_with_court_and_jurisdiction = Document("test/1234", mock_api_client)
        document_with_court_and_jurisdiction.court = "UKFTT-GRC"
        document_with_court_and_jurisdiction.jurisdiction = "InformationRights"

        assert document_with_court.has_valid_court is True
        assert document_with_court_and_jurisdiction.has_valid_court is True
        assert document_without_court.has_valid_court is False

    @pytest.mark.parametrize(
        "failed_to_parse, is_parked, is_held, has_name, has_valid_court, publishable",
        [
            (False, False, False, True, True, True),  # Publishable
            (True, False, False, False, False, False),  # Parser failure
            (False, False, True, True, True, False),  # Held
            (False, True, False, True, True, False),  # Parked
            (False, False, False, False, True, False),  # No name
            (False, False, False, True, False, False),  # Invalid court
        ],
    )
    def test_document_is_publishable_conditions(
        self,
        mock_api_client,
        failed_to_parse,
        is_held,
        is_parked,
        has_name,
        has_valid_court,
        publishable,
    ):
        document = Document("test/1234", mock_api_client)
        document.failed_to_parse = failed_to_parse
        document.is_parked = is_parked
        document.is_held = is_held
        document.has_name = has_name
        document.has_valid_court = has_valid_court

        assert document.is_publishable is publishable

    def test_document_validation_failure_messages_if_no_messages(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso xmlns:akn="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                        xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment><meta><identification><FRBRWork>
                <FRBRname value="Test Claimant v Test Defendant"/>
                </FRBRWork></identification></meta></judgment>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)
        document.is_parked = False
        document.is_held = False
        document.has_valid_court = True

        assert document.validation_failure_messages == []

    def test_judgment_validation_failure_messages_if_failing(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.failed_to_parse = True
        document.is_parked = True
        document.is_held = True
        document.has_name = False
        document.has_valid_court = False

        assert document.validation_failure_messages == sorted(
            [
                "This document failed to parse",
                "This document is currently parked at a temporary URI",
                "This document is currently on hold",
                "This document has no name",
                "The court for this document is not valid",
            ]
        )


class TestDocumentPublish:
    def test_publish_fails_if_not_publishable(self, mock_api_client):
        with pytest.raises(CannotPublishUnpublishableDocument):
            document = Document("test/1234", mock_api_client)
            document.is_publishable = False
            document.publish()
            mock_api_client.set_published.assert_not_called()

    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.publish_documents")
    @patch("caselawclient.models.documents.Document.enrich")
    def test_publish(
        self,
        mock_enrich,
        mock_publish_documents,
        mock_announce_document_event,
        mock_api_client,
    ):
        document = Document("test/1234", mock_api_client)
        document.is_publishable = True
        document.publish()
        mock_publish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", True)
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234", status="publish"
        )
        mock_enrich.assert_called_once()


class TestDocumentUnpublish:
    @patch("caselawclient.models.documents.announce_document_event")
    @patch("caselawclient.models.documents.unpublish_documents")
    def test_unpublish(
        self, mock_unpublish_documents, mock_announce_document_event, mock_api_client
    ):
        document = Document("test/1234", mock_api_client)
        document.unpublish()
        mock_unpublish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", False)
        mock_api_client.break_checkout.assert_called_once_with("test/1234")
        mock_announce_document_event.assert_called_once_with(
            uri="test/1234", status="unpublish"
        )


class TestDocumentEnrichedRecently:
    def test_enriched_recently_returns_false_when_never_enriched(self, mock_api_client):
        document = Document("test/1234", mock_api_client)

        assert document.enriched_recently is False

    def test_enriched_recently_returns_true_within_cooldown(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.enrichment_datetime = datetime.datetime.now(
            tz=datetime.timezone.utc
        ) - datetime.timedelta(seconds=30)

        assert document.enriched_recently is True

    def test_enriched_recently_returns_false_outside_cooldown(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.enrichment_datetime = datetime.datetime.now(
            tz=datetime.timezone.utc
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
        self, mock_api_client, enriched_recently, validates_against_schema, can_enrich
    ):
        document = Document("test/1234", mock_api_client)
        with patch.object(
            Document, "enriched_recently", new_callable=PropertyMock
        ) as mock_enriched_recently:
            with patch.object(
                Document, "validates_against_schema", new_callable=PropertyMock
            ) as mock_validates_against_schema:
                mock_enriched_recently.return_value = enriched_recently
                mock_validates_against_schema.return_value = validates_against_schema

                assert document.can_enrich is can_enrich


class TestDocumentEnrich:
    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.documents.announce_document_event")
    def test_force_enrich(self, mock_announce_document_event, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.force_enrich()

        mock_api_client.set_property.assert_called_once_with(
            "test/1234", "last_sent_to_enrichment", "1955-11-05T06:00:00+00:00"
        )

        mock_announce_document_event.assert_called_once_with(
            uri="test/1234", status="enrich", enrich=True
        )

    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_no_enrich_when_can_enrich_is_false(self, force_enrich, mock_api_client):
        document = Document("test/1234", mock_api_client)
        with patch.object(
            Document, "can_enrich", new_callable=PropertyMock
        ) as can_enrich:
            can_enrich.return_value = False
            document.enrich()
            force_enrich.assert_not_called()

    @patch("caselawclient.models.documents.Document.force_enrich")
    def test_enrich_when_can_enrich_is_true(self, force_enrich, mock_api_client):
        document = Document("test/1234", mock_api_client)
        with patch.object(
            Document, "can_enrich", new_callable=PropertyMock
        ) as can_enrich:
            can_enrich.return_value = True
            document.enrich()
            force_enrich.assert_called()


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


class TestDocumentDelete:
    def test_not_safe_to_delete_if_published(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_published = True

        assert document.safe_to_delete is False

    def test_safe_to_delete_if_unpublished(self, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.is_published = False

        assert document.safe_to_delete is True

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_safe(self, mock_aws_delete_documents, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.safe_to_delete = True

        document.delete()

        mock_api_client.delete_judgment.assert_called_once_with("test/1234")
        mock_aws_delete_documents.assert_called_once_with("test/1234")

    @patch("caselawclient.models.documents.delete_documents_from_private_bucket")
    def test_delete_if_unsafe(self, mock_aws_delete_documents, mock_api_client):
        document = Document("test/1234", mock_api_client)
        document.safe_to_delete = False

        with pytest.raises(DocumentNotSafeForDeletion):
            document.delete()

        mock_api_client.delete_judgment.assert_not_called()
        mock_aws_delete_documents.assert_not_called()


class TestDocumentMetadata:
    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_name(self, opening_tag, closing_tag, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Test Claimant v Test Defendant"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.name == "Test Claimant v Test Defendant"
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court(self, opening_tag, closing_tag, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <proprietary>
                            <uk:court>Court of Testing</uk:court>
                        </proprietary>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.court == "Court of Testing"
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_jurisdiction(self, opening_tag, closing_tag, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <proprietary>
                            <uk:jurisdiction>SoftwareTesting</uk:jurisdiction>
                        </proprietary>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.jurisdiction == "SoftwareTesting"
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court_and_jurisdiction_with_jurisdiction(
        self, opening_tag, closing_tag, mock_api_client
    ):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <proprietary>
                            <uk:court>UKFTT-CourtOfTesting</uk:court>
                            <uk:jurisdiction>SoftwareTesting</uk:jurisdiction>
                        </proprietary>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert (
            document.court_and_jurisdiction_identifier_string
            == "UKFTT-CourtOfTesting/SoftwareTesting"
        )
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court_and_jurisdiction_without_jurisdiction(
        self, opening_tag, closing_tag, mock_api_client
    ):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <proprietary>
                            <uk:court>CourtOfTesting</uk:court>
                        </proprietary>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.court_and_jurisdiction_identifier_string == "CourtOfTesting"
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_date_as_string(self, opening_tag, closing_tag, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRdate date="2023-02-03"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.document_date_as_string == "2023-02-03"
        assert document.document_date_as_date == datetime.date(2023, 2, 3)
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_bad_date_as_string(self, opening_tag, closing_tag, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = f"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <{opening_tag}>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRdate date="kitten"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                </{closing_tag}>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.document_date_as_string == "kitten"
        with pytest.warns(UnparsableDate):
            assert document.document_date_as_date is None
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    def test_absent_date_as_string(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.document_date_as_string == ""
        assert document.document_date_as_date is None

    def test_dates(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRManifestation>
                                <FRBRdate date="2024-08-31T16:41:01" name="tna-enriched"/>
                                <FRBRdate date="2023-08-31T16:41:01" name="tna-enriched"/>
                                <FRBRdate date="2025-08-31T16:41:01" name="transform"/>
                                <FRBRdate date="2026-08-31T16:41:01" name="transform"/>
                            </FRBRManifestation>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.enrichment_datetime.year == 2024
        assert document.transformation_datetime.year == 2026
        assert document.get_latest_manifestation_datetime().year == 2026
        assert document.get_latest_manifestation_type() == "transform"
        assert [
            x.year for x in document.get_manifestation_datetimes("tna-enriched")
        ] == [2024, 2023]

    def test_no_dates(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = """
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRManifestation>
                            </FRBRManifestation>
                        </identification>
                    </meta>
                </judgment>
            </akomaNtoso>
        """.encode(
            "utf-8"
        )

        document = Document("test/1234", mock_api_client)

        assert document.enrichment_datetime is None
        assert document.transformation_datetime is None
        assert document.get_latest_manifestation_datetime() is None
        assert document.get_manifestation_datetimes("any") == []

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.utilities.aws.create_sns_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"REPARSE_SNS_TOPIC": "MY_TOPIC"})
    def test_reparse_empty(self, sns, mock_api_client):
        document = JudgmentFactory().build(
            is_published=False,
            name="",
            neutral_citation="",
            court="",
            document_date_as_string="1000-01-01",
            document_noun="judgment",
        )

        document.api_client = mock_api_client
        Judgment.reparse(document)

        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123", "last_sent_to_parser", "1955-11-05T06:00:00+00:00"
        )

        # first call, second argument (the kwargs), so [0][1]
        returned_message = json.loads(
            sns.return_value.publish.call_args_list[0][1]["Message"]
        )
        # hide random parameters
        del returned_message["properties"]["timestamp"]
        del returned_message["properties"]["executionId"]

        assert returned_message == {
            "properties": {
                "messageType": "uk.gov.nationalarchives.da.messages.request.courtdocument.parse.RequestCourtDocumentParse",
                "function": "fcl-judgment-parse-request",
                "producer": "FCL",
                "parentExecutionId": None,
            },
            "parameters": {
                "s3Bucket": "MY_BUCKET",
                "s3Key": "test/2023/123/test_2023_123.docx",
                "reference": "TDR-12345",
                "originator": "FCL",
                "parserInstructions": {
                    "documentType": "judgment",
                    "metadata": {
                        "name": None,
                        "cite": None,
                        "court": None,
                        "date": None,
                        "uri": "test/2023/123",
                    },
                },
            },
        }

    @time_machine.travel(datetime.datetime(1955, 11, 5, 6))
    @patch("caselawclient.models.utilities.aws.create_sns_client")
    @patch.dict(os.environ, {"PRIVATE_ASSET_BUCKET": "MY_BUCKET"})
    @patch.dict(os.environ, {"REPARSE_SNS_TOPIC": "MY_TOPIC"})
    def test_reparse_full(self, sns, mock_api_client):
        document = JudgmentFactory().build(is_published=True)
        document.api_client = mock_api_client

        Judgment.reparse(document)

        mock_api_client.set_property.assert_called_once_with(
            "test/2023/123", "last_sent_to_parser", "1955-11-05T06:00:00+00:00"
        )

        # first call, second argument (the kwargs), so [0][1]
        returned_message = json.loads(
            sns.return_value.publish.call_args_list[0][1]["Message"]
        )
        # hide random parameters
        del returned_message["properties"]["timestamp"]
        del returned_message["properties"]["executionId"]

        assert returned_message == {
            "properties": {
                "messageType": "uk.gov.nationalarchives.da.messages.request.courtdocument.parse.RequestCourtDocumentParse",
                "function": "fcl-judgment-parse-request",
                "producer": "FCL",
                "parentExecutionId": None,
            },
            "parameters": {
                "s3Bucket": "MY_BUCKET",
                "s3Key": "test/2023/123/test_2023_123.docx",
                "reference": "TDR-12345",
                "originator": "FCL",
                "parserInstructions": {
                    "documentType": "judgment",
                    "metadata": {
                        "name": "Judgment v Judgement",
                        "cite": "[2023] Test 123",
                        "court": "Court of Testing",
                        "date": "2023-02-03",
                        "uri": "test/2023/123",
                    },
                },
            },
        }
