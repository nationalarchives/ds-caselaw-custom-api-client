import json
from enum import Enum
from typing import Optional, TypedDict

from typing_extensions import NotRequired


class AnnotationDataDict(TypedDict):
    type: str
    calling_function: str
    message: NotRequired[str]


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

    def __init__(self, version_type: VersionType, message: Optional[str] = None):
        """
        :param version_type: The type of version being created
        :param message: A human-readable string containing information about the version which can't be expressed in the
            structured data.
        """
        self.version_type = version_type
        self.message = message

    def set_calling_function(self, calling_function: str) -> None:
        """
        Set the name of the calling function for tracing purposes

        :param calling_function: The name of the function which is performing the database write
        """
        self.calling_function = calling_function

    @property
    def structured_annotation_dict(self) -> AnnotationDataDict:
        """
        :return: A structured dict representing this `VersionAnnotation`

        :raises AttributeError: The name of the calling function has not been set; use `set_calling_function()`
        """
        if not self.calling_function:
            raise AttributeError(
                "The name of the calling function has not been set; use set_calling_function()"
            )

        annotation_data: AnnotationDataDict = {
            "type": self.version_type.value,
            "calling_function": self.calling_function,
        }

        if self.message:
            annotation_data["message"] = self.message

        return annotation_data

    @property
    def as_json(self) -> str:
        """Render the structured annotation data as JSON, so it can be stored in the MarkLogic dls:annotation field.

        :return: A JSON string representing this `VersionAnnotation`"""

        return json.dumps(self.structured_annotation_dict)

    def __str__(self) -> str:
        return self.as_json
