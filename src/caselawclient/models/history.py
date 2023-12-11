from typing import Union

import lxml.etree


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
