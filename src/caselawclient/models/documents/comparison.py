from typing import TypedDict

import caselawclient.models.documents


class AttributeComparison(TypedDict):
    """Results from a comparison of one attribute across two documents"""

    attribute: str
    attribute_label: str
    this_value: str
    that_value: str
    match: bool


class Comparison(list[AttributeComparison]):
    def __init__(
        self, this_doc: "caselawclient.models.documents.Document", that_doc: "caselawclient.models.documents.Document"
    ):
        # court, date, title
        self.append(
            AttributeComparison(
                attribute="court",
                attribute_label="court",
                this_value=this_doc.court,
                that_value=that_doc.court,
                match=this_doc.court == that_doc.court,
            )
        )
        self.append(
            AttributeComparison(
                attribute="date",
                attribute_label="date",
                this_value=this_doc.body.document_date_as_string,
                that_value=that_doc.body.document_date_as_string,
                match=this_doc.body.document_date_as_string == that_doc.body.document_date_as_string,
            )
        )
        self.append(
            AttributeComparison(
                attribute="name",
                attribute_label="name",
                this_value=this_doc.name,
                that_value=that_doc.name,
                match=this_doc.name == that_doc.name,
            )
        )

    def match(self) -> bool:
        """Is this comparison an exact match across all attributes?"""
        return all(x["match"] for x in self)

    def get(self, attribute: str) -> AttributeComparison:
        """Get an attribute by name"""
        return [x for x in self if x["attribute"] == attribute][0]
