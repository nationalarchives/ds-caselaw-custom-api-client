from typing import Dict, Optional, cast

from lxml import etree

DEFAULT_NAMESPACES = {
    "uk": "https://caselaw.nationalarchives.gov.uk/akn",
    "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
}

# _Element is the only class lxml exposes, so need to use the private class for typing
Element = etree._Element  # noqa: SLF001


def get_xpath_nodes(
    node: Element,
    path: str,
    namespaces: Optional[Dict[str, str]] = None,
) -> list[Element]:
    return cast(list[Element], node.xpath(path, namespaces=namespaces))


def get_xpath_match_string(
    node: Element,
    path: str,
    namespaces: Optional[Dict[str, str]] = None,
    fallback: str = "",
) -> str:
    return str((node.xpath(path, namespaces=namespaces) or [fallback])[0])


def get_xpath_match_strings(
    node: Element,
    path: str,
    namespaces: Optional[Dict[str, str]] = None,
) -> list[str]:
    return [str(x) for x in node.xpath(path, namespaces=namespaces)]
