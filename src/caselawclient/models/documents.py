import datetime
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Optional

from ds_caselaw_utils import courts
from ds_caselaw_utils.courts import CourtNotFoundException
from lxml import etree
from requests_toolbelt.multipart import decoder

from ..errors import DocumentNotFoundError
from ..xml_helpers import get_xpath_match_string
from .utilities import VersionsDict, get_judgment_root, render_versions
from .utilities.aws import (
    delete_documents_from_private_bucket,
    generate_docx_url,
    generate_pdf_url,
    notify_changed,
    publish_documents,
    unpublish_documents,
    uri_for_s3,
)

DOCUMENT_STATUS_HOLD = "On hold"
""" This document has been placed on hold to actively prevent publication. """

DOCUMENT_STATUS_PUBLISHED = "Published"
""" This document has been published and should be considered publicly visible. """

DOCUMENT_STATUS_IN_PROGRESS = "In progress"
""" This document has not been published or put on hold, and should be progressing through the document pipeline. """

DOCUMENT_COLLECTION_URI_JUDGMENT = "judgment"
DOCUMENT_COLLECTION_URI_PRESS_SUMMARY = "press-summary"

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient


class CannotPublishUnpublishableDocument(Exception):
    """A document which has failed publication safety checks in `Document.is_publishable` cannot be published."""

    pass


class DocumentNotSafeForDeletion(Exception):
    """A document which is not safe for deletion cannot be deleted."""

    pass


