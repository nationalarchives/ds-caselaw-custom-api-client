"""Tests for writing resolved metadata claims into Akoma Ntoso body XML."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents.body import (
    FRBR_EXPRESSION_XPATH,
    FRBR_WORK_XPATH,
    NAME_XPATH,
    PARTIES_XPATH,
)
from caselawclient.models.documents.exceptions import UnparsableDecisionDateError
from caselawclient.models.documents.metadata.fields.field import (
    MetadataDateValue,
    MetadataField,
    MetadataPartyValue,
    MetadataStringValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import DEFAULT_NAMESPACES

EXPRESSION_DATE_XPATH = f"{FRBR_EXPRESSION_XPATH}/akn:FRBRdate/@date"
LIFECYCLE_EVENTREF_DATE_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:lifecycle/akn:eventRef/@date"
WORK_FRBRDATE_XPATH = "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date"


class TestWriteResolvedTitleToBody:
    def test_write_resolved_title_updates_frbrname(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("Resolved title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.title.write_resolved_to_body()

        assert document.body.name == "Resolved title"

    def test_suppressed_title_removes_frbrname(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("Editor title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.title.write_resolved_to_body()

        assert (
            document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname")
            == []
        )

    def test_whitespace_only_body_title_is_treated_as_empty_on_write_back(self, mock_api_client):
        body = DocumentBodyFactory.build(name="   ")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        document.metadata.title.write_resolved_to_body()

        assert document.body.name == ""
        assert (
            document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname")
            == []
        )

    def test_save_writes_resolved_title_into_xml(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("Saved title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        with patch.object(document.api_client, "document_exists", return_value=True):
            document.save(message="Sync title to XML")

        xml_tree = mock_api_client.update_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Saved title"

    def test_save_on_insert_writes_resolved_title_into_xml(self, mock_api_client):
        from caselawclient.models.judgments import Judgment
        from caselawclient.types import DocumentURIString

        body = DocumentBodyFactory.build(name="Original title")
        with patch.object(mock_api_client, "document_exists", return_value=False):
            document = Judgment.from_xml(body, mock_api_client, uri=DocumentURIString("test/new-doc"))
            document.metadata_fields.add(
                MetadataField(
                    name="title",
                    value=MetadataStringValue("Inserted title"),
                    source=MetadataSource.EDITOR,
                    id=str(uuid4()),
                    timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                )
            )
            document.save(message="Insert with title sync")

        xml_tree = mock_api_client.insert_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Inserted title"


class TestSaveMaterialisesBeforeWriteBack:
    def test_save_materialises_body_claims_before_writing_resolved_metadata_to_body(self, mock_api_client):
        """Write-back must run after materialisation so DOCUMENT claims exist before we sync XML."""
        body = DocumentBodyFactory.build(court="Body court")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        call_order: list[str] = []
        original_materialise = document._convert_body_claims_to_structured_metadata  # noqa: SLF001
        original_write_back = document._write_resolved_metadata_to_body  # noqa: SLF001

        def track_materialise() -> None:
            call_order.append("materialise")
            original_materialise()

        def track_write_back() -> None:
            call_order.append("write_back")
            original_write_back()

        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("Editor court"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        with (
            patch.object(document, "_convert_body_claims_to_structured_metadata", side_effect=track_materialise),
            patch.object(document, "_write_resolved_metadata_to_body", side_effect=track_write_back),
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml"),
        ):
            document.save(message="Ordered save")

        assert call_order == ["materialise", "write_back"]
        document_claims = document.metadata_fields.by_name("court")
        assert any(
            claim.source is MetadataSource.DOCUMENT and claim.value == MetadataStringValue("Body court")
            for claim in document_claims
        )
        assert document.body.court == "Editor court"


class TestWriteResolvedDateToBody:
    def test_write_decision_date_does_not_touch_expression_lifecycle_or_year(self, mock_api_client):
        """Date write-back is scoped to FRBRWork/FRBRdate only (see write_decision_date / clear_decision_date)."""
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment name="judgment">
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="2020-01-01" name="judgment"/>
                            </FRBRWork>
                            <FRBRExpression>
                                <FRBRdate date="2019-01-01" name="judgment"/>
                                <FRBRdate date="2019-06-01" name="transform"/>
                            </FRBRExpression>
                        </identification>
                        <lifecycle>
                            <eventRef date="2018-01-01" source="#tna"/>
                        </lifecycle>
                        <proprietary>
                            <uk:year>2020</uk:year>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )

        def unrelated_date_fields() -> dict[str, str | list[str]]:
            return {
                "expression_judgment_date": body.get_xpath_match_string(EXPRESSION_DATE_XPATH),
                "expression_transform_dates": body.get_xpath_match_strings(
                    "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression/"
                    "akn:FRBRdate[@name='transform']/@date"
                ),
                "lifecycle_eventref_date": body.get_xpath_match_string(LIFECYCLE_EVENTREF_DATE_XPATH),
                "proprietary_year": body.get_xpath_match_string(
                    "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:year/text()"
                ),
            }

        before_write = unrelated_date_fields()
        body.write_decision_date(datetime.date(2024, 6, 15))
        assert body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-06-15"
        assert unrelated_date_fields() == before_write

        before_clear = unrelated_date_fields()
        body.clear_decision_date()
        assert body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == ""
        assert unrelated_date_fields() == before_clear

    def test_write_resolved_date_updates_only_frbrwork_frbrdate(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment name="judgment">
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="2020-01-01" name="judgment"/>
                            </FRBRWork>
                            <FRBRExpression>
                                <FRBRdate date="2019-01-01" name="judgment"/>
                            </FRBRExpression>
                        </identification>
                        <lifecycle>
                            <eventRef date="2018-01-01" source="#tna"/>
                        </lifecycle>
                        <proprietary>
                            <uk:year>2020</uk:year>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        resolved = datetime.date(2024, 6, 15)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(resolved),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.date.write_resolved_to_body()

        assert document.body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-06-15"
        assert document.body.get_xpath_match_string(EXPRESSION_DATE_XPATH) == "2019-01-01"
        assert document.body.get_xpath_match_string(LIFECYCLE_EVENTREF_DATE_XPATH) == "2018-01-01"
        assert (
            document.body.get_xpath_match_string("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:year/text()")
            == "2020"
        )

    def test_write_resolved_date_does_not_create_frbrexpression(self, mock_api_client):
        body = DocumentBodyFactory.build(document_date_as_string="2020-01-01")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        assert document.body.get_xpath_nodes(FRBR_EXPRESSION_XPATH) == []

        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2024, 6, 15)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )
        document.metadata.date.write_resolved_to_body()

        assert document.body.get_xpath_nodes(FRBR_EXPRESSION_XPATH) == []
        assert document.body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-06-15"

    def test_write_resolved_date_creates_work_frbrdate_when_absent(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment name="judgment">
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        assert document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate") == []

        resolved = datetime.date(2024, 6, 15)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(resolved),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.date.write_resolved_to_body()

        assert document.body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-06-15"
        assert (
            document.body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@name"
            )
            == "judgment"
        )

    def test_write_resolved_date_with_multiple_work_frbrdates(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment name="judgment">
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="2020-01-01" name="decision"/>
                                <FRBRdate date="2025-07-29T12:47:42" name="transform"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2024, 6, 15)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.date.write_resolved_to_body()

        assert document.body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-06-15"
        transform_dates = document.body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate[@name='transform']/@date"
        )
        assert transform_dates == ["2025-07-29T12:47:42"]

        with patch.object(document.api_client, "document_exists", return_value=True):
            document.save(message="Save with multiple work FRBRdates")

    def test_suppressed_date_claim_clears_work_frbrdate_only(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="2020-01-01" name="judgment"/>
                                <FRBRdate date="2025-07-29T12:47:42" name="transform"/>
                            </FRBRWork>
                            <FRBRExpression>
                                <FRBRdate date="2019-01-01" name="judgment"/>
                            </FRBRExpression>
                        </identification>
                        <proprietary><uk:year>2020</uk:year></proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2024, 1, 1)),
                source=MetadataSource.DOCUMENT,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.date.write_resolved_to_body()

        assert document.body.document_date_as_date is None
        transform_dates = document.body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate[@name='transform']/@date"
        )
        assert transform_dates == ["2025-07-29T12:47:42"]
        assert document.body.get_xpath_match_string(EXPRESSION_DATE_XPATH) == "2019-01-01"
        assert (
            document.body.get_xpath_match_string("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:year/text()")
            == "2020"
        )

    def test_unparsable_body_date_without_claims_raises_on_write_back(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="kitten" name="judgment"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        with pytest.raises(UnparsableDecisionDateError, match="kitten"):
            document.metadata.date.write_resolved_to_body()

        assert document.body.decision_date_raw == "kitten"

    def test_save_with_unparsable_body_date_and_no_claims_raises(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="kitten" name="judgment"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            pytest.raises(UnparsableDecisionDateError, match="kitten"),
        ):
            document.save(message="Should not rewrite unparsable date")

        mock_api_client.update_document_xml.assert_not_called()

    def test_editor_date_claim_can_fix_unparsable_body_date_on_save(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                                <FRBRdate date="kitten" name="judgment"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2024, 3, 1)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        with patch.object(document.api_client, "document_exists", return_value=True):
            document.save(message="Replace unparsable date")

        assert document.body.get_xpath_match_string(WORK_FRBRDATE_XPATH) == "2024-03-01"

    def test_no_date_claims_and_absent_work_date_is_no_op(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="Name"/>
                            </FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        document.metadata.date.write_resolved_to_body()

        assert document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate") == []


class TestWriteResolvedCourtToBody:
    def test_write_resolved_court_updates_proprietary(self, mock_api_client):
        body = DocumentBodyFactory.build(court="Original Court")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("EWHC"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.court.write_resolved_to_body()

        assert document.body.court == "EWHC"

    def test_suppressed_court_removes_uk_court_nodes(self, mock_api_client):
        body = DocumentBodyFactory.build(court="Original Court")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("EWHC"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.court.write_resolved_to_body()

        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court") == []

    def test_whitespace_only_body_court_is_removed_on_write_back(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta><proprietary><uk:court>   </uk:court></proprietary></meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("EWHC"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.court.write_resolved_to_body()

        assert document.body.court == ""
        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court") == []


class TestWriteResolvedJurisdictionToBody:
    def test_write_resolved_jurisdiction_updates_proprietary(self, mock_api_client):
        body = DocumentBodyFactory.build(jurisdiction="EW")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value=MetadataStringValue("NI"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.jurisdiction.write_resolved_to_body()

        assert document.body.jurisdiction == "NI"

    def test_suppressed_jurisdiction_removes_uk_jurisdiction_nodes(self, mock_api_client):
        body = DocumentBodyFactory.build(jurisdiction="EW")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value=MetadataStringValue("NI"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.jurisdiction.write_resolved_to_body()

        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:jurisdiction") == []

    def test_whitespace_only_body_jurisdiction_is_removed_on_write_back(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta><proprietary><uk:jurisdiction>  </uk:jurisdiction></proprietary></meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="jurisdiction",
                value=MetadataStringValue("NI"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.jurisdiction.write_resolved_to_body()

        assert document.body.jurisdiction == ""
        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:jurisdiction") == []


class TestWriteResolvedCategoriesToBody:
    def test_write_resolved_categories_replaces_proprietary_nodes(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody
        from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue
        from caselawclient.types import DocumentCategory

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:category>Old</uk:category>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="categories",
                value=MetadataCategoryValue(name="Human rights", parent=None),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.categories.write_resolved_to_body()

        assert document.body.categories == [DocumentCategory(name="Human rights")]

    def test_write_resolved_categories_writes_nested_category_tree(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody
        from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue
        from caselawclient.types import DocumentCategory

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta><proprietary/></meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="categories",
                value=MetadataCategoryValue(name="Appeals", parent=None),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )
        document.metadata_fields.add(
            MetadataField(
                name="categories",
                value=MetadataCategoryValue(name="Registration variation", parent="Appeals"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.categories.write_resolved_to_body()

        assert document.body.categories == [
            DocumentCategory(
                name="Appeals",
                subcategories=[DocumentCategory(name="Registration variation")],
            )
        ]
        category_nodes = document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category")
        assert len(category_nodes) == 2
        parent_nodes = [node for node in category_nodes if node.get("parent") is None]
        child_nodes = [node for node in category_nodes if node.get("parent") == "Appeals"]
        assert [node.text for node in parent_nodes] == ["Appeals"]
        assert [node.text for node in child_nodes] == ["Registration variation"]

    def test_suppressed_category_claims_remove_uk_category_nodes(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody
        from caselawclient.models.documents.metadata.fields.field import MetadataCategoryValue

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <proprietary>
                            <uk:category>Old</uk:category>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="categories",
                value=MetadataCategoryValue(name="Human rights", parent=None),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        document.metadata.categories.write_resolved_to_body()

        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:category") == []


class TestSaveDoesNotWritePartiesToBody:
    def test_save_leaves_uk_party_nodes_unchanged(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork><FRBRname value="Title"/></FRBRWork>
                        </identification>
                        <proprietary>
                            <uk:party role="Claimant">Jerry</uk:party>
                        </proprietary>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        party_nodes_before = document.body.get_xpath_nodes(PARTIES_XPATH)
        document.metadata_fields.add(
            MetadataField(
                name="parties",
                value=MetadataPartyValue(name="Tom", role="Defendant"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        with patch.object(document.api_client, "document_exists", return_value=True):
            document.save(message="Save with party claim")

        party_nodes_after = document.body.get_xpath_nodes(PARTIES_XPATH)
        assert len(party_nodes_before) == 1
        assert party_nodes_before[0].text == "Jerry"
        assert party_nodes_before[0].get("role") == "Claimant"
        assert len(party_nodes_after) == 1
        assert party_nodes_after[0].text == "Jerry"
        assert party_nodes_after[0].get("role") == "Claimant"


class TestMetadataWriteBackSupport:
    def test_content_as_xml_updates_after_title_write_back(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        _ = document.body.content_as_xml
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("Updated title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.title.write_resolved_to_body()

        assert "Updated title" in document.body.content_as_xml
        assert "Original title" not in document.body.content_as_xml

    def test_press_summary_shape_does_not_support_metadata_write_back(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn"
                xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <doc name="pressSummary">
                    <preface><p><docTitle><span>Press Summary</span></docTitle></p></preface>
                </doc>
            </akomaNtoso>
            """
        )
        assert body.supports_metadata_write_back is False

    def test_write_court_creates_proprietary_when_missing(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork><FRBRname value="Title"/></FRBRWork>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("EWHC"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.court.write_resolved_to_body()

        assert document.body.court == "EWHC"

    def test_write_court_inserts_proprietary_before_presentation(self, mock_api_client):
        from lxml import etree

        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:html="http://www.w3.org/1999/xhtml"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork><FRBRname value="Title"/></FRBRWork>
                        </identification>
                        <presentation source="#"><html:style/></presentation>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="court",
                value=MetadataStringValue("EWHC"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.court.write_resolved_to_body()

        meta = document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta")[0]
        akn_ns = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        child_local_names = [
            name for child in meta if (name := etree.QName(child).localname) and etree.QName(child).namespace == akn_ns
        ]
        assert child_local_names.index("proprietary") < child_local_names.index("presentation")
