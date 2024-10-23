import pytest

from caselawclient.factories import DocumentFactory, JudgmentFactory, PressSummaryFactory, SearchResultFactory


def test_content_as_html():
    doc = DocumentFactory.build()
    assert doc.content_as_html() == "<p>This is a judgment.</p>"


class TestSearchStatusBehaviour:
    def test_status(self):
        search = SearchResultFactory.build()
        assert search.metadata.editor_status == "New"


class TestDocumentNCNBehaviour:
    def test_ncn_judgment(self):
        doc = JudgmentFactory.build(neutral_citation="not the default")
        assert doc.neutral_citation == "not the default"

    def test_ncn_press(self):
        doc = PressSummaryFactory.build(neutral_citation="not the default")
        assert doc.neutral_citation == "not the default"

    def test_ncn_doc(self):
        doc = DocumentFactory.build(neutral_citation="not the default")
        with pytest.raises(AttributeError):
            doc.neutral_citation
