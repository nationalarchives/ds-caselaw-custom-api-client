import pytest

from caselawclient.factories import (
    DocumentBodyFactory,
    DocumentFactory,
    JudgmentFactory,
    PressSummaryFactory,
    SearchResultFactory,
    build_document_body_xml,
)


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
            _ = doc.neutral_citation


class TestDocumentBodyXmlEscaping:
    def test_build_document_body_xml_escapes_special_characters_in_attributes_and_text(self):
        xml = build_document_body_xml(
            name='R v G & B <"quoted">',
            court="Court of Testing & Appeals",
            jurisdiction='A & B <"jurisdiction">',
            case_number="ABC & 123",
        )

        assert 'value="R v G &amp; B &lt;&quot;quoted&quot;&gt;"' in xml
        assert "<uk:court>Court of Testing &amp; Appeals</uk:court>" in xml
        assert '<uk:jurisdiction>A &amp; B &lt;"jurisdiction"&gt;</uk:jurisdiction>' in xml
        assert "<uk:caseNumber>ABC &amp; 123</uk:caseNumber>" in xml

    def test_document_body_factory_accepts_ampersand_in_name(self):
        body = DocumentBodyFactory.build(name="R v G & B")

        assert body.name == "R v G & B"

    def test_judgment_factory_accepts_ampersand_in_body_name(self, mock_api_client):
        judgment = JudgmentFactory.build(
            api_client=mock_api_client,
            body=DocumentBodyFactory.build(name="R v G & B"),
        )

        assert judgment.body.name == "R v G & B"
        assert judgment.metadata.title.value == "R v G & B"
