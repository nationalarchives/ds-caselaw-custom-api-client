from datetime import UTC, date, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from caselawclient.factories import JudgmentFactory, PressSummaryFactory
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.body_metadata import BodyMetadataWriteBack, writable_akn_document_root_xpath
from caselawclient.models.documents.body_metadata import frbr_identification_writer as frbr_writer_module
from caselawclient.models.documents.body_metadata.akn import FRBR_WORK_CHILDREN_ORDER, FRBR_WORK_XPATH
from caselawclient.models.documents.body_metadata.frbr_identification_writer import (
    FrbrIdentificationWriter,
    _apply_resolved_metadata_to_identification,
    _ensure_frbr_child,
    _upsert_work_decision_frbrdate,
)
from caselawclient.models.documents.metadata.fields.field import MetadataDateValue, MetadataField, MetadataStringValue
from caselawclient.models.documents.metadata.fields.source import MetadataSource
from tests.models.documents.body_metadata.fixtures import (
    WORK_DECISION_FRBRDATE_XPATH,
    add_editor_date,
    add_editor_title,
    doc_minimal_body,
    doc_with_identification,
    judgment_body_with_custom_work,
    judgment_body_with_valid_identification,
    valid_frbr_triple_inner,
)


class TestWritableAknDocumentRoot:
    def test_ambiguous_root_is_not_writable(self):
        body = DocumentBody(
            b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
            <judgment name="judgment"><meta/></judgment>
            <doc name="pressSummary"><mainBody/></doc>
            </akomaNtoso>"""
        )
        assert writable_akn_document_root_xpath(body._xml) is None  # noqa: SLF001
        assert body.supports_metadata_write_back is False

    @pytest.mark.parametrize(
        "body",
        [
            DocumentBody(
                b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <judgment name="judgment"><meta/></judgment></akomaNtoso>"""
            ),
            DocumentBody(
                b"""<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
                <doc name="pressSummary"><mainBody/></doc></akomaNtoso>"""
            ),
        ],
    )
    def test_judgment_and_doc_without_frbrwork_are_not_writable(self, body):
        assert writable_akn_document_root_xpath(body._xml) is not None  # noqa: SLF001
        assert body.supports_metadata_write_back is False

    def test_parser_error_is_not_writable(self):
        body = DocumentBody(b"<error>failed</error>")
        assert body.supports_metadata_write_back is False

    def test_sync_noops_when_body_is_not_writable(self, mock_api_client):
        body = DocumentBody(b"<error>failed</error>")
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)

        assert BodyMetadataWriteBack().sync(document) is False


