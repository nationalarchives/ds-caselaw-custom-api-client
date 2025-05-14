import datetime
import os
import warnings
from functools import cached_property
from typing import TYPE_CHECKING, Any, Optional

from ds_caselaw_utils import courts
from ds_caselaw_utils.courts import CourtNotFoundException
from ds_caselaw_utils.types import NeutralCitationString
from requests_toolbelt.multipart import decoder

from caselawclient.errors import (
    DocumentNotFoundError,
    NotSupportedOnVersion,
    OnlySupportedOnVersion,
)
from caselawclient.identifier_resolution import IdentifierResolutions
from caselawclient.models.identifiers import Identifier
from caselawclient.models.identifiers.fclid import FindCaseLawIdentifier, FindCaseLawIdentifierSchema
from caselawclient.models.identifiers.unpacker import unpack_all_identifiers_from_etree
from caselawclient.models.utilities import VersionsDict, extract_version, render_versions
from caselawclient.models.utilities.aws import (
    ParserInstructionsDict,
    announce_document_event,
    check_docx_exists,
    delete_documents_from_private_bucket,
    generate_docx_url,
    generate_pdf_url,
    publish_documents,
    request_parse,
    unpublish_documents,
)
from caselawclient.types import DocumentURIString

from .body import DocumentBody
from .exceptions import CannotPublishUnpublishableDocument, DocumentNotSafeForDeletion
from .statuses import DOCUMENT_STATUS_HOLD, DOCUMENT_STATUS_IN_PROGRESS, DOCUMENT_STATUS_NEW, DOCUMENT_STATUS_PUBLISHED

MINIMUM_ENRICHMENT_TIME = datetime.timedelta(minutes=20)


class GatewayTimeoutGettingHTMLWithQuery(RuntimeWarning):
    pass


DOCUMENT_COLLECTION_URI_JUDGMENT = "judgment"
DOCUMENT_COLLECTION_URI_PRESS_SUMMARY = "press-summary"

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient


