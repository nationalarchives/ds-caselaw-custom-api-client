import pytest

from caselawclient.factories import JudgmentFactory, PressSummaryFactory
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.body_metadata import BodyMetadataWriteBack, writable_akn_document_root_xpath
from caselawclient.models.documents.body_metadata.akn import FRBR_WORK_XPATH
from caselawclient.models.documents.body_metadata.frbr_identification_writer import FrbrIdentificationWriter
from tests.models.documents.body_metadata.fixtures import (
    add_editor_title,
    doc_minimal_body,
    doc_with_identification,
    judgment_minimal_body,
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
    def test_judgment_and_doc_are_writable(self, body):
        assert writable_akn_document_root_xpath(body._xml) is not None  # noqa: SLF001
        assert body.supports_metadata_write_back is True

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

    @pytest.mark.parametrize(
        ("judgment_name", "expected_frbr_date_name"),
        [("decision", "decision"), ("judgment", "judgment")],
    )
    def test_scaffolded_frbrdate_name_follows_judgment_root_name(
        self, mock_api_client, judgment_name, expected_frbr_date_name
    ):
        body = judgment_minimal_body(judgment_name=judgment_name)
        document = JudgmentFactory.build(api_client=mock_api_client, body=body)

        assert FrbrIdentificationWriter().write(document) is True
        assert document.body.get_xpath_match_string(
            f"{FRBR_WORK_XPATH}/akn:FRBRdate[@name='{expected_frbr_date_name}']/@date"
        )
        other_name = "judgment" if expected_frbr_date_name == "decision" else "decision"
        assert not document.body.get_xpath_nodes(f"{FRBR_WORK_XPATH}/akn:FRBRdate[@name='{other_name}']")

    def test_scaffold_ignores_unparseable_existing_frbrdate(self, mock_api_client):
        work_only = """
                    <FRBRWork>
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="not-a-date" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                    </FRBRWork>
        """
        body = DocumentBody(doc_with_identification(triple_inner=work_only))
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Title")

        assert FrbrIdentificationWriter().write(document) is True
        assert (
            document.body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRExpression"
                "/akn:FRBRdate[@name='judgment']/@date"
            )
            == "1001-01-01"
        )

    def test_creates_identification_triple_from_scratch(self, mock_api_client):
        body = doc_minimal_body()
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Example title")

        assert FrbrIdentificationWriter().write(document) is True
        assert (
            body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
            )
            == "Example title"
        )
        assert body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRthis/@value"
        ).endswith("/id/test/2023/123")

    def test_repairs_incomplete_identification_when_trial_block_is_valid(self, mock_api_client):
        incomplete = """
                    <FRBRWork>
                      <FRBRname value="Broken"/>
                    </FRBRWork>
        """
        body = DocumentBody(doc_with_identification(triple_inner=incomplete))
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)

        assert FrbrIdentificationWriter().write(document) is True
        assert body.get_xpath_nodes("/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRExpression")
        assert body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRthis/@value"
        )

    def test_does_not_commit_when_trial_identification_stays_invalid(self, mock_api_client, caplog):
        work_valid = """
                    <FRBRWork>
                      <FRBRthis value="https://example/id/work"/>
                      <FRBRuri value="https://example/id/work"/>
                      <FRBRdate date="2023-01-01" name="judgment"/>
                      <FRBRauthor href="#tna"/>
                      <FRBRcountry value="GB-UKM"/>
                    </FRBRWork>
        """
        body = DocumentBody(
            doc_with_identification(
                triple_inner=work_valid,
                extra_identification_siblings='    <lifecycle source="#tna"/>\n',
            )
        )
        original_frbrname = body.get_xpath_match_string(
            "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
        )
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Editor title")

        assert FrbrIdentificationWriter().write(document) is False
        assert (
            body.get_xpath_match_string(
                "/akn:akomaNtoso/akn:doc/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value"
            )
            == original_frbrname
        )
        assert "unexpected children" in caplog.text

    def test_does_not_commit_when_identification_validator_rejects_trial(self, mock_api_client, caplog):
        body = doc_minimal_body()
        original_xml = body.content_as_xml
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Example title")

        def reject_identification(_identification):
            return "trial identification rejected"

        assert FrbrIdentificationWriter(identification_validator=reject_identification).write(document) is False
        assert body.content_as_xml == original_xml
        assert "trial identification rejected" in caplog.text
