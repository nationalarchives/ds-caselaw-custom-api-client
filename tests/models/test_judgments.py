from unittest.mock import patch

import pytest

from caselawclient.errors import DocumentNotFoundError
from caselawclient.factories import PressSummaryFactory
from caselawclient.models.judgments import Judgment


class TestJudgment:
    def test_best_identifier(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.neutral_citation = "[2023] TEST 1234"
        assert judgment.best_human_identifier == judgment.neutral_citation


class TestJudgmentValidation:
    def test_has_ncn(self, mock_api_client):
        document_with_ncn = Judgment("test/1234", mock_api_client)
        document_with_ncn.neutral_citation = "[2023] TEST 1234"

        document_without_ncn = Judgment("test/1234", mock_api_client)
        document_without_ncn.neutral_citation = ""

        assert document_with_ncn.has_ncn is True
        assert document_without_ncn.has_ncn is False

    def test_judgment_neutral_citation(self, mock_api_client):
        mock_api_client.get_judgment_xml_bytestring.return_value = b"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                        xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:cite>[2023] TEST 1234</uk:cite>
                        </proprietary>
                    </meta>
                </judgment>
            </akomaNtoso>
        """

        judgment = Judgment("test/1234", mock_api_client)

        assert judgment.neutral_citation == "[2023] TEST 1234"
        mock_api_client.get_judgment_xml_bytestring.assert_called_once_with(
            "test/1234",
            show_unpublished=True,
        )

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

    def test_judgment_validation_failure_messages_if_failing(self, mock_api_client):
        judgment = Judgment("test/1234", mock_api_client)
        judgment.is_failure = True
        judgment.is_parked = True
        judgment.is_held = True
        judgment.has_name = False
        judgment.has_ncn = False
        judgment.has_valid_ncn = False
        judgment.has_valid_court = False

        assert judgment.validation_failure_messages == sorted(
            [
                "This document failed to parse",
                "This judgment is currently parked at a temporary URI",
                "This judgment is currently on hold",
                "This judgment has no name",
                "This judgment has no neutral citation number",
                "The neutral citation number of this judgment is not valid",
                "The court for this judgment is not valid",
            ],
        )


class TestLinkedDocuments:
    @patch("caselawclient.models.press_summaries.PressSummary")
    def test_linked_document(self, document_mock, mock_api_client):
        press_summary = PressSummaryFactory.build()
        document_mock.return_value = press_summary

        judgment = Judgment("/test/1234", mock_api_client)

        assert judgment.linked_document == press_summary
        document_mock.assert_called_once_with(
            "test/1234/press-summary/1",
            mock_api_client,
        )

    @patch("caselawclient.models.press_summaries.PressSummary")
    def test_linked_document_returns_nothing_when_does_not_exist(
        self,
        document_mock,
        mock_api_client,
    ):
        document_mock.side_effect = DocumentNotFoundError()

        judgment = Judgment("/test/1234", mock_api_client)
        assert judgment.linked_document is None