class Document:
    """
    A base class from which all other document types are extensions. This class includes the essential methods for
    retrieving and manipulating a document within MarkLogic.
    """

    document_noun = "document"
    """ The noun for a single instance of this document type. """

    document_noun_plural = "documents"
    """ The noun for a plural of this document type. """

    type_collection_name: str

    attributes_to_validate: list[tuple[str, bool, str]] = [
        (
            "is_failure",
            False,
            "This document failed to parse",
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

    def __init__(self, uri: DocumentURIString, api_client: "MarklogicApiClient", search_query: Optional[str] = None):
        """
        :param uri: The URI of the document to retrieve from MarkLogic.
        :param api_client: An instance of the API client object to handle communication with the MarkLogic server.
        :param search_query: Optionally, a search string which should be highlighted if it appears in the document body.

        :raises DocumentNotFoundError: The document does not exist within MarkLogic
        """
        self.uri: DocumentURIString = uri
        self.api_client: MarklogicApiClient = api_client
        if not self.document_exists():
            raise DocumentNotFoundError(f"Document {self.uri} does not exist")

        self.body: DocumentBody = DocumentBody(
            xml_bytestring=self.api_client.get_judgment_xml_bytestring(
                self.uri,
                show_unpublished=True,
                search_query=search_query,
            ),
        )
        """ `Document.body` represents the body of the document itself, without any information such as version tracking or properties. """

        self._initialise_identifiers()

    def __repr__(self) -> str:
        name = self.body.name or "un-named"
        return f"<{self.document_noun} {self.uri}: {name}>"

    def document_exists(self) -> bool:
        """Helper method to verify the existence of a document within MarkLogic.

        :return: `True` if the document exists, `False` otherwise."""
        return self.api_client.document_exists(self.uri)

    def docx_exists(self) -> bool:
        """There is a docx in S3 private bucket for this Document"""
        return check_docx_exists(self.uri)

    def _initialise_identifiers(self) -> None:
        """Load this document's identifiers from MarkLogic."""

        identifiers_element_as_etree = self.api_client.get_property_as_node(self.uri, "identifiers")
        self.identifiers = unpack_all_identifiers_from_etree(identifiers_element_as_etree)

    @property
    def best_human_identifier(self) -> Optional[Identifier]:
        """Return the preferred identifier for the document, providing that it is considered human readable."""
        preferred_identifier = self.identifiers.preferred()
        if preferred_identifier and preferred_identifier.schema.human_readable:
            return preferred_identifier
        return None

    @property
    def public_uri(self) -> str:
        """
        :return: The absolute, public URI at which a copy of this document can be found
        """
        return f"https://caselaw.nationalarchives.gov.uk/{self.slug}"

    @cached_property
    def slug(self) -> str:
        """
        :return: The best public-facing URL for the judgment, which is the slug
        of the most-preferred identifier, which should either be an NCN or fclid.
        """
        preferred_identifier = self.identifiers.preferred()
        if preferred_identifier:
            return preferred_identifier.url_slug
        msg = f"No preferred identifier exists for {self.uri}"
        raise RuntimeError(msg)

    @cached_property
    def is_published(self) -> bool:
        return self.api_client.get_published(self.uri)

    @cached_property
    def is_held(self) -> bool:
        return self.api_client.get_property(self.uri, "editor-hold") == "true"

    @cached_property
    def is_locked(self) -> bool:
        return self.checkout_message is not None

    @cached_property
    def checkout_message(self) -> Optional[str]:
        return self.api_client.get_judgment_checkout_status_message(self.uri)

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
        return generate_docx_url(self.uri)

    @property
    def pdf_url(self) -> str:
        return generate_pdf_url(self.uri)

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
    def versions_as_documents(self) -> list[Any]:
        """
        Returns a list of `Document` subclasses corresponding to the versions of the document. The first entry is:
           * the most recent
           * the highest numbered

        Note that this is only valid on the managed document -- a `DLS-DOCUMENTVERSION` error will occur if the document
        this is called on is itself a version.
        """
        if self.is_version:
            raise NotSupportedOnVersion(
                "Cannot get versions of a version for {self.uri}",
            )
        docs = []
        for version in self.versions:
            doc_uri = DocumentURIString(version["uri"])
            docs.append(self.api_client.get_document_by_uri(doc_uri))
        return docs

    @cached_property
    def version_number(self) -> int:
        """
        Note that the highest number is the most recent version.
        Raises an exception if it is not a version (e.g. /2022/eat/1 is not a version)
        """
        version = extract_version(self.uri)
        if version == 0:
            raise OnlySupportedOnVersion(
                f"Version number requested for {self.uri} which is not a version",
            )
        return version

    @cached_property
    def is_version(self) -> bool:
        "Is this document a potentially historic version of a document, or is it the main document itself?"
        return extract_version(self.uri) != 0

    @cached_property
    def is_failure(self) -> bool:
        """
        Is this document in a 'failure' state from which no recovery is possible? This is considered to be the case if:

        - The document entirely failed to parse

        :return: `True` if this document is in a 'failure' state, otherwise `False`
        """
        return self.body.failed_to_parse

    @cached_property
    def is_parked(self) -> bool:
        return "parked" in self.uri

    @cached_property
    def has_name(self) -> bool:
        return bool(self.body.name)

    @cached_property
    def has_valid_court(self) -> bool:
        try:
            return bool(
                courts.get_by_code(self.body.court_and_jurisdiction_identifier_string),
            )
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

    @cached_property
    def annotation(self) -> str:
        return self.api_client.get_version_annotation(self.uri)

    @cached_property
    def version_created_datetime(self) -> datetime.datetime:
        return self.api_client.get_version_created_datetime(self.uri)

    @property
    def status(self) -> str:
        if self.is_published:
            return DOCUMENT_STATUS_PUBLISHED

        if self.is_held:
            return DOCUMENT_STATUS_HOLD

        if self.assigned_to:
            return DOCUMENT_STATUS_IN_PROGRESS

        return DOCUMENT_STATUS_NEW

    def force_enrich(self) -> None:
        """
        Request enrichment of the document, but do no checks
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        self.api_client.set_property(
            self.uri,
            "last_sent_to_enrichment",
            now.isoformat(),
        )

        announce_document_event(
            uri=self.uri,
            status="enrich",
            enrich=True,
        )

    def enrich(self) -> bool:
        """
        Request enrichment of a document, if it's sensible to do so.
        """
        if self.enriched_recently is False:
            print("Enrichment requested")
            self.force_enrich()
            return True
        print("Enrichment not requested as document was enriched recently")
        return False

    @cached_property
    def enriched_recently(self) -> bool:
        """
        Has this document been enriched recently?
        """

        last_enrichment = self.body.enrichment_datetime
        if not last_enrichment:
            return False

        now = datetime.datetime.now(tz=datetime.timezone.utc)

        return now - last_enrichment < MINIMUM_ENRICHMENT_TIME

    @cached_property
    def validates_against_schema(self) -> bool:
        """
        Does the document validate against the most recent schema?
        """
        return self.api_client.validate_document(self.uri)

    def assign_fclid_if_missing(self) -> Optional[FindCaseLawIdentifier]:
        """If the document does not have an FCLID already, mint a new one and save it."""
        if len(self.identifiers.of_type(FindCaseLawIdentifier)) == 0:
            document_fclid = FindCaseLawIdentifierSchema.mint(self.api_client)
            self.identifiers.add(document_fclid)
            self.save_identifiers()
            return document_fclid

        return None

    def publish(self) -> None:
        """
        :raises CannotPublishUnpublishableDocument: This document has not passed the checks in `is_publishable`, and as
        such cannot be published.
        """
        if not self.is_publishable:
            raise CannotPublishUnpublishableDocument

        ## Make sure the document has an FCLID
        self.assign_fclid_if_missing()

        publish_documents(self.uri)
        self.api_client.set_published(self.uri, True)
        announce_document_event(
            uri=self.uri,
            status="publish",
        )
        self.enrich()

    def unpublish(self) -> None:
        self.api_client.break_checkout(self.uri)
        unpublish_documents(self.uri)
        self.api_client.set_published(self.uri, False)
        announce_document_event(
            uri=self.uri,
            status="unpublish",
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
            raise DocumentNotSafeForDeletion

    def move(self, new_citation: NeutralCitationString) -> None:
        self.api_client.update_document_uri(self.uri, new_citation)

    def force_reparse(self) -> None:
        "Send an SNS notification that triggers reparsing, also sending all editor-modifiable metadata and URI"

        now = datetime.datetime.now(datetime.timezone.utc)
        self.api_client.set_property(self.uri, "last_sent_to_parser", now.isoformat())

        parser_type_noun = {"judgment": "judgment", "press summary": "pressSummary"}[self.document_noun]
        checked_date: Optional[str] = (
            self.body.document_date_as_date.isoformat()
            if self.body.document_date_as_date and self.body.document_date_as_date > datetime.date(1001, 1, 1)
            else None
        )

        # the keys of parser_instructions should exactly match the parser output
        # in the *-metadata.json files by the parser. Whilst typically empty
        # values are "" from the API, we should pass None instead in this case.

        parser_instructions: ParserInstructionsDict = {
            "documentType": parser_type_noun,
            "metadata": {
                "name": self.body.name or None,
                "cite": None,
                "court": self.body.court or None,
                "date": checked_date,
                "uri": self.uri,
            },
        }

        ## TODO: Remove this hack around the fact that NCNs are assumed to be present for all documents' metadata, but actually different document classes may have different metadata
        if hasattr(self, "neutral_citation"):
            parser_instructions["metadata"]["cite"] = self.neutral_citation

        request_parse(
            uri=self.uri,
            reference=self.consignment_reference,
            parser_instructions=parser_instructions,
        )

    def reparse(self) -> bool:
        # note that we set 'last_sent_to_parser' even if we can't send it to the parser
        # it means 'last tried to reparse' much more consistently.
        now = datetime.datetime.now(datetime.timezone.utc)
        self.api_client.set_property(self.uri, "last_sent_to_parser", now.isoformat())
        if self.can_reparse:
            self.force_reparse()
            return True
        return False

    @cached_property
    def can_reparse(self) -> bool:
        """
        Is it sensible to reparse this document?
        """
        return self.docx_exists()

    def save_identifiers(self) -> None:
        """Save the current state of this Document's identifiers to MarkLogic."""
        self.identifiers.validate()
        self.api_client.set_property_as_node(self.uri, "identifiers", self.identifiers.as_etree)

    def __getattr__(self, name: str) -> Any:
        warnings.warn(f"{name} no longer exists on Document, using Document.body instead", DeprecationWarning)
        try:
            return getattr(self.body, name)
        except Exception:
            raise AttributeError(f"Neither 'Document' nor 'DocumentBody' objects have an attribute '{name}'")

    def linked_document_resolutions(self, namespaces: list[str], only_published: bool = True) -> IdentifierResolutions:
        """Get document resolutions which share the same neutral citation as this document."""
        if not hasattr(self, "neutral_citation") or not self.neutral_citation:
            return IdentifierResolutions([])

        resolutions = self.api_client.resolve_from_identifier_value(self.neutral_citation)
        if only_published:
            resolutions = resolutions.published()

        # only documents which aren't this one and have a right namespace
        return IdentifierResolutions(
            [
                resolution
                for resolution in resolutions
                if resolution.document_uri != self.uri.as_marklogic() and resolution.identifier_namespace in namespaces
            ]
        )

    def linked_documents(self, namespaces: list[str], only_published: bool = True) -> list["Document"]:
        resolutions = self.linked_document_resolutions(namespaces=namespaces, only_published=only_published)
        return [
            Document(resolution.document_uri.as_document_uri(), api_client=self.api_client)
            for resolution in resolutions
        ]

    def content_as_html(self) -> str | None:
        xlst_image_location = os.getenv("XSLT_IMAGE_LOCATION", "")
        return self.body.content_html(f"{xlst_image_location}/{self.uri}")
