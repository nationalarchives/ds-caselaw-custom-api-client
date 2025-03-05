from pytest import raises

from caselawclient import client_helpers
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary


class TestGetDocumentTypeClass:
    def test_ingested_document_type_judgment(self):
        """Check that documents with a root tag of `<judgment>` are detected as `Judgment`s."""
        assert client_helpers.get_document_type_class(b"<judgment />") == Judgment

    def test_ingested_document_type_press_summary(self):
        """ "Check that documents with a root tag of `<doc name="pressSummary">` are detected as `PressSummary`s."""
        assert client_helpers.get_document_type_class(b'<doc name="pressSummary" />') == PressSummary

    def test_ingested_document_type_doc_without_press_summary_name(self):
        """ "Check that documents with a root tag of `<doc>` but no `name="pressSummary" raise an exception."""
        with raises(client_helpers.CannotDetermineDocumentType):
            client_helpers.get_document_type_class(b"<doc />")

    def test_ingested_document_type_unknown(self):
        """Check that in the absence of typing information an exception is raised."""
        with raises(client_helpers.CannotDetermineDocumentType):
            client_helpers.get_document_type_class(b"<xml />")
