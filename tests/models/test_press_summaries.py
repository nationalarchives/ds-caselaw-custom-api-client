from unittest.mock import Mock

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.models.press_summaries import PressSummary


@pytest.fixture
def mock_api_client():
    return Mock(spec=MarklogicApiClient)


class TestPressSummaryValidation:
    def test_has_ncn(self, mock_api_client):
        document_with_ncn = PressSummary("test/1234", mock_api_client)
        document_with_ncn.neutral_citation = "[2023] TEST 1234"

        document_without_ncn = PressSummary("test/1234", mock_api_client)
        document_without_ncn.neutral_citation = ""

        assert document_with_ncn.has_ncn is True
        assert document_without_ncn.has_ncn is False

    def test_press_summary_neutral_citation(self, mock_api_client):
        mock_api_client.get_judgment_xml.return_value = """
        <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
            xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
        <doc name="pressSummary">
            <mainBody>
            <p>
                some paragraph
            </p>
            <p>
                <docTitle>
                    <span>Press Summary of Case A</span>
                </docTitle>
                <neutralCitation style="font-weight:bold;font-family:Garamond">[2016] TEST 49</neutralCitation>
            </p>
            </mainBody>
        </doc>
        </akomaNtoso>
        """

        press_summary = PressSummary("test/1234", mock_api_client)

        assert press_summary.neutral_citation == "[2016] TEST 49"
        mock_api_client.get_judgment_xml.assert_called_once_with(
            "test/1234", show_unpublished=True
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
        press_summary = PressSummary("test/1234", mock_api_client)
        press_summary.neutral_citation = ncn_to_test

        assert press_summary.has_valid_ncn is valid

    def test_press_summary_validation_failure_messages_if_failing(
        self, mock_api_client
    ):
        press_summary = PressSummary("test/1234", mock_api_client)
        press_summary.is_parked = True
        press_summary.is_held = True
        press_summary.has_name = False
        press_summary.has_ncn = False
        press_summary.has_valid_ncn = False
        press_summary.has_valid_court = False

        assert press_summary.validation_failure_messages == sorted(
            [
                "This press summary is currently parked at a temporary URI",
                "This press summary is currently on hold",
                "This press summary has no name",
                "This press summary has no neutral citation number",
                "The neutral citation number of this press summary is not valid",
                "The court for this press summary is not valid",
            ]
        )