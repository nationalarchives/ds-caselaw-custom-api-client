import json
from enum import Enum
from typing import Any, Optional, TypedDict

from typing_extensions import NotRequired


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
