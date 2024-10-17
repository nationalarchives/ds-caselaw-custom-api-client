from caselawclient.factories import DocumentFactory


def test_content_as_html():
    doc = DocumentFactory.build()
    assert doc.content_as_html() == "<p>This is a judgment.</p>"
