from typing import TypedDict

import caselawclient.models.documents


class AttributeComparison(TypedDict):
    """Results from a comparison of one attribute across two documents"""

    label: str
    this_value: str
    that_value: str
    match: bool


class Comparison(dict[str, AttributeComparison]):
    def __init__(
        self, this_doc: "caselawclient.models.documents.Document", that_doc: "caselawclient.models.documents.Document"
    ):
        # court, date, title
        self["court"] = AttributeComparison(
            label="court",
            this_value=this_doc.metadata["court"].value,
            that_value=that_doc.metadata["court"].value,
            match=this_doc.metadata["court"].value == that_doc.metadata["court"].value,
        )

        self["date"] = AttributeComparison(
            label="date",
            this_value=this_doc.metadata["date"].as_string,
            that_value=that_doc.metadata["date"].as_string,
            match=this_doc.metadata["date"].as_string == that_doc.metadata["date"].as_string,
        )
        self["name"] = AttributeComparison(
            label="name",
            this_value=this_doc.metadata["name"].value,
            that_value=that_doc.metadata["name"].value,
            match=this_doc.metadata["name"].value == that_doc.metadata["name"].value,
        )

    def match(self) -> bool:
        """Is this comparison an exact match across all attributes?"""
        return all(x["match"] for x in self.values())