class TestFrbrIdentificationWriter:
    def test_write_returns_false_when_body_is_not_writable(self, mock_api_client):
        document = PressSummaryFactory.build(
            api_client=mock_api_client,
            body=DocumentBody(b"<error>failed</error>"),
        )

        assert FrbrIdentificationWriter().write(document) is False

    def test_write_noops_without_title_claims(self, mock_api_client):
        work_only = """
                    <FRBRWork>
                      <FRBRname value="Existing"/>
                    </FRBRWork>
        """
        body = DocumentBody(doc_with_identification(triple_inner=work_only))
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        original_xml = body.content_as_xml

        assert FrbrIdentificationWriter().write(document) is False
        assert body.content_as_xml == original_xml

    def test_write_noops_when_identification_has_no_frbrwork(self, mock_api_client):
        body = doc_minimal_body()
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Example title")

        assert FrbrIdentificationWriter().write(document) is False

    def test_write_updates_frbrname_without_touching_frbr_uris(self, mock_api_client):
        triple = valid_frbr_triple_inner()
        body = DocumentBody(
            doc_with_identification(
                triple_inner=triple.replace(
                    '<FRBRcountry value="GB-UKM"/>',
                    '<FRBRcountry value="GB-UKM"/>\n                      <FRBRname value="Before"/>',
                    1,
                )
            )
        )
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "After")

        assert FrbrIdentificationWriter().write(document) is True
        assert (
            body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
            )
            == "After"
        )
        assert (
            body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRthis/@value"
            )
            == "https://example/id/work"
        )
        assert body.get_xpath_nodes("/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRExpression")

    def test_does_not_commit_when_trial_identification_stays_invalid(self, mock_api_client):
        body = DocumentBody(
            doc_with_identification(
                triple_inner=valid_frbr_triple_inner(),
                extra_identification_siblings='    <lifecycle source="#tna"/>\n',
            )
        )
        original_frbrname = body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
        )
        assert body.supports_metadata_write_back is False
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Editor title")

        assert FrbrIdentificationWriter().write(document) is False
        assert (
            body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
            )
            == original_frbrname
        )

    def test_does_not_commit_when_identification_validator_rejects_trial(self, mock_api_client, caplog):
        from tests.models.documents.body_metadata.fixtures import judgment_body_with_valid_identification

        body = judgment_body_with_valid_identification(title="Before")
        original_xml = body.content_as_xml
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Example title")

        def reject_identification(_identification):
            return "trial identification rejected"

        assert FrbrIdentificationWriter(identification_validator=reject_identification).write(document) is False
        assert body.content_as_xml == original_xml
        assert "trial identification rejected" in caplog.text

    def test_write_returns_false_when_trial_apply_raises_value_error(self, mock_api_client, caplog):
        body = judgment_body_with_valid_identification(title="Before")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "After")

        with patch.object(
            frbr_writer_module,
            "_apply_resolved_metadata_to_identification",
            side_effect=ValueError("trial apply failed"),
        ):
            assert FrbrIdentificationWriter().write(document) is False

        assert body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
        ) == "Before"
        assert "trial apply failed" in caplog.text

    def test_write_returns_false_when_live_apply_raises_value_error(self, mock_api_client, caplog):
        body = judgment_body_with_valid_identification(title="Before")
        original_xml = body.content_as_xml
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "After")

        with (
            patch.object(
                frbr_writer_module,
                "_apply_resolved_metadata_to_identification",
                side_effect=[None, ValueError("live apply failed")],
            ),
            patch.object(frbr_writer_module, "validate_frbr_identification_element", return_value=None),
        ):
            assert FrbrIdentificationWriter().write(document) is False

        assert body.content_as_xml == original_xml
        assert "live apply failed" in caplog.text

    def test_whitespace_only_title_claim_removes_frbrname(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Before")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Ignored")

        class WhitespaceTitleResolved:
            has_any_claims = True
            value = MetadataStringValue("   ")

        original_resolve = document.metadata_fields.resolve

        def resolve_with_whitespace_title(name: str):
            if name == "title":
                return WhitespaceTitleResolved()
            return original_resolve(name)

        with patch.object(document.metadata_fields, "resolve", side_effect=resolve_with_whitespace_title):
            assert FrbrIdentificationWriter().write(document) is True

        assert document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRname") == []

    def test_upsert_inserts_work_decision_frbrdate_when_none_exist(self, mock_api_client):
        body = judgment_body_with_valid_identification(title="Name")
        work = body.get_xpath_nodes(FRBR_WORK_XPATH)[0]
        for child in list(work):
            if child.tag.endswith("FRBRdate") and (child.get("name") or "") in {"judgment", "decision", ""}:
                work.remove(child)

        _upsert_work_decision_frbrdate(body._xml, "judgment", date(2024, 6, 15))  # noqa: SLF001

        assert body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2024-06-15"

    def test_apply_raises_when_identification_has_multiple_frbrwork(self, mock_api_client):
        triple = valid_frbr_triple_inner().replace(
            "</FRBRWork>",
            '</FRBRWork>\n                    <FRBRWork>\n                      <FRBRthis value="https://example/id/work-2"/>\n'
            "                    </FRBRWork>",
            1,
        )
        body = DocumentBody(doc_with_identification(triple_inner=triple))
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, date(2024, 6, 15))

        with pytest.raises(ValueError, match="exactly one FRBRWork"):
            _apply_resolved_metadata_to_identification(document, body._xml, False, True)  # noqa: SLF001

    def test_ensure_frbr_child_raises_for_unknown_local_name(self):
        body = judgment_body_with_valid_identification(title="Name")

        with pytest.raises(ValueError, match="not listed in child_order"):
            _ensure_frbr_child(body._xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, "bogus")  # noqa: SLF001

    def test_ensure_frbr_child_raises_for_duplicate_children(self):
        triple = valid_frbr_triple_inner().replace(
            '<FRBRcountry value="GB-UKM"/>',
            '<FRBRcountry value="GB-UKM"/>\n                      <FRBRname value="first"/>\n'
            '                      <FRBRname value="second"/>',
            1,
        )
        body = DocumentBody(doc_with_identification(triple_inner=triple))

        with pytest.raises(ValueError, match="Multiple FRBRname"):
            _ensure_frbr_child(body._xml, FRBR_WORK_XPATH, FRBR_WORK_CHILDREN_ORDER, "FRBRname")  # noqa: SLF001

    def test_date_write_uses_judgment_frbrdate_name_for_unrecognised_root_name(self, mock_api_client):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work, judgment_name="order")
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        add_editor_date(document, date(2024, 6, 15))

        FrbrIdentificationWriter().write(document)

        work_dates = document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate")
        decision_named = [element for element in work_dates if (element.get("name") or "") in {"judgment", "decision"}]
        assert len(decision_named) == 1
        assert decision_named[0].get("name") == "judgment"

    def test_suppressed_date_claim_removes_work_decision_frbrdates(self, mock_api_client):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)
        document.metadata_fields.add(
            MetadataField(
                name="date",
                value=MetadataDateValue(date(2024, 6, 15)),
                source=MetadataSource.EDITOR,
                id=str(uuid4()),
                timestamp=datetime(2025, 1, 1, tzinfo=UTC),
                rejected=True,
            )
        )

        assert FrbrIdentificationWriter().write(document) is False
        assert document.body.get_xpath_match_string(WORK_DECISION_FRBRDATE_XPATH) == "2020-01-01"


class TestDocumentBodyDecisionDateRaw:
    def test_decision_date_raw_uses_first_matching_frbrdate_when_duplicates_exist(self):
        work = """
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2020-01-01" name="judgment"/>
                      <FRBRdate date="2019-01-01" name="decision"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                      <FRBRname value="Name"/>
        """
        body = judgment_body_with_custom_work(work_inner=work, judgment_name="decision")

        assert body.decision_date_raw == "2020-01-01"
