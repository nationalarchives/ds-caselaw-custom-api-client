from typing import Union

import lxml.etree

namespaces = {"flag": "http://caselaw.nationalarchives.gov.uk/history/flags"}


class HistoryEvent:
    def __init__(
        self,
        attributes: dict[str, str],
        flags: list[str],
        payload: Union[bytes, str, lxml.etree._Element],
    ):
        self.attributes = attributes
        self.flags = flags
        if isinstance(payload, lxml.etree._Element):
            self.payload = lxml.etree.tostring(payload)
        else:
            self.payload = payload

    @classmethod
    def from_xml(cls, element: lxml.etree._Element) -> "HistoryEvent":
        flags = [a for a in element.attrib.keys() if element.attrib[a] == "true"]
        flags = element.attrib.keys()
        return cls(element.attrib, flags, element)