class Document:
    """
    A base class from which all other document types are extensions. This class includes the essential methods for
    retrieving and manipulating a document within MarkLogic.
    """

    document_noun = "document"
    """ The noun for a single instance of this document type. """

    document_noun_plural = "documents"
    """ The noun for a plural of this document type. """

    attributes_to_validate: list[tuple[str, bool, str]] = [
        (
            "failed_to_parse",
            False,
            "This document failed to parse",
        ),
        (
            "is_failure",
            False,
            "This {document_noun} does not have a valid URI",
        ),
        (
            "is_parked",
            False,
            "This {document_noun} is currently parked at a temporary URI",
        ),
        (
            "is_held",
            False,
            "This {document_noun} is currently on hold",
        ),
        (
            "has_name",
            True,
            "This {document_noun} has no name",
        ),
        (
            "has_valid_court",
            True,
            "The court for this {document_noun} is not valid",
        ),
    ]
    """
    A list of tuples in the form:

    ``` python
    (
        attribute_name,
        passing_condition,
        error_message,
    )
    ```

    describing attributes which should be checked in order for a document to be considered valid.

    Individual document classes should extend this list where necessary to validate document type-specific attributes.
    """

    def __init__(self, uri: str, api_client: "MarklogicApiClient"):
        """
        :raises DocumentNotFoundError: The document does not exist within MarkLogic
        """
        self.uri = uri.strip("/")
        self.api_client = api_client
        if not self.document_exists():
            raise DocumentNotFoundError(f"Document {self.uri} does not exist")

    def document_exists(self) -> bool:
        """Helper method to verify the existence of a document within MarkLogic.

        :return: `True` if the document exists, `False` otherwise."""
        return self.api_client.document_exists(self.uri)

    @property
    def best_human_identifier(self) -> Optional[str]:
        """
        Some identifier that is understood by legal professionals to refer to this legal event
        that is not the name of the document.
        Typically, this will be the neutral citation number, should it exist.
        Should typically overridden in subclasses.
        """
        return None

    @property
    def public_uri(self) -> str:
        """
        :return: The absolute, public URI at which a copy of this document can be found
        """
        return "https://caselaw.nationalarchives.gov.uk/{uri}".format(uri=self.uri)

    @cached_property
    def name(self) -> str:
        return self._get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRname/@value",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )

    @cached_property
    def court(self) -> str:
        return self._get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:proprietary/uk:court/text()",
            {
                "uk": "https://caselaw.nationalarchives.gov.uk/akn",
                "akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0",
            },
        )

    @cached_property
    def document_date_as_string(self) -> str:
        return self._get_xpath_match_string(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRWork/akn:FRBRdate/@date",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )

    @cached_property
    def document_date_as_date(self) -> datetime.date:
        return datetime.datetime.strptime(
            self.document_date_as_string, "%Y-%m-%d"
        ).date()

    @cached_property
    def is_published(self) -> bool:
        return self.api_client.get_published(self.uri)

    @cached_property
    def is_held(self) -> bool:
        return self.api_client.get_property(self.uri, "editor-hold") == "true"

    @cached_property
    def source_name(self) -> str:
        return self.api_client.get_property(self.uri, "source-name")

    @cached_property
    def source_email(self) -> str:
        return self.api_client.get_property(self.uri, "source-email")

    @cached_property
    def consignment_reference(self) -> str:
        return self.api_client.get_property(self.uri, "transfer-consignment-reference")

    @property
    def docx_url(self) -> str:
        return generate_docx_url(uri_for_s3(self.uri))

    @property
    def pdf_url(self) -> str:
        return generate_pdf_url(uri_for_s3(self.uri))

    @cached_property
    def assigned_to(self) -> str:
        return self.api_client.get_property(self.uri, "assigned-to")

    @cached_property
    def versions(self) -> list[VersionsDict]:
        versions_response = self.api_client.list_judgment_versions(self.uri)

        try:
            decoded_versions = decoder.MultipartDecoder.from_response(versions_response)
            return render_versions(decoded_versions.parts)
        except AttributeError:
            return []

    @cached_property
    def content_as_xml(self) -> str:
        return self.api_client.get_judgment_xml(self.uri, show_unpublished=True)

    @cached_property
    def content_as_xml_bytestring(self) -> bytes:
        return self.api_client.get_judgment_xml_bytestring(
            self.uri, show_unpublished=True
        )

    @cached_property
    def content_as_xml_tree(self) -> Any:
        return etree.fromstring(self.content_as_xml_bytestring)

    def content_as_html(self, version_uri: Optional[str] = None) -> str:
        results = self.api_client.eval_xslt(
            self.uri, version_uri, show_unpublished=True
        )
        multipart_data = decoder.MultipartDecoder.from_response(results)
        return str(multipart_data.parts[0].text)

    @cached_property
    def is_failure(self) -> bool:
        if "failures" in self.uri:
            return True
        return False

    @cached_property
    def is_parked(self) -> bool:
        if "parked" in self.uri:
            return True
        return False

    @cached_property
    def failed_to_parse(self) -> bool:
        """
        Did this document entirely fail to parse?

        :return: `True` if there was a complete parser failure, otherwise `False`
        """
        if "error" in self._get_root():
            return True
        return False

    def _get_root(self) -> str:
        return get_judgment_root(self.content_as_xml_bytestring)

    @cached_property
    def has_name(self) -> bool:
        if not self.name:
            return False

        return True

    @cached_property
    def has_valid_court(self) -> bool:
        try:
            return bool(courts.get_by_code(self.court))
        except CourtNotFoundException:
            return False

    @cached_property
    def is_publishable(self) -> bool:
        # If there are any validation failures, there will be no messages in the list.
        # An empty list (which is falsy) therefore means the judgment can be published safely.
        return not self.validation_failure_messages

    @cached_property
    def validation_failure_messages(self) -> list[str]:
        exception_list = []
        for function_name, pass_value, message in self.attributes_to_validate:
            if getattr(self, function_name) != pass_value:
                exception_list.append(message.format(document_noun=self.document_noun))
        return sorted(exception_list)

    @property
    def status(self) -> str:
        if self.is_published:
            return DOCUMENT_STATUS_PUBLISHED

        if self.is_held:
            return DOCUMENT_STATUS_HOLD

        return DOCUMENT_STATUS_IN_PROGRESS

    def enrich(self) -> None:
        notify_changed(
            uri=self.uri,
            status="published",
            enrich=True,
        )

    def publish(self) -> None:
        """
        :raises CannotPublishUnpublishableDocument: This document has not passed the checks in `is_publishable`, and as
        such cannot be published.
        """
        if not self.is_publishable:
            raise CannotPublishUnpublishableDocument

        publish_documents(uri_for_s3(self.uri))
        self.api_client.set_published(self.uri, True)
        notify_changed(
            uri=self.uri,
            status="published",
            enrich=True,
        )

    def unpublish(self) -> None:
        self.api_client.break_checkout(self.uri)
        unpublish_documents(uri_for_s3(self.uri))
        self.api_client.set_published(self.uri, False)
        notify_changed(
            uri=self.uri,
            status="not published",
            enrich=False,
        )

    def hold(self) -> None:
        self.api_client.set_property(self.uri, "editor-hold", "true")

    def unhold(self) -> None:
        self.api_client.set_property(self.uri, "editor-hold", "false")

    @cached_property
    def safe_to_delete(self) -> bool:
        """
        Determines if a document is in a state where it's safe to be deleted, eg not currently publicly available.

        :return: If the document is safe to be deleted
        """

        return not self.is_published

    def delete(self) -> None:
        """
        Deletes this document from MarkLogic and any resources from AWS.
        """

        if self.safe_to_delete:
            self.api_client.delete_judgment(self.uri)
            delete_documents_from_private_bucket(self.uri)
        else:
            raise DocumentNotSafeForDeletion()

    def _get_xpath_match_string(self, xpath: str, namespaces: Dict[str, str]) -> str:
        return get_xpath_match_string(self.content_as_xml_tree, xpath, namespaces)

    def overwrite(self, new_citation: str) -> None:
        self.api_client.overwrite_document(self.uri, new_citation)

    def move(self, new_citation: str) -> None:
        self.api_client.update_document_uri(self.uri, new_citation)
