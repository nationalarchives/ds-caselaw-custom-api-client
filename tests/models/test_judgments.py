import datetime
from unittest.mock import Mock, patch

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import JudgmentNotFoundError
from caselawclient.models.judgments import (
    JUDGMENT_STATUS_HOLD,
    JUDGMENT_STATUS_IN_PROGRESS,
    JUDGMENT_STATUS_PUBLISHED,
    CannotPublishUnpublishableJudgment,
    Judgment,
)


@pytest.fixture
def mock_api_client():
    return Mock(spec=MarklogicApiClient)


class TestJudgment:
    def test_uri_strips_slashes(self, mock_api_client):
        judgment = Judgment("////test/1234/////", mock_api_client)

        assert judgment.uri == "test/1234"

    def test_public_uri(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)

        assert (
            judgment.public_uri == "https://caselaw.nationalarchives.gov.uk/test/1234"
        )

    def test_judgment_exists_check(self, mock_api_client):
        mock_api_client.judgment_exists.return_value = False
        with pytest.raises(JudgmentNotFoundError):
            Judgment("not_a_real_judgment", mock_api_client)

    def test_judgment_neutral_citation(self, mock_api_client):
        mock_api_client.get_judgment_citation.return_value = "[2023] TEST 1234"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.neutral_citation == "[2023] TEST 1234"
        mock_api_client.get_judgment_citation.assert_called_once_with("test/1234")

    def test_judgment_name(self, mock_api_client):
        mock_api_client.get_judgment_name.return_value = (
            "Test Judgment v Test Judgement"
        )

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.name == "Test Judgment v Test Judgement"
        mock_api_client.get_judgment_name.assert_called_once_with("test/1234")

    def test_judgment_court(self, mock_api_client):
        mock_api_client.get_judgment_court.return_value = "Court of Testing"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.court == "Court of Testing"
        mock_api_client.get_judgment_court.assert_called_once_with("test/1234")

    def test_judgment_date_as_string(self, mock_api_client):
        mock_api_client.get_judgment_work_date.return_value = "2023-02-03"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.judgment_date_as_string == "2023-02-03"
        assert judgment.judgment_date_as_date == datetime.date(2023, 2, 3)
        mock_api_client.get_judgment_work_date.assert_called_once_with("test/1234")

    def test_judgment_is_published(self, mock_api_client):
        mock_api_client.get_published.return_value = True

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.is_published is True
        mock_api_client.get_published.assert_called_once_with("test/1234")

    def test_judgment_is_held(self, mock_api_client):
        mock_api_client.get_property.return_value = False

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.is_held is False
        mock_api_client.get_property.assert_called_once_with("test/1234", "editor-hold")

    def test_judgment_is_sensitive(self, mock_api_client):
        mock_api_client.get_sensitive.return_value = True

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.is_sensitive is True
        mock_api_client.get_sensitive.assert_called_once_with("test/1234")

    def test_judgment_is_anonymised(self, mock_api_client):
        mock_api_client.get_anonymised.return_value = True

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.is_anonymised is True
        mock_api_client.get_anonymised.assert_called_once_with("test/1234")

    def test_judgment_has_supplementary_materials(self, mock_api_client):
        mock_api_client.get_supplemental.return_value = True

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.has_supplementary_materials is True
        mock_api_client.get_supplemental.assert_called_once_with("test/1234")

    def test_judgment_source_name(self, mock_api_client):
        mock_api_client.get_property.return_value = "Test Name"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.source_name == "Test Name"
        mock_api_client.get_property.assert_called_once_with("test/1234", "source-name")

    def test_judgment_source_email(self, mock_api_client):
        mock_api_client.get_property.return_value = "testemail@example.com"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.source_email == "testemail@example.com"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234", "source-email"
        )

    def test_judgment_consignment_reference(self, mock_api_client):
        mock_api_client.get_property.return_value = "TDR-2023-ABC"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.consignment_reference == "TDR-2023-ABC"
        mock_api_client.get_property.assert_called_once_with(
            "test/1234", "transfer-consignment-reference"
        )

    @patch("caselawclient.models.judgments.generate_docx_url")
    def test_judgment_docx_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.docx"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.docx_url == "https://example.com/mock.docx"
        mock_url_generator.assert_called_once

    @patch("caselawclient.models.judgments.generate_pdf_url")
    def test_judgment_pdf_url(self, mock_url_generator, mock_api_client):
        mock_url_generator.return_value = "https://example.com/mock.pdf"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.pdf_url == "https://example.com/mock.pdf"
        mock_url_generator.assert_called_once

    def test_judgment_assigned_to(self, mock_api_client):
        mock_api_client.get_property.return_value = "testuser"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.assigned_to == "testuser"
        mock_api_client.get_property.assert_called_once_with("test/1234", "assigned-to")

    def test_judgment_content_as_xml(self, mock_api_client):
        mock_api_client.get_judgment_xml.return_value = "<xml></xml>"

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.content_as_xml() == "<xml></xml>"
        mock_api_client.get_judgment_xml.assert_called_once_with(
            "test/1234", show_unpublished=True
        )

    def test_judgment_status(self, mock_api_client):
        in_progress_judgment = Judgment("test/1234", mock_api_client)
        in_progress_judgment.is_held = False
        in_progress_judgment.is_published = False
        assert in_progress_judgment.status == JUDGMENT_STATUS_IN_PROGRESS

        on_hold_judgment = Judgment("test/1234", mock_api_client)
        on_hold_judgment.is_held = True
        on_hold_judgment.is_published = False
        assert on_hold_judgment.status == JUDGMENT_STATUS_HOLD

        published_judgment = Judgment("test/1234", mock_api_client)
        on_hold_judgment.is_held = False
        published_judgment.is_published = True
        assert published_judgment.status == JUDGMENT_STATUS_PUBLISHED


