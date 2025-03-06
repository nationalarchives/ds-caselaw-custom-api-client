from pytest import raises

from caselawclient import client_helpers
from caselawclient.models.documents import Document
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary


class TestGetDocumentTypeClass:
    def test_ingested_document_type_judgment(self):
        """Check that documents with a main tag of `<judgment>` are detected as `Judgment`s."""
        assert (
            client_helpers.get_document_type_class(
                b'<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><judgment /></akomaNtoso>'
            )
            == Judgment
        )

    def test_ingested_document_type_press_summary(self):
        """Check that documents with a main tag of `<doc name="pressSummary">` are detected as `PressSummary`s."""
        assert (
            client_helpers.get_document_type_class(
                b'<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><doc name="pressSummary" /></akomaNtoso>'
            )
            == PressSummary
        )

    def test_ingested_document_error(self):
        """Check that parser logs with root tags of `<error>` are detected as plain `Document`s."""
        client_helpers.get_document_type_class(b"<error/>") == Document

    def test_ingested_document_type_doc_without_press_summary_name(self):
        """ "Check that documents with a main tag of `<doc>` but no `name="pressSummary"` raise an exception."""
        with raises(client_helpers.CannotDetermineDocumentType):
            client_helpers.get_document_type_class(
                b'<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><doc /></akomaNtoso>'
            )

    def test_ingested_document_type_unknown(self):
        """Check that in the absence of typing information an exception is raised."""
        with raises(client_helpers.CannotDetermineDocumentType):
            client_helpers.get_document_type_class(b"<xml />")
