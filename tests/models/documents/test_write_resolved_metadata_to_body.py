"""Tests for writing resolved metadata claims into Akoma Ntoso body XML."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents.body import FRBR_WORK_XPATH, NAME_XPATH, DocumentBody
from caselawclient.models.documents.body_metadata import BodyMetadataWriteBack
from caselawclient.models.documents.exceptions import UnparsableDecisionDateError
from caselawclient.models.documents.metadata.fields.field import (
    MetadataDateValue,
    MetadataField,
    MetadataStringValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import DEFAULT_NAMESPACES
from tests.models.documents.body_metadata.fixtures import (
    EXPRESSION_DECISION_FRBRDATE_XPATH,
    FRBRWORK_NAME_VALUE_XPATH,
    WORK_DECISION_FRBRDATE_XPATH,
    add_editor_date,
    add_editor_title,
    akn_child_local_names,
    doc_press_summary_body,
    judgment_body_with_custom_work,
    judgment_body_with_valid_identification,
    judgment_with_identification,
    valid_frbr_triple_inner,
)


def _sync_resolved_metadata_to_body(document) -> None:
    assert BodyMetadataWriteBack().sync(document)


def _assert_write_back_noops(document) -> None:
    assert BodyMetadataWriteBack().sync(document) is False


def _body_with_unparsable_work_decision_date() -> DocumentBody:
    work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="not-a-date" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
    return judgment_body_with_custom_work(work_inner=work)


class TestWriteResolvedTitleToBody:
    def test_write_resolved_title_updates_frbrname(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Resolved title")

        _sync_resolved_metadata_to_body(document)

        assert document.body.name == "Resolved title"
        assert document.body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH) == "Resolved title"

    def test_title_write_back_leaves_frbr_identity_unchanged(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Original title")
        work = body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        child_order_before = akn_child_local_names(work)
        frbr_this_values = body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRthis/@value"
        )
        frbr_uri_values = body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRuri/@value"
        )
        date_values = body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRdate/@date"
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Resolved title")

        _sync_resolved_metadata_to_body(document)

        work_after = document.body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        assert akn_child_local_names(work_after) == child_order_before
        assert (
            document.body.get_xpath_match_strings(
                "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRthis/@value"
            )
            == frbr_this_values
        )
        assert (
            document.body.get_xpath_match_strings(
                "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRuri/@value"
            )
            == frbr_uri_values
        )
        assert (
            document.body.get_xpath_match_strings(
                "/akn:akomaNtoso/akn:*/akn:meta/akn:identification//akn:FRBRdate/@date"
            )
            == date_values
        )

    def test_suppressed_title_removes_frbrname(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Original title")
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

        _sync_resolved_metadata_to_body(document)

        assert (
            document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname")
            == []
        )

    def test_body_title_is_not_written_back_without_title_claims(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Body-only title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        original_frbrname = body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH)

        assert BodyMetadataWriteBack().sync(document) is False
        assert body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH) == original_frbrname
        assert document.body.name == "Body-only title"

    def test_whitespace_only_body_title_removes_frbrname_without_claims(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="   ")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        assert BodyMetadataWriteBack().sync(document) is True
        assert (
            document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname")
            == []
        )
        assert document.body.name == ""

    def test_save_writes_resolved_title_into_xml(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Saved title")

        with patch.object(document.api_client, "document_exists", return_value=True):
            document.save(message="Sync title to XML")

        xml_tree = mock_api_client.update_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Saved title"

    def test_save_on_insert_writes_resolved_title_into_xml(self, mock_api_client):
        from caselawclient.models.judgments import Judgment
        from caselawclient.types import DocumentURIString

        body = judgment_body_with_valid_identification(title="Original title")
        with patch.object(mock_api_client, "document_exists", return_value=False):
            document = Judgment.from_xml(body, mock_api_client, uri=DocumentURIString("test/new-doc"))
            add_editor_title(document, "Inserted title")
            document.save(message="Insert with title sync")

        xml_tree = mock_api_client.insert_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Inserted title"


class TestWriteResolvedDateToBody:
    def test_write_resolved_date_updates_work_frbrdate_only(self, mock_api_client):
        expression = """
                    <FRBRExpression>
                      <FRBRthis value="https://example/expression"/>
                      <FRBRuri value="https://example/expression"/>
                      <FRBRdate date="2019-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRlanguage language="eng"/>
                    </FRBRExpression>
                    <FRBRManifestation>
                      <FRBRthis value="https://example/data.xml"/>
                      <FRBRuri value="https://example/data.xml"/>
                      <FRBRdate date="2023-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRformat value="application/xml"/>
                    </FRBRManifestation>
        """
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work, expression_manifestation_inner=expression)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, datetime.date(2024, 6, 15))

        _sync_resolved_metadata_to_body(document)

        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2024-06-15"
        assert document.body.get_xpath_match_string(EXPRESSION_DECISION_FRBRDATE_XPATH) == "2019-01-01"

    def test_write_resolved_date_reuses_judgment_named_frbrdate_when_root_is_decision(self, mock_api_client):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work, judgment_name="decision")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, datetime.date(2024, 6, 15))

        _sync_resolved_metadata_to_body(document)

        work_dates = document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate")
        assert len(work_dates) == 1
        assert work_dates[0].get("name") == "decision"
        assert work_dates[0].get("date") == "2024-06-15"

    def test_write_decision_date_updates_judgment_without_reusing_transform(self, mock_api_client):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2025-07-29T12:47:42" name="transform"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, datetime.date(2024, 6, 15))

        _sync_resolved_metadata_to_body(document)

        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2024-06-15"
        transform_dates = document.body.get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate[@name='transform']/@date"
        )
        assert transform_dates == ["2025-07-29T12:47:42"]
        assert len(document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate")) == 2

    def test_legacy_unnamed_work_frbrdate_is_updated_in_place(self, mock_api_client):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01"/>
                      <FRBRdate date="2025-07-29" name="transform"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, datetime.date(2024, 6, 15))

        _sync_resolved_metadata_to_body(document)

        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2024-06-15"
        assert len(document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate")) == 2

    def test_suppressed_date_claim_does_not_commit_when_block_becomes_invalid(self, mock_api_client):
        body = DocumentBodyFactory.build(document_date_as_string="2020-01-01")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        original_date = document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2024, 6, 15)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        _assert_write_back_noops(document)

        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == original_date

    def test_unparsable_body_date_without_claims_does_not_block_write_back_sync(self, mock_api_client):
        body = _body_with_unparsable_work_decision_date()
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        _assert_write_back_noops(document)

    def test_save_raises_when_body_decision_date_is_unparsable_and_unclaimed(self, mock_api_client):
        body = _body_with_unparsable_work_decision_date()
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        with (
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml") as update_document_xml,
            pytest.raises(UnparsableDecisionDateError, match="not a valid ISO date"),
        ):
            document.save(message="Should not persist")

        update_document_xml.assert_not_called()

    def test_editor_date_claim_can_fix_unparsable_body_date_on_save(self, mock_api_client):
        body = _body_with_unparsable_work_decision_date()
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, datetime.date(2024, 6, 15))

        _sync_resolved_metadata_to_body(document)

        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2024-06-15"


class TestSaveMaterialisesBeforeWriteBack:
    def test_save_materialises_body_claims_before_writing_resolved_metadata_to_body(self, mock_api_client):
        """On save(), body-claim materialisation runs before write-back (patched hooks record call order)."""
        body = judgment_body_with_valid_identification(title="Body title")
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

        document.metadata.title.materialise_body_claims()
        add_editor_title(document, "Editor title")

        with (
            patch.object(document, "_convert_body_claims_to_structured_metadata", side_effect=track_materialise),
            patch.object(document, "_write_resolved_metadata_to_body", side_effect=track_write_back),
            patch.object(document.api_client, "document_exists", return_value=True),
            patch.object(document.api_client, "update_document_xml"),
        ):
            document.save(message="Ordered save")

        assert call_order == ["materialise", "write_back"]
        document_claims = document.metadata_fields.by_name("title")
        assert any(
            claim.source is MetadataSource.DOCUMENT and claim.value == MetadataStringValue("Body title")
            for claim in document_claims
        )
        assert document.body.name == "Editor title"


class TestMetadataWriteBackSupport:
    def test_content_as_xml_updates_after_title_write_back(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        _ = document.body.content_as_xml
        add_editor_title(document, "Updated title")

        _sync_resolved_metadata_to_body(document)

        assert "Updated title" in document.body.content_as_xml
        assert "Original title" not in document.body.content_as_xml

    def test_press_summary_without_frbrwork_does_not_support_write_back(self):
        assert doc_press_summary_body().supports_metadata_write_back is False

    def test_work_only_press_summary_identification_does_not_support_write_back(self):
        from pathlib import Path

        from caselawclient.models.documents.body import DocumentBody

        harness_fixture = Path(__file__).resolve().parents[3] / "marklogic_harness/fixtures/documents/press_summary.xml"
        body = DocumentBody(harness_fixture.read_bytes())
        assert body.supports_metadata_write_back is False

    def test_title_write_back_noops_when_identification_has_only_manifestation(self, mock_api_client):
        triple = """
                    <FRBRManifestation>
                      <FRBRthis value=""/>
                    </FRBRManifestation>
        """
        body = DocumentBody(judgment_with_identification(triple_inner=triple, source=None))
        assert body.supports_metadata_write_back is False
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "New title")
        original_xml = body.content_as_xml

        _assert_write_back_noops(document)
        assert body.content_as_xml == original_xml

    def test_write_title_inserts_frbrname_in_schema_order(self, mock_api_client):
        body = DocumentBody(
            judgment_with_identification(
                triple_inner="""
                    <FRBRWork>
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2023-01-01" name="judgment"/>
                      <FRBRauthor href="#court"/>
                      <FRBRcountry value="GB-UKM"/>
                    </FRBRWork>
                    <FRBRExpression>
                      <FRBRthis value="https://example/expression"/>
                      <FRBRuri value="https://example/expression"/>
                      <FRBRdate date="2023-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRlanguage language="eng"/>
                    </FRBRExpression>
                    <FRBRManifestation>
                      <FRBRthis value="https://example/data.xml"/>
                      <FRBRuri value="https://example/data.xml"/>
                      <FRBRdate date="2023-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRformat value="application/xml"/>
                    </FRBRManifestation>
        """
            )
        )
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Ordered title")

        _sync_resolved_metadata_to_body(document)

        work = document.body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        child_names = akn_child_local_names(work)
        assert child_names.index("FRBRauthor") < child_names.index("FRBRname")
        assert document.body.name == "Ordered title"

    def test_write_title_noops_when_multiple_frbrname_elements(self, mock_api_client):
        triple = valid_frbr_triple_inner().replace(
            '<FRBRcountry value="GB-UKM"/>',
            '<FRBRcountry value="GB-UKM"/>\n                      <FRBRname value="first"/>\n'
            '                      <FRBRname value="second"/>',
            1,
        )
        body = DocumentBody(judgment_with_identification(triple_inner=triple))
        assert body.supports_metadata_write_back is False
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "New title")
        original_xml = body.content_as_xml

        _assert_write_back_noops(document)
        assert body.content_as_xml == original_xml
