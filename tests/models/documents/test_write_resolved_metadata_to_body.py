"""Tests for writing resolved metadata claims into Akoma Ntoso body XML."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory, PressSummaryFactory
from caselawclient.models.documents.body import FRBR_WORK_XPATH, NAME_XPATH, DocumentBody
from caselawclient.models.documents.body_metadata import BodyMetadataWriteBack
from caselawclient.models.documents.metadata.fields.field import (
    MetadataDateValue,
    MetadataField,
    MetadataStringValue,
)
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from caselawclient.xml_helpers import DEFAULT_NAMESPACES
from tests.models.documents.body_metadata.fixtures import (
    FRBRWORK_NAME_VALUE_XPATH,
    IDENTIFICATION_XPATH,
    add_editor_title,
    akn_child_local_names,
    doc_press_summary_body,
    judgment_with_identification,
)


def _sync_resolved_metadata_to_body(document) -> None:
    assert BodyMetadataWriteBack().sync(document)


def _assert_write_back_noops(document) -> None:
    assert BodyMetadataWriteBack().sync(document) is False


class TestWriteResolvedTitleToBody:
    def test_write_resolved_title_updates_frbrname(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Resolved title")

        _sync_resolved_metadata_to_body(document)

        assert document.body.name == "Resolved title"
        assert document.body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH) == "Resolved title"

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

        _sync_resolved_metadata_to_body(document)

        assert (
            document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname")
            == []
        )

    @pytest.mark.parametrize("body_name", ["Body-only title", "   "])
    def test_body_title_is_not_written_back_without_title_claims(self, mock_api_client, body_name):
        body = DocumentBodyFactory.build(name=body_name)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        original_frbrname = body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH)

        _sync_resolved_metadata_to_body(document)

        assert body.get_xpath_match_string(FRBRWORK_NAME_VALUE_XPATH) == original_frbrname
        if body_name.strip():
            assert document.body.name == body_name.strip()
        else:
            assert document.body.name == ""

    def test_date_claims_do_not_change_frbrdate_in_pr1(self, mock_api_client):
        triple_with_title = """
                    <FRBRWork>
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-05-10" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Original title"/>
                    </FRBRWork>
                    <FRBRExpression>
                      <FRBRthis value="https://example/expression"/>
                      <FRBRuri value="https://example/expression"/>
                      <FRBRdate date="2020-05-10" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRlanguage language="eng"/>
                    </FRBRExpression>
                    <FRBRManifestation>
                      <FRBRthis value="https://example/data.xml"/>
                      <FRBRuri value="https://example/data.xml"/>
                      <FRBRdate date="2020-05-10" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRformat value="application/xml"/>
                    </FRBRManifestation>
        """
        body = DocumentBody(judgment_with_identification(triple_inner=triple_with_title))
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        decision_date_xpath = (
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate[@name='judgment']/@date"
        )
        original_work_date = body.get_xpath_match_string(decision_date_xpath)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(datetime.date(2025, 6, 15)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        _sync_resolved_metadata_to_body(document)

        assert body.get_xpath_match_string(decision_date_xpath) == original_work_date

    def test_save_writes_resolved_title_into_xml(self, mock_api_client):
        body = DocumentBodyFactory.build(name="Original title")
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

        body = DocumentBodyFactory.build(name="Original title")
        with patch.object(mock_api_client, "document_exists", return_value=False):
            document = Judgment.from_xml(body, mock_api_client, uri=DocumentURIString("test/new-doc"))
            add_editor_title(document, "Inserted title")
            document.save(message="Insert with title sync")

        xml_tree = mock_api_client.insert_document_xml.call_args[0][1]
        title_value = xml_tree.xpath(NAME_XPATH, namespaces=DEFAULT_NAMESPACES)[0]
        assert title_value == "Inserted title"


class TestSaveMaterialisesBeforeWriteBack:
    def test_save_materialises_body_claims_before_writing_resolved_metadata_to_body(self, mock_api_client):
        """On save(), body-claim materialisation runs before write-back (patched hooks record call order)."""
        body = DocumentBodyFactory.build(name="Body title")
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
        body = DocumentBodyFactory.build(name="Original title")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        _ = document.body.content_as_xml
        add_editor_title(document, "Updated title")

        _sync_resolved_metadata_to_body(document)

        assert "Updated title" in document.body.content_as_xml
        assert "Original title" not in document.body.content_as_xml

    def test_press_summary_body_supports_metadata_write_back(self):
        assert doc_press_summary_body().supports_metadata_write_back is True

    def test_press_summary_title_write_back_scaffolds_identification(self, mock_api_client):
        document = PressSummaryFactory.build(api_client=mock_api_client, body=doc_press_summary_body())
        add_editor_title(document, "Resolved press summary title")

        _sync_resolved_metadata_to_body(document)

        assert document.body.name == "Resolved press summary title"
        assert document.body.get_xpath_nodes(FRBR_WORK_XPATH)
        assert document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRExpression")

    def test_write_title_creates_frbrwork_when_identification_has_only_manifestation(self, mock_api_client):
        triple = """
                    <FRBRManifestation>
                      <FRBRthis value=""/>
                    </FRBRManifestation>
        """
        body = DocumentBody(judgment_with_identification(triple_inner=triple, source=None))
        assert body.supports_metadata_write_back is True
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "New title")

        _sync_resolved_metadata_to_body(document)

        assert document.body.name == "New title"
        assert len(document.body.get_xpath_nodes(FRBR_WORK_XPATH)) == 1
        identification = document.body.get_xpath_nodes(IDENTIFICATION_XPATH)[0]
        child_names = akn_child_local_names(identification)
        assert child_names.index("FRBRWork") < child_names.index("FRBRManifestation")

    def test_write_title_inserts_frbrname_in_schema_order(self, mock_api_client):
        triple = """
                    <FRBRWork>
                      <FRBRauthor href="#court"/>
                    </FRBRWork>
        """
        body = DocumentBody(judgment_with_identification(triple_inner=triple, source=None))
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Ordered title")

        _sync_resolved_metadata_to_body(document)

        work = document.body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        child_names = akn_child_local_names(work)
        assert child_names.index("FRBRauthor") < child_names.index("FRBRname")
        assert document.body.name == "Ordered title"

    def test_write_title_noops_when_multiple_frbrname_elements(self, mock_api_client, caplog):
        triple = """
                    <FRBRWork>
                      <FRBRname value="first"/>
                      <FRBRname value="second"/>
                    </FRBRWork>
        """
        body = DocumentBody(judgment_with_identification(triple_inner=triple, source=None))
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "New title")
        original_xml = body.content_as_xml

        _assert_write_back_noops(document)
        assert body.content_as_xml == original_xml
        assert "Multiple FRBRname elements" in caplog.text
