from typing import Dict, Optional

from lxml import etree


def get_xpath_match_string(
    node: etree._Element,
    path: str,
    namespaces: Optional[Dict[str, str]] = None,
    fallback: str = "",
) -> str:
    kwargs = {"namespaces": namespaces} if namespaces else {}
    return str((node.xpath(path, **kwargs) or [fallback])[0])
