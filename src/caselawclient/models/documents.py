import datetime
import warnings
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, NewType, Optional

from ds_caselaw_utils import courts
from ds_caselaw_utils.courts import CourtNotFoundException
from lxml import etree
from lxml import html as html_parser
from requests_toolbelt.multipart import decoder

from caselawclient.models.utilities import extract_version

from ..errors import (
    DocumentNotFoundError,
    GatewayTimeoutError,
    NotSupportedOnVersion,
    OnlySupportedOnVersion,
)
from ..xml_helpers import get_xpath_match_string, get_xpath_match_strings
from .utilities import VersionsDict, get_judgment_root, render_versions
from .utilities.aws import (
    ParserInstructionsDict,
    announce_document_event,
    delete_documents_from_private_bucket,
    generate_docx_url,
    generate_pdf_url,
    publish_documents,
    request_parse,
    unpublish_documents,
    uri_for_s3,
)


class UnparsableDate(Warning):
    pass


class GatewayTimeoutGettingHTMLWithQuery(RuntimeWarning):
    pass


DOCUMENT_STATUS_HOLD = "On hold"
""" This document has been placed on hold to actively prevent publication. """

DOCUMENT_STATUS_PUBLISHED = "Published"
""" This document has been published and should be considered publicly visible. """

DOCUMENT_STATUS_IN_PROGRESS = "In progress"
""" This document has not been published or put on hold, and has been picked up by an editor and
    should be progressing through the document pipeline. """

DOCUMENT_STATUS_NEW = "New"
""" This document isn't published, on hold, or assigned, and can be picked up by an editor in the future. """


DOCUMENT_COLLECTION_URI_JUDGMENT = "judgment"
DOCUMENT_COLLECTION_URI_PRESS_SUMMARY = "press-summary"

if TYPE_CHECKING:
    from caselawclient.Client import MarklogicApiClient


DocumentURIString = NewType("DocumentURIString", str)


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
        :param uri: For historical reasons this accepts a pseudo-URI which may include leading or trailing slashes.

        :raises DocumentNotFoundError: The document does not exist within MarkLogic
        """
        self.uri = DocumentURIString(uri.strip("/"))
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
    def document_date_as_date(self) -> Optional[datetime.date]:
        if not self.document_date_as_string:
            return None
        try:
            return datetime.datetime.strptime(
                self.document_date_as_string, "%Y-%m-%d"
            ).date()
        except ValueError:
            warnings.warn(
                f"Unparsable date encountered: {self.document_date_as_string}",
                UnparsableDate,
            )
            return None

    def get_manifestation_datetimes(
        self, name: Optional[str] = None
    ) -> list[datetime.datetime]:
        name_filter = f"[@name='{name}']" if name else ""
        iso_datetimes = self._get_xpath_match_strings(
            "/akn:akomaNtoso/akn:*/akn:meta/akn:identification/akn:FRBRManifestation"
            f"/akn:FRBRdate{name_filter}/@date",
            {"akn": "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"},
        )
        return [datetime.datetime.fromisoformat(event) for event in iso_datetimes]

    def get_latest_manifestation_datetime(
        self, name: Optional[str] = None
    ) -> Optional[datetime.datetime]:
        events = self.get_manifestation_datetimes(name)
        if not events:
            return None
        else:
            return max(events)

    def get_latest_manifestation_type(self) -> Optional[str]:
        return max(
            (
                (type, time)
                for type in ["transform", "tna-enriched"]
                if (time := self.get_latest_manifestation_datetime(type))
            ),
            key=lambda x: x[1],
        )[0]

    @cached_property
    def transformation_datetime(self) -> Optional[datetime.datetime]:
        return self.get_latest_manifestation_datetime("transform")

    @cached_property
    def enrichment_datetime(self) -> Optional[datetime.datetime]:
        return self.get_latest_manifestation_datetime("tna-enriched")

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
                "Cannot get versions of a version for {self.uri}"
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
                f"Version number requested for {self.uri} which is not a version"
            )
        return version

    @cached_property
    def is_version(self) -> bool:
        "Is this document a potentially historic version of a document, or is it the main document itself?"
        return extract_version(self.uri) != 0

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

    def content_as_html(
        self,
        version_uri: Optional[DocumentURIString] = None,
        query: Optional[str] = None,
    ) -> str:
        try:
            results = self.api_client.eval_xslt(
                self.uri, version_uri, show_unpublished=True, query=query
            )
            multipart_data = decoder.MultipartDecoder.from_response(results)
            return str(multipart_data.parts[0].text)
        except GatewayTimeoutError as e:
            if query is not None:
                warnings.warn(
                    (
                        "Gateway timeout when getting content with query"
                        "highlighting for document %s, version %s, and query"
                        '"%s", falling back to unhighlighted content...'
                    )
                    % (self.uri, version_uri, query),
                    GatewayTimeoutGettingHTMLWithQuery,
                )
                return self.content_as_html(version_uri)
            else:
                raise e

    def number_of_mentions(self, query: str) -> int:
        html = self.content_as_html(query=query)
        tree = html_parser.fromstring(html.encode("utf-8"))
        return len(tree.findall(".//mark"))

    @cached_property
    def is_failure(self) -> bool:
        """
        Is this document in a 'failure' state from which no recovery is possible? This is considered to be the case if:

        - The document entirely failed to parse

        :return: `True` if this document is in a 'failure' state, otherwise `False`
        """
        if self.failed_to_parse:
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

    def enrich(self) -> None:
        announce_document_event(
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
        announce_document_event(
            uri=self.uri,
            status="published",
            enrich=True,
        )

    def unpublish(self) -> None:
        self.api_client.break_checkout(self.uri)
        unpublish_documents(uri_for_s3(self.uri))
        self.api_client.set_published(self.uri, False)
        announce_document_event(
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

    def _get_xpath_match_strings(
        self, xpath: str, namespaces: Dict[str, str]
    ) -> list[str]:
        return get_xpath_match_strings(self.content_as_xml_tree, xpath, namespaces)

    def overwrite(self, new_citation: str) -> None:
        self.api_client.overwrite_document(self.uri, new_citation)

    def move(self, new_citation: str) -> None:
        self.api_client.update_document_uri(self.uri, new_citation)

    def reparse(self) -> None:
        "Send an SNS notification that triggers reparsing, also sending all editor-modifiable metadata and URI"

        parser_type_noun = {"judgment": "judgment", "press summary": "pressSummary"}[
            self.document_noun
        ]
        checked_date = (
            self.document_date_as_string
            if self.document_date_as_string > "1001"
            else None
        )

        # the keys of parser_instructions should exactly match the parser output
        # in the *-metadata.json files by the parser. Whilst typically empty
        # values are "" from the API, we should pass None instead in this case.

        parser_instructions: ParserInstructionsDict = {
            "name": self.name or None,
            "cite": self.best_human_identifier or None,
            "court": self.court or None,
            "date": checked_date,
            "uri": self.uri,
            "documentType": parser_type_noun,
            "published": self.is_published,
        }

        request_parse(
            uri=self.uri,
            reference=self.consignment_reference,
            parser_instructions=parser_instructions,
        )
