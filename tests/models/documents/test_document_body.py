import datetime
import os

import pytest
from bs4 import BeautifulSoup

from caselawclient.factories import DocumentBodyFactory
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

        assert body.enrichment_datetime and body.enrichment_datetime.year == 2024
        assert body.transformation_datetime and body.transformation_datetime.year == 2026
        latest_manifestation_datetime = body.get_latest_manifestation_datetime()
        assert latest_manifestation_datetime and latest_manifestation_datetime.year == 2026
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
            target_html = file.read()
            prettified_target_html = BeautifulSoup(target_html, features="html.parser").prettify()

        body = DocumentBody(xml_document.encode())
        transformed_html = body.content_as_html(image_base_url="https://test.caselaw.nationalarchives.gov.uk/")
        prettified_transformed_html = BeautifulSoup(transformed_html, features="html.parser").prettify()

        assert prettified_transformed_html == prettified_target_html

    def test_actual_content_body(self):
        body = DocumentBodyFactory.build("""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <judgment name="decision">
                <meta/><header/>
                <judgmentBody>
                <decision>
                a
                <p/>
                </decision>
                </judgmentBody>
            </judgment>
            </akomaNtoso>""")
        assert body.has_actual_content

    def test_actual_content_header(self):
        body = DocumentBodyFactory.build("""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <judgment name="decision">
                <meta/>
                <header>a</header>
                <judgmentBody>
                <decision>
                <p/>
                </decision>
                </judgmentBody>
            </judgment>
            </akomaNtoso>""")
        assert body.has_actual_content

    def test_no_actual_content(self):
        body = DocumentBodyFactory.build("""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
            <judgment name="decision">
                <meta/><header/>
                <judgmentBody>
                <decision>
                <p/>
                </decision>
                </judgmentBody>
            </judgment>
            </akomaNtoso>""")

        assert not (body.has_actual_content)
