import datetime
import os
import re

import pytest

from caselawclient.models.documents import (
    DocumentBody,
)
from caselawclient.models.documents.body import (
    UnparsableDate,
)


class TestDocumentBody:
    def test_document_parsed(self):
        body = DocumentBody(b"""
            <akomaNtoso>Parsing succeeded</akomaNtoso>
        """)

        assert body.failed_to_parse is False

    def test_document_failed_to_parse(self):
        body = DocumentBody(b"""
            <error>Parsing failed</error>
        """)

        assert body.failed_to_parse is True

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_name(self, opening_tag, closing_tag):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.name == "Test Claimant v Test Defendant"

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court(self, opening_tag, closing_tag):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.court == "Court of Testing"

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_jurisdiction(self, opening_tag, closing_tag):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.jurisdiction == "SoftwareTesting"

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court_and_jurisdiction_with_jurisdiction(
        self,
        opening_tag,
        closing_tag,
    ):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.court_and_jurisdiction_identifier_string == "UKFTT-CourtOfTesting/SoftwareTesting"

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_court_and_jurisdiction_without_jurisdiction(
        self,
        opening_tag,
        closing_tag,
    ):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.court_and_jurisdiction_identifier_string == "CourtOfTesting"

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_date_as_string(self, opening_tag, closing_tag):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.document_date_as_string == "2023-02-03"
        assert body.document_date_as_date == datetime.date(2023, 2, 3)

    @pytest.mark.parametrize(
        "opening_tag, closing_tag",
        [
            ("judgment", "judgment"),
            ('doc name="pressSummary"', "doc"),
        ],
    )
    def test_bad_date_as_string(self, opening_tag, closing_tag):
        body = DocumentBody(
            f"""
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
        """.encode()
        )

        assert body.document_date_as_string == "kitten"
        with pytest.warns(UnparsableDate):
            assert body.document_date_as_date is None

    def test_absent_date_as_string(self):
        body = DocumentBody(b"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            </akomaNtoso>
        """)

        assert body.document_date_as_string == ""
        assert body.document_date_as_date is None

    def test_dates(self, mock_api_client):
        body = DocumentBody(b"""
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
        """)

        assert body.enrichment_datetime.year == 2024
        assert body.transformation_datetime.year == 2026
        assert body.get_latest_manifestation_datetime().year == 2026
        assert body.get_latest_manifestation_type() == "transform"
        assert [x.year for x in body.get_manifestation_datetimes("tna-enriched")] == [2024, 2023]

    def test_document_with_no_dates(self, mock_api_client):
        body = DocumentBody(b"""
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
        """)

        assert body.enrichment_datetime is None
        assert body.transformation_datetime is None
        assert body.get_latest_manifestation_datetime() is None
        assert body.get_manifestation_datetimes("any") == []

    def test_content_as_html_for_standard_judgment(self):
        """Run our HTML XSLT on a judgment to make sure it's formatting as we expect."""

        with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "xslt", "test_standard_judgment.xml"), "r"
        ) as file:
            xml_document = file.read()

        with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "xslt", "test_standard_judgment.html"), "r"
        ) as file:
            html_document = file.read()

            # The HTML which comes out of the XSLT doesn't have extra whitespace, but our test document does to aid readability.
            # This reassembles our pretty HTML into a straight string for comparison purposes.
            html_without_whitespace = "".join(re.split(r"\s*\n\s*", html_document.strip()))

        body = DocumentBody(xml_document.encode())

        assert body.content_as_html == html_without_whitespace
