import lxml.etree

from caselawclient.xml_helpers import get_xpath_match_string, get_xpath_match_strings


def test_xpath_single():
    node = lxml.etree.fromstring("<root><cat>1</cat><cat>2</cat></root>")
    path = "//cat/text()"
    assert get_xpath_match_string(node, path) == "1"


def test_xpath_multiple():
    node = lxml.etree.fromstring("<root><cat>1</cat><cat>2</cat></root>")
    path = "//cat/text()"
    assert get_xpath_match_strings(node, path) == ["1", "2"]