class TestJudgmentValidation:
    def test_judgment_is_failure(self, mock_api_client):
        successful_judgment = Judgment("test/1234", mock_api_client)
        failing_judgment = Judgment("failures/test/1234", mock_api_client)

        assert successful_judgment.is_failure is False
        assert failing_judgment.is_failure is True

    def test_judgment_is_parked(self, mock_api_client):
        normal_judgment = Judgment("test/1234", mock_api_client)
        parked_judgment = Judgment("parked/a1b2c3d4", mock_api_client)

        assert normal_judgment.is_parked is False
        assert parked_judgment.is_parked is True

    def test_has_name(self, mock_api_client):
        judgment_with_name = Judgment("test/1234", mock_api_client)
        judgment_with_name.name = "Judgment v Judgement"

        judgment_without_name = Judgment("test/1234", mock_api_client)
        judgment_without_name.name = ""

        assert judgment_with_name.has_name is True
        assert judgment_without_name.has_name is False

    def test_has_ncn(self, mock_api_client):
        judgment_with_ncn = Judgment("test/1234", mock_api_client)
        judgment_with_ncn.neutral_citation = "[2023] TEST 1234"

        judgment_without_ncn = Judgment("test/1234", mock_api_client)
        judgment_without_ncn.neutral_citation = ""

        assert judgment_with_ncn.has_ncn is True
        assert judgment_without_ncn.has_ncn is False

    @pytest.mark.parametrize(
        "ncn_to_test, valid",
        [
            ("[2022] UKSC 1", True),
            ("[1604] EWCA Crim 555", True),
            ("[2022] EWHC 1 (Comm)", True),
            ("[1999] EWCOP 7", True),
            ("[2022] UKUT 1 (IAC)", True),
            ("[2022] EAT 1", True),
            ("[2022] UKFTT 1 (TC)", True),
            ("[2022] UKFTT 1 (GRC)", True),
            ("[2022] EWHC 1 (KB)", True),
            ("", False),
            ("1604] EWCA Crim 555", False),
            ("[2022 EWHC 1 Comm", False),
            ("[1999] EWCOP", False),
            ("[2022] UKUT B1 IAC", False),
            ("[2022] EAT A", False),
            ("[2022] NOTACOURT 1 TC", False),
        ],
    )
    def test_has_valid_ncn(self, mock_api_client, ncn_to_test, valid):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.neutral_citation = ncn_to_test

        assert judgment.has_valid_ncn is valid

    def test_has_court(self, mock_api_client):
        judgment_with_court = Judgment("test/1234", mock_api_client)
        judgment_with_court.court = "[2023] TEST 1234"

        judgment_without_court = Judgment("test/1234", mock_api_client)
        judgment_without_court.court = ""

        assert judgment_with_court.has_court is True
        assert judgment_without_court.has_court is False

    @pytest.mark.parametrize(
        "is_parked, is_held, has_name, has_ncn, has_valid_ncn, has_court, publishable",
        [
            (False, False, True, True, True, True, True),  # Publishable
            (False, True, True, True, True, True, False),  # Held
            (True, False, True, True, True, True, False),  # Parked
            (False, False, False, True, True, True, False),  # No name
            (False, False, True, False, True, True, False),  # No NCN
            (False, False, True, True, False, True, False),  # Invalid NCN
            (False, False, True, True, True, False, False),  # No court
        ],
    )
    def test_judgment_is_publishable_conditions(
        self,
        mock_api_client,
        is_held,
        is_parked,
        has_name,
        has_ncn,
        has_valid_ncn,
        has_court,
        publishable,
    ):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.is_parked = is_parked
        judgment.is_held = is_held
        judgment.has_name = has_name
        judgment.has_ncn = has_ncn
        judgment.has_valid_ncn = has_valid_ncn
        judgment.has_court = has_court

        assert judgment.is_publishable is publishable

    def test_judgment_validation_failure_messages_if_no_messages(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.is_parked = False
        judgment.is_held = False
        judgment.has_name = True
        judgment.has_ncn = True
        judgment.has_valid_ncn = True
        judgment.has_court = True

        assert judgment.validation_failure_messages == []

    def test_judgment_validation_failure_messages_if_failing(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.is_parked = True
        judgment.is_held = True
        judgment.has_name = False
        judgment.has_ncn = False
        judgment.has_valid_ncn = False
        judgment.has_court = False

        assert judgment.validation_failure_messages == sorted(
            [
                "This judgment is currently parked at a temporary URI",
                "This judgment is currently on hold",
                "This judgment has no name",
                "This judgment has no neutral citation number",
                "The neutral citation number of this judgment is not valid",
                "This judgment has no court",
            ]
        )


class TestJudgmentPublication:
    def test_publish_fails_if_not_publishable(self, mock_api_client):
        with pytest.raises(CannotPublishUnpublishableJudgment):
            judgment = Judgment("test/1234", mock_api_client)
            judgment.is_publishable = False
            judgment.publish()
            mock_api_client.set_published.assert_not_called()

    @patch("caselawclient.models.judgments.notify_changed")
    @patch("caselawclient.models.judgments.publish_documents")
    def test_publish(
        self, mock_publish_documents, mock_notify_changed, mock_api_client
    ):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.is_publishable = True
        judgment.publish()
        mock_publish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", True)
        mock_notify_changed.assert_called_once_with(
            uri="test/1234", status="published", enrich=True
        )

    @patch("caselawclient.models.judgments.notify_changed")
    @patch("caselawclient.models.judgments.unpublish_documents")
    def test_unpublish(
        self, mock_unpublish_documents, mock_notify_changed, mock_api_client
    ):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.unpublish()
        mock_unpublish_documents.assert_called_once_with("test/1234")
        mock_api_client.set_published.assert_called_once_with("test/1234", False)
        mock_api_client.break_checkout.assert_called_once_with("test/1234")
        mock_notify_changed.assert_called_once_with(
            uri="test/1234", status="not published", enrich=False
        )


class TestJudgmentHold:
    def test_hold(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.hold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234", "editor-hold", "true"
        )

    def test_unhold(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.unhold()
        mock_api_client.set_property.assert_called_once_with(
            "test/1234", "editor-hold", "false"
        )
