"""Tests for writing resolved metadata claims into Akoma Ntoso body XML."""

import datetime
from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest

from caselawclient.factories import DocumentBodyFactory, JudgmentFactory
from caselawclient.models.documents.body import FRBR_WORK_XPATH, NAME_XPATH
from caselawclient.models.documents.metadata.fields.field import (
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
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("Editor title"),
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

    def test_write_title_creates_frbrwork_when_identification_has_only_manifestation(self, mock_api_client):
        from lxml import etree

        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
                xmlns:uk="https://caselaw.nationalarchives.gov.uk/akn">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRManifestation>
                                <FRBRthis value=""/>
                            </FRBRManifestation>
                        </identification>
                    </meta>
                    <header><p/></header>
                    <judgmentBody><decision><p/></decision></judgmentBody>
                </judgment>
            </akomaNtoso>
            """
        )
        assert body.supports_metadata_write_back is True
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="title",
                value=MetadataStringValue("New title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.title.write_resolved_to_body()

        assert document.body.name == "New title"
        assert len(document.body.get_xpath_nodes(FRBR_WORK_XPATH)) == 1
        identification = document.body.get_xpath_nodes("/akn:akomaNtoso/akn:*/akn:meta/akn:identification")[0]
        akn_ns = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        child_names = [
            etree.QName(child).localname
            for child in identification
            if isinstance(child.tag, str) and etree.QName(child).namespace == akn_ns
        ]
        assert child_names.index("FRBRWork") < child_names.index("FRBRManifestation")

    def test_write_title_inserts_frbrname_in_schema_order(self, mock_api_client):
        from lxml import etree

        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRauthor href="#court"/>
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
                name="title",
                value=MetadataStringValue("Ordered title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        document.metadata.title.write_resolved_to_body()

        work = document.body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        akn_ns = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
        child_names = [
            etree.QName(child).localname
            for child in work
            if isinstance(child.tag, str) and etree.QName(child).namespace == akn_ns
        ]
        assert child_names.index("FRBRauthor") < child_names.index("FRBRname")
        assert document.body.name == "Ordered title"

    def test_write_title_raises_when_multiple_frbrname_elements(self, mock_api_client):
        from caselawclient.models.documents.body import DocumentBody

        body = DocumentBody(
            b"""
            <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment>
                    <meta>
                        <identification>
                            <FRBRWork>
                                <FRBRname value="first"/>
                                <FRBRname value="second"/>
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
                name="title",
                value=MetadataStringValue("New title"),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime.datetime(2025, 1, 1, tzinfo=UTC),
            )
        )

        with pytest.raises(ValueError, match="Multiple FRBRname elements under FRBRWork"):
            document.metadata.title.write_resolved_to_body()
