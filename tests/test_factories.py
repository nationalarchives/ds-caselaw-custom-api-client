from caselawclient.factories import DocumentFactory, JudgmentFactory


def test_content_as_html():
    doc = DocumentFactory.build()
    assert doc.content_as_html() == "<p>This is a judgment.</p>"


def test_ncn():
    doc = JudgmentFactory.build(neutral_citation="not the default")
    breakpoint()
    assert doc.neutral_citation == "not the default"
