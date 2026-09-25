import pytest

from caselawclient.factories import PressSummaryFactory
from caselawclient.models.documents.body import DocumentBody
from caselawclient.models.documents.body_metadata import BodyMetadataWriteBack, writable_akn_document_root_xpath
from caselawclient.models.documents.body_metadata.frbr_identification_writer import FrbrIdentificationWriter
from tests.models.documents.body_metadata.fixtures import (
    add_editor_title,
    doc_minimal_body,
    doc_with_identification,
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

    def test_does_not_commit_when_trial_identification_stays_invalid(self, mock_api_client, caplog):
        body = DocumentBody(
            doc_with_identification(
                triple_inner=valid_frbr_triple_inner(),
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
        work_only = """
                    <FRBRWork>
                      <FRBRname value="Before"/>
                    </FRBRWork>
        """
        body = DocumentBody(doc_with_identification(triple_inner=work_only))
        original_xml = body.content_as_xml
        document = PressSummaryFactory.build(api_client=mock_api_client, body=body)
        add_editor_title(document, "Example title")

        def reject_identification(_identification):
            return "trial identification rejected"

        assert FrbrIdentificationWriter(identification_validator=reject_identification).write(document) is False
        assert body.content_as_xml == original_xml
        assert "trial identification rejected" in caplog.text
