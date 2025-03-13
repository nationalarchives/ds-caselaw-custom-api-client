import json
from enum import Enum
from typing import Any, Optional, TypedDict

from lxml import etree
from typing_extensions import NotRequired

from caselawclient.xml_helpers import DEFAULT_NAMESPACES

from ..models.documents import Document
from ..models.judgments import Judgment
from ..models.parser_logs import ParserLog
from ..models.press_summaries import PressSummary


class CannotDetermineDocumentType(Exception):
    pass


class AnnotationDataDict(TypedDict):
    type: str
    calling_function: str
    calling_agent: str
    message: NotRequired[str]
    payload: NotRequired[dict[str, Any]]
    automated: bool


class VersionType(Enum):
    """Valid types of version."""

    SUBMISSION = "submission"
    """ This version has been created as a result of a submission of a new document. """

    ENRICHMENT = "enrichment"
    """ This version has been created through an enrichment process. """

    EDIT = "edit"
    """ This version has been created as the result of a manual edit. """


class VersionAnnotation:
    """A class holding structured data about the reason for a version."""

    def __init__(
        self,
        version_type: VersionType,
        automated: bool,
        message: Optional[str] = None,
        payload: Optional[dict[str, Any]] = None,
    ):
        """
        :param version_type: The type of version being created
        :param automated: `True` if this action has happened as the result of an automated process, rather than a human
            action
        :param message: A human-readable string containing information about the version which can't be expressed in the
            structured data.
        :param payload: A dict containing additional information relevant to this version change
        """
        self.version_type = version_type
        self.automated = automated
        self.message = message
        self.payload = payload

        self.calling_function: Optional[str] = None
        self.calling_agent: Optional[str] = None

    def set_calling_function(self, calling_function: str) -> None:
        """
        Set the name of the calling function for tracing purposes

        :param calling_function: The name of the function which is performing the database write
        """
        self.calling_function = calling_function

    def set_calling_agent(self, calling_agent: str) -> None:
        """
        Set the name of the calling agent for tracing purposes

        :param calling_agent: The name of the agent which is performing the database write
        """
        self.calling_agent = calling_agent

    @property
    def structured_annotation_dict(self) -> AnnotationDataDict:
        """
        :return: A structured dict representing this `VersionAnnotation`

        :raises AttributeError: The name of the calling function has not been set; use `set_calling_function()`
        :raises AttributeError: The name of the calling agent has not been set; use `set_calling_agent()`
        """
        if not self.calling_function:
            raise AttributeError(
                "The name of the calling function has not been set; use set_calling_function()",
            )

        if not self.calling_agent:
            raise AttributeError(
                "The name of the calling agent has not been set; use set_calling_agent()",
            )

        annotation_data: AnnotationDataDict = {
            "type": self.version_type.value,
            "calling_function": self.calling_function,
            "calling_agent": self.calling_agent,
            "automated": self.automated,
        }

        if self.message:
            annotation_data["message"] = self.message

        if self.payload:
            annotation_data["payload"] = self.payload

        return annotation_data

    @property
    def as_json(self) -> str:
        """Render the structured annotation data as JSON, so it can be stored in the MarkLogic dls:annotation field.

        :return: A JSON string representing this `VersionAnnotation`"""

        return json.dumps(self.structured_annotation_dict)

    def __str__(self) -> str:
        return self.as_json


def get_document_type_class(xml: bytes) -> type[Document]:
    """Attempt to get the type of the document based on the top-level structure of the XML document."""

    node = etree.fromstring(xml)

    # If the main node is `<judgment>`, it's a judgment
    if node.xpath("/akn:akomaNtoso/akn:judgment", namespaces=DEFAULT_NAMESPACES):
        return Judgment

    # If the main node is `<doc name='pressSummary'>`, it's a press summary
    if node.xpath("/akn:akomaNtoso/akn:doc[@name='pressSummary']", namespaces=DEFAULT_NAMESPACES):
        return PressSummary

    # If the document is a parser error with a root element of `error`, it's not of a special type.
    if node.xpath("/error", namespaces=DEFAULT_NAMESPACES):
        return ParserLog

    # Otherwise, we don't know for sure. Fail out.
    raise CannotDetermineDocumentType(
        "Unable to determine the Document type by its XML",
    )
