from typing import Union

import lxml.etree

flag_ns_bare = "http://caselaw.nationalarchives.gov.uk/history/flags"
flag_ns_wrapped = f"{{{flag_ns_bare}}}"
namespaces = {"flag": flag_ns_bare}


class EventPayloadInvalid(RuntimeError):
    """The payload did not start with a <payload> tag."""

    pass


class HistoryEvent:
    def __repr__(self) -> str:
        return f"HistoryEvent({repr(self.attributes)}, {repr(self.flags)}, payload?)"

    def __init__(
        self,
        attributes: dict[str, str],
        flags: list[str],
        payload: Union[str, lxml.etree._Element],
    ):
        self.attributes = attributes
        self.flags = flags
        if isinstance(payload, lxml.etree._Element):
            self.payload = lxml.etree.tostring(payload).decode("utf-8")
        elif isinstance(payload, bytes):
            self.payload = payload.decode("utf-8")
        elif isinstance(payload, str):
            self.payload = payload

        print(self.payload)

        if not self.payload.startswith("<payload"):
            raise EventPayloadInvalid("Event payloads must start with a <payload> tag")

    @classmethod
    def from_xml(cls, element: lxml.etree._Element) -> "HistoryEvent":
        raw_attribs = element.attrib
        attributes = {
            k: v for k, v in raw_attribs.items() if not k.startswith(flag_ns_wrapped)
        }
        flags = [
            k.partition(flag_ns_wrapped)[2]
            for k in raw_attribs.keys()
            if k.startswith(flag_ns_wrapped)
        ]
        try:
            (payload,) = element.xpath("./payload")
        except ValueError:  # there might not be exactly 1 payload
            payload = "<payload/>"
        return cls(attributes, flags, payload)
