"""Tests for writing resolved metadata claims into Akoma Ntoso body XML."""

import datetime
from datetime import UTC
from uuid import uuid4

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents.body import NAME_XPATH
from caselawclient.models.documents.metadata.fields.field import (
    MetadataDateValue,
    MetadataField,
    MetadataStringValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import DEFAULT_NAMESPACES


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

        document.save(message="Sync title to XML")

        xml_tree = mock_api_client.update_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Saved title"


class TestWriteResolvedDateToBody:
    def test_write_resolved_date_updates_work_and_expression_frbrdate(self, mock_api_client):
        body = DocumentBodyFactory.build(document_date_as_string="2020-01-01")
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

        assert document.body.document_date_as_date == resolved
        expression_date = document.body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression/akn:FRBRdate/@date"
        )
        assert expression_date == "2024-06-15"
        assert (
            document.body.get_xpath_match_string("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:year/text()")
            == "2024"
        )

    def test_suppressed_date_claim_clears_frbr_dates_in_body(self, mock_api_client):
        body = DocumentBodyFactory.build(document_date_as_string="2020-01-01")
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
        assert (
            document.body.get_xpath_match_string("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:year/text()") == ""
        )


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


class TestWriteResolvedCaseNumberToBody:
    def test_write_resolved_case_number_replaces_nodes(self, mock_api_client):
        body = DocumentBodyFactory.build(case_number="OLD/123")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="case_number",
                value=MetadataStringValue("NEW/456"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.case_number.write_resolved_to_body()

        assert document.body.case_number == "NEW/456"

    def test_no_case_number_metadata_leaves_body_without_uk_case_number(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

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

        document.metadata.case_number.write_resolved_to_body()

        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:caseNumber") == []


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
