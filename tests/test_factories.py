import pytest

from caselawclient.factories import DocumentFactory, JudgmentFactory, PressSummaryFactory, SearchResultFactory


class TestSearchStatusBehaviour:
    def test_status(self):
        search = SearchResultFactory.build()
        assert search.metadata.editor_status == "New"  # type: ignore[attr-defined]


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
