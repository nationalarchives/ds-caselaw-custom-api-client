import importlib.metadata
import json
import logging
import os
import re
import warnings
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Optional, Type, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, ParseError, fromstring

import environ
import requests
from ds_caselaw_utils.types import NeutralCitationString
from lxml import etree
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart import decoder

from caselawclient import xquery_type_dicts as query_dicts
from caselawclient.client_helpers import VersionAnnotation
from caselawclient.identifier_resolution import IdentifierResolutions
from caselawclient.models.documents import (
    DOCUMENT_COLLECTION_URI_JUDGMENT,
    DOCUMENT_COLLECTION_URI_PRESS_SUMMARY,
    Document,
)
from caselawclient.models.judgments import Judgment
from caselawclient.models.press_summaries import PressSummary
from caselawclient.models.utilities import move
from caselawclient.search_parameters import SearchParameters
from caselawclient.types import DocumentIdentifierSlug, DocumentIdentifierValue, DocumentURIString
from caselawclient.xquery_type_dicts import (
    MarkLogicDocumentURIString,
    MarkLogicDocumentVersionURIString,
    MarkLogicPrivilegeURIString,
)

from .content_hash import validate_content_hash
from .errors import (
    DocumentNotFoundError,
    GatewayTimeoutError,
    MarklogicAPIError,
    MarklogicBadRequestError,
    MarklogicCheckoutConflictError,
    MarklogicCommunicationError,
    MarklogicNotPermittedError,
    MarklogicResourceLockedError,
    MarklogicResourceNotCheckedOutError,
    MarklogicResourceNotFoundError,
    MarklogicResourceUnmanagedError,
    MarklogicUnauthorizedError,
    MarklogicValidationFailedError,
)

env = environ.Env()
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_XSL_TRANSFORM = "accessible-html.xsl"

try:
    VERSION = importlib.metadata.version("ds-caselaw-marklogic-api-client")
except importlib.metadata.PackageNotFoundError:
    VERSION = "0"
DEFAULT_USER_AGENT = f"ds-caselaw-marklogic-api-client/{VERSION}"

DEBUG: bool = bool(os.getenv("DEBUG", default=False))


class NoResponse(Exception):
    """A requests HTTPError has no response. We expect this will never happen."""


class MultipartResponseLongerThanExpected(Exception):
    """
    MarkLogic has returned a multipart response with more than one part, where only a single part was expected.
    """


def get_multipart_strings_from_marklogic_response(
    response: requests.Response,
) -> list[str]:
    """
    Given a HTTP response from a MarkLogic server, extract the text content from each part of the response.

    :param response: A multipart HTTP response

    :return: A list of the text within each part of the response
    """
    if not (response.content):
        return []

    multipart_data = decoder.MultipartDecoder.from_response(response)

    return [part.text for part in multipart_data.parts]


def get_multipart_bytes_from_marklogic_response(
    response: requests.Response,
) -> list[bytes]:
    if not (response.content):
        return []

    multipart_data = decoder.MultipartDecoder.from_response(response)

    return [part.content for part in multipart_data.parts]


def get_single_string_from_marklogic_response(
    response: requests.Response,
) -> str:
    """
    Given a HTTP response from a MarkLogic server, assuming the response contains a single part, extract the text
    content of the response.

    :param response: A multipart HTTP response

    :return: The text of the response

    :raises MultipartResponseLongerThanExpected: If the response from MarkLogic has more than one part
    """
    parts = get_multipart_strings_from_marklogic_response(response)
    part_count = len(parts)

    if part_count == 0:
        # TODO: This should strictly speaking be None, but fixing this involves refactoring a lot of other stuff which
        # relies on "" being falsy.
        return ""

    if part_count > 1:
        raise MultipartResponseLongerThanExpected(
            f"Response returned {part_count} multipart items, expected 1",
        )

    return parts[0]


def get_single_bytestring_from_marklogic_response(
    response: requests.Response,
) -> bytes:
    parts = get_multipart_bytes_from_marklogic_response(response)
    part_count = len(parts)

    if part_count == 0:
        # TODO: This should strictly speaking be None, but fixing this involves refactoring a lot of other stuff which
        # relies on "" being falsy.
        return b""

    if part_count > 1:
        raise MultipartResponseLongerThanExpected(
            f"Response returned {part_count} multipart items, expected 1",
        )

    return parts[0]


class MarklogicApiClient:
    """
    The base class for interacting with a MarkLogic instance.
    """

    http_error_classes: dict[int, Type[MarklogicAPIError]] = {
        400: MarklogicBadRequestError,
        401: MarklogicUnauthorizedError,
        403: MarklogicNotPermittedError,
        404: MarklogicResourceNotFoundError,
        504: GatewayTimeoutError,
    }
    error_code_classes: dict[str, Type[MarklogicAPIError]] = {
        "XDMP-DOCNOTFOUND": MarklogicResourceNotFoundError,
        "XDMP-LOCKCONFLICT": MarklogicResourceLockedError,
        "DLS-UNMANAGED": MarklogicResourceUnmanagedError,
        "DLS-NOTCHECKEDOUT": MarklogicResourceNotCheckedOutError,
        "DLS-CHECKOUTCONFLICT": MarklogicCheckoutConflictError,
        "SEC-PRIVDNE": MarklogicNotPermittedError,
        "XDMP-VALIDATE.*": MarklogicValidationFailedError,
        "FCL-DOCUMENTNOTFOUND.*": DocumentNotFoundError,
    }

    default_http_error_class = MarklogicCommunicationError

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        use_https: bool,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"{'https' if use_https else 'http'}://{self.host}:8011"
        # Apply auth / common headers to the session
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.headers.update({"User-Agent": user_agent})
        self.user_agent = user_agent

    def get_press_summaries_for_document_uri(
        self,
        uri: DocumentURIString,
    ) -> list[PressSummary]:
        """
        Returns a list of PressSummary objects associated with a given Document URI
        """
        vars: query_dicts.GetComponentsForDocumentDict = {
            "parent_uri": uri,
            "component": "pressSummary",
        }
        response = self._send_to_eval(vars, "get_components_for_document.xqy")
        uris = get_multipart_strings_from_marklogic_response(response)
        return [
            PressSummary(DocumentURIString(uri.strip("/").strip(".xml")), self) for uri in uris
        ]  # TODO: Migrate this strip behaviour into proper manipulation of a MarkLogicURIString

    def get_document_by_uri(
        self,
        uri: DocumentURIString,
        search_query: Optional[str] = None,
    ) -> Document:
        document_type_class = self.get_document_type_from_uri(uri)
        return document_type_class(uri, self, search_query=search_query)

    def get_document_type_from_uri(self, uri: DocumentURIString) -> Type[Document]:
        vars: query_dicts.DocumentCollectionsDict = {
            "uri": self._format_uri_for_marklogic(uri),
        }
        response = self._send_to_eval(vars, "document_collections.xqy")
        collections = get_multipart_strings_from_marklogic_response(response)

        if DOCUMENT_COLLECTION_URI_JUDGMENT in collections:
            return Judgment
        if DOCUMENT_COLLECTION_URI_PRESS_SUMMARY in collections:
            return PressSummary
        return Document

    def _get_error_code_class(self, error_code: str) -> Type[MarklogicAPIError]:
        """
        Get the exception type for a MarkLogic error code, or the first part of one
        """
        for regex, error in self.error_code_classes.items():
            if re.fullmatch(regex, error_code):
                return error
        print(f"No error code match found for {error_code}")
        return self.default_http_error_class

    def _path_to_request_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    @classmethod
    def _get_error_code(cls, content_as_xml: Optional[str]) -> str:
        logging.warning(
            "XMLTools is deprecated and will be removed in later versions. "
            "Use methods from MarklogicApiClient.Client instead.",
        )
        if not content_as_xml:
            return "Unknown error, Marklogic returned a null or empty response"
        try:
            xml = fromstring(content_as_xml)
            return xml.find(
                "message-code",
                namespaces={"": "http://marklogic.com/xdmp/error"},
            ).text  # type: ignore
        except (ParseError, TypeError, AttributeError):
            return "Unknown error, Marklogic returned a null or empty response"

    def _raise_for_status(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.response is None:
                raise NoResponse
            status_code = e.response.status_code
            new_error_class = self.http_error_classes.get(
                status_code,
                self.default_http_error_class,
            )
            try:
                response_body = json.dumps(response.json(), indent=4)
            except requests.JSONDecodeError:
                response_body = response.text

            if new_error_class == self.default_http_error_class:
                # Attempt to decode the error code from the response

                error_code = self._get_error_code(response.content.decode("utf-8"))

                new_error_class = self._get_error_code_class(error_code)

            new_exception = new_error_class(
                f"{e}. Response body:\n{response_body}",
            )
            new_exception.response = response
            raise new_exception

    def _format_uri_for_marklogic(
        self,
        uri: DocumentURIString,
    ) -> MarkLogicDocumentURIString:
        """
        MarkLogic requires a document URI that begins with a slash `/` and ends in `.xml`. This method ensures any takes
        a `DocumentURIString` and converts it to a MarkLogic-friendly `MarkLogicDocumentURIString`.

        :return: A `MarkLogicDocumentURIString` at which the document at the given `DocumentURIString` can be located
            within MarkLogic.
        """
        return MarkLogicDocumentURIString(f"/{uri.lstrip('/').rstrip('/')}.xml")

    def _xquery_path(self, xquery_file_name: str) -> str:
        return os.path.join(ROOT_DIR, "xquery", xquery_file_name)

    def _send_to_eval(
        self,
        vars: query_dicts.MarkLogicAPIDict,
        xquery_file_name: str,
    ) -> requests.Response:
        return self.eval(
            self._xquery_path(xquery_file_name),
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def _eval_and_decode(
        self,
        vars: query_dicts.MarkLogicAPIDict,
        xquery_file_name: str,
    ) -> str:
        response = self._send_to_eval(vars, xquery_file_name)
        return get_single_string_from_marklogic_response(response)

    def _eval_as_bytes(
        self,
        vars: query_dicts.MarkLogicAPIDict,
        xquery_file_name: str,
    ) -> bytes:
        response = self._send_to_eval(vars, xquery_file_name)
        return get_single_bytestring_from_marklogic_response(response)

    def prepare_request_kwargs(
        self,
        method: str,
        path: str,
        body: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        kwargs = dict(url=self._path_to_request_url(path))
        if data is not None:
            data = {k: v for k, v in data.items() if v is not None}
            if method == "GET":
                kwargs["params"] = data  # type: ignore
            else:
                kwargs["data"] = json.dumps(data)
        if body is not None:
            kwargs["data"] = body
        return kwargs

    def make_request(
        self,
        method: str,
        path: str,
        headers: CaseInsensitiveDict[Union[str, Any]],
        body: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> requests.Response:
        kwargs = self.prepare_request_kwargs(method, path, body, data)
        self.session.headers = headers
        response = self.session.request(method, **kwargs)
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def GET(self, path: str, headers: dict[str, Any], **data: Any) -> requests.Response:
        logging.warning("GET() is deprecated, use eval() or invoke()")
        return self.make_request("GET", path, headers, data)  # type: ignore

    def POST(
        self,
        path: str,
        headers: dict[str, Any],
        **data: Any,
    ) -> requests.Response:
        logging.warning("POST() is deprecated, use eval() or invoke()")
        return self.make_request("POST", path, headers, data)  # type: ignore

    def document_exists(self, document_uri: DocumentURIString) -> bool:
        uri = self._format_uri_for_marklogic(document_uri)
        vars: query_dicts.DocumentExistsDict = {
            "uri": uri,
        }
        decoded_response = self._eval_and_decode(vars, "document_exists.xqy")

        if decoded_response == "true":
            return True
        if decoded_response == "false":
            return False
        raise RuntimeError("Marklogic response was neither true nor false")

    def get_judgment_xml_bytestring(
        self,
        judgment_uri: DocumentURIString,
        version_uri: Optional[DocumentURIString] = None,
        show_unpublished: bool = False,
        search_query: Optional[str] = None,
    ) -> bytes:
        marklogic_document_uri = self._format_uri_for_marklogic(judgment_uri)
        marklogic_document_version_uri = (
            MarkLogicDocumentVersionURIString(
                self._format_uri_for_marklogic(version_uri),
            )
            if version_uri
            else None
        )
        show_unpublished = self.verify_show_unpublished(show_unpublished)

        vars: query_dicts.GetJudgmentDict = {
            "uri": marklogic_document_uri,
            "version_uri": marklogic_document_version_uri,
            "show_unpublished": show_unpublished,
            "search_query": search_query,
        }

        response = self._eval_as_bytes(vars, "get_judgment.xqy")
        if not response:
            raise MarklogicNotPermittedError(
                "The document is not published and show_unpublished was not set",
            )

        return response

    def get_judgment_xml(
        self,
        judgment_uri: DocumentURIString,
        version_uri: Optional[DocumentURIString] = None,
        show_unpublished: bool = False,
        search_query: Optional[str] = None,
    ) -> str:
        return self.get_judgment_xml_bytestring(
            judgment_uri,
            version_uri,
            show_unpublished,
            search_query=search_query,
        ).decode(encoding="utf-8")

    def set_document_name(
        self,
        document_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(document_uri)
        vars: query_dicts.SetMetadataNameDict = {"uri": uri, "content": content}
        return self._send_to_eval(vars, "set_metadata_name.xqy")

    def set_judgment_date(
        self,
        judgment_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        warnings.warn(
            "set_judgment_date() is deprecated, use set_document_work_expression_date()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.set_document_work_expression_date(judgment_uri, content)

    def set_document_work_expression_date(
        self,
        document_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(document_uri)
        vars: query_dicts.SetMetadataWorkExpressionDateDict = {
            "uri": uri,
            "content": content,
        }

        return self._send_to_eval(vars, "set_metadata_work_expression_date.xqy")

    def set_judgment_citation(
        self,
        judgment_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.SetMetadataCitationDict = {
            "uri": uri,
            "content": content.strip(),
        }

        return self._send_to_eval(vars, "set_metadata_citation.xqy")

    def set_document_court(
        self,
        document_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(document_uri)
        vars: query_dicts.SetMetadataCourtDict = {"uri": uri, "content": content}

        return self._send_to_eval(vars, "set_metadata_court.xqy")

    def set_document_jurisdiction(
        self,
        document_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(document_uri)
        vars: query_dicts.SetMetadataJurisdictionDict = {"uri": uri, "content": content}
        return self._send_to_eval(vars, "set_metadata_jurisdiction.xqy")

    def set_document_court_and_jurisdiction(
        self,
        document_uri: DocumentURIString,
        content: str,
    ) -> requests.Response:
        if "/" in content:
            court, jurisdiction = re.split("\\s*/\\s*", content)
            self.set_document_court(document_uri, court)
            return self.set_document_jurisdiction(document_uri, jurisdiction)
        self.set_document_court(document_uri, content)
        return self.set_document_jurisdiction(document_uri, "")

    def set_judgment_this_uri(
        self,
        judgment_uri: DocumentURIString,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        content_with_id = f"https://caselaw.nationalarchives.gov.uk/id/{judgment_uri.lstrip('/')}"
        content_without_id = f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}"
        content_with_xml = f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}/data.xml"
        vars: query_dicts.SetMetadataThisUriDict = {
            "uri": uri,
            "content_with_id": content_with_id,
            "content_without_id": content_without_id,
            "content_with_xml": content_with_xml,
        }

        return self._send_to_eval(vars, "set_metadata_this_uri.xqy")

    def save_locked_judgment_xml(
        self,
        judgment_uri: DocumentURIString,
        judgment_xml: bytes,
        annotation: VersionAnnotation,
    ) -> requests.Response:
        """assumes the judgment is already locked, does not unlock/check in
        note this version assumes the XML is raw bytes, rather than a tree..."""

        validate_content_hash(judgment_xml)
        uri = self._format_uri_for_marklogic(judgment_uri)

        annotation.set_calling_function("save_locked_judgment_xml")
        annotation.set_calling_agent(self.user_agent)

        vars: query_dicts.UpdateLockedJudgmentDict = {
            "uri": uri,
            "judgment": judgment_xml.decode("utf-8"),
            "annotation": annotation.as_json,
        }

        return self._send_to_eval(vars, "update_locked_judgment.xqy")

    def insert_document_xml(
        self,
        document_uri: DocumentURIString,
        document_xml: Element,
        document_type: type[Document],
        annotation: VersionAnnotation,
    ) -> requests.Response:
        """
        Insert a new XML document into MarkLogic.

        :param document_uri: The URI to insert the document at
        :param document_xml: The XML of the document to insert
        :param document_type: The type class of the document
        :param annotation: Annotations to record alongside this version

        :return: The response object from MarkLogic
        """
        xml = ElementTree.tostring(document_xml)

        uri = self._format_uri_for_marklogic(document_uri)

        annotation.set_calling_function("insert_document_xml")
        annotation.set_calling_agent(self.user_agent)

        vars: query_dicts.InsertDocumentDict = {
            "uri": uri,
            "type_collection": document_type.type_collection_name,
            "document": xml.decode("utf-8"),
            "annotation": annotation.as_json,
        }

        return self._send_to_eval(vars, "insert_document.xqy")

    def update_document_xml(
        self,
        document_uri: DocumentURIString,
        document_xml: Element,
        annotation: VersionAnnotation,
    ) -> requests.Response:
        """
        Updates an existing XML document in MarkLogic with a new version.

        This uses `dls:document-checkout-update-checkin` to perform this in a single operation.

        :param document_uri: The URI of the document to update
        :param document_xml: The new XML content of the document
        :param annotation: Annotations to record alongside this version

        :return: The response object from MarkLogic
        """
        xml = ElementTree.tostring(document_xml)

        uri = self._format_uri_for_marklogic(document_uri)

        annotation.set_calling_function("update_document_xml")
        annotation.set_calling_agent(self.user_agent)

        vars: query_dicts.UpdateDocumentDict = {
            "uri": uri,
            "judgment": xml.decode("utf-8"),
            "annotation": annotation.as_json,
        }

        return self._send_to_eval(vars, "update_document.xqy")

    def list_judgment_versions(
        self,
        judgment_uri: DocumentURIString,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.ListJudgmentVersionsDict = {"uri": uri}

        return self._send_to_eval(vars, "list_judgment_versions.xqy")

    def checkout_judgment(
        self,
        judgment_uri: DocumentURIString,
        annotation: str = "",
        expires_at_midnight: bool = False,
        timeout_seconds: int = -1,
    ) -> requests.Response:
        """If timeout_seconds is -1, the lock never times out"""
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.CheckoutJudgmentDict = {
            "uri": uri,
            "annotation": annotation,
            "timeout": timeout_seconds,
        }

        if expires_at_midnight:
            timeout = self.calculate_seconds_until_midnight()
            vars["timeout"] = timeout

        return self._send_to_eval(vars, "checkout_judgment.xqy")

    def checkin_judgment(self, judgment_uri: DocumentURIString) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.CheckinJudgmentDict = {"uri": uri}

        return self._send_to_eval(vars, "checkin_judgment.xqy")

    def get_judgment_checkout_status(
        self,
        judgment_uri: DocumentURIString,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetJudgmentCheckoutStatusDict = {"uri": uri}

        return self._send_to_eval(vars, "get_judgment_checkout_status.xqy")

    def get_judgment_checkout_status_message(
        self,
        judgment_uri: DocumentURIString,
    ) -> Optional[str]:
        """Return the annotation of the lock or `None` if there is no lock."""
        response = self.get_judgment_checkout_status(judgment_uri)
        if not response.content:
            return None
        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        if content == "":
            return None
        response_xml = ElementTree.fromstring(content)
        return response_xml.find(
            "dls:annotation",
            namespaces={"dls": "http://marklogic.com/xdmp/dls"},
        ).text  # type: ignore

    def get_judgment_version(
        self,
        judgment_uri: DocumentURIString,
        version: int,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetJudgmentVersionDict = {"uri": uri, "version": str(version)}

        return self._send_to_eval(vars, "get_judgment_version.xqy")

    def validate_document(self, document_uri: DocumentURIString) -> bool:
        vars: query_dicts.ValidateDocumentDict = {
            "uri": self._format_uri_for_marklogic(document_uri),
        }
        response = self._send_to_eval(vars, "validate_document.xqy")
        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        xml = ElementTree.fromstring(content)
        return (
            len(
                xml.findall(
                    ".//error:error",
                    {"error": "http://marklogic.com/xdmp/error"},
                ),
            )
            == 0
        )

    def eval(
        self,
        xquery_path: str,
        vars: str,
        accept_header: str = "multipart/mixed",
    ) -> requests.Response:
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": accept_header,
        }
        data = {
            "xquery": Path(xquery_path).read_text(),
            "vars": vars,
        }
        path = "LATEST/eval"

        if DEBUG:
            print(f"Sending {vars} to {xquery_path}")

        response = self.session.request(
            "POST",
            url=self._path_to_request_url(path),
            headers=headers,
            data=data,
        )
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def invoke(
        self,
        module: str,
        vars: str,
        accept_header: str = "multipart/mixed",
    ) -> requests.Response:
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": accept_header,
        }
        data = {
            "module": module,
            "vars": vars,
        }
        path = "LATEST/invoke"
        response = self.session.request(
            "POST",
            url=self._path_to_request_url(path),
            headers=headers,
            data=data,
        )
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def advanced_search(self, search_parameters: SearchParameters) -> requests.Response:
        """
        Performs a search on the entire document set.

        :param query:
        :param court:
        :param judge:
        :param party:
        :param neutral_citation:
        :param specific_keyword:
        :param order:
        :param date_from:
        :param date_to:
        :param page:
        :param page_size:
        :param show_unpublished: If True, both published and unpublished documents will be returned
        :param only_unpublished: If True, will only return published documents. Ignores the value of show_unpublished
        :param collections:
        :return:
        """
        module = "/judgments/search/search-v2.xqy"  # as stored on Marklogic
        search_parameters.show_unpublished = self.verify_show_unpublished(
            search_parameters.show_unpublished,
        )
        vars = json.dumps(search_parameters.as_marklogic_payload())
        return self.invoke(module, vars)

    def eval_xslt(
        self,
        judgment_uri: DocumentURIString,
        version_uri: Optional[DocumentURIString] = None,
        show_unpublished: bool = False,
        xsl_filename: str = DEFAULT_XSL_TRANSFORM,
        query: Optional[str] = None,
    ) -> requests.Response:
        marklogic_document_uri = self._format_uri_for_marklogic(judgment_uri)
        marklogic_document_version_uri = (
            MarkLogicDocumentVersionURIString(
                self._format_uri_for_marklogic(version_uri),
            )
            if version_uri
            else None
        )

        image_location = os.getenv("XSLT_IMAGE_LOCATION", "")

        show_unpublished = self.verify_show_unpublished(show_unpublished)

        vars: query_dicts.XsltTransformDict = {
            "uri": marklogic_document_uri,
            "version_uri": marklogic_document_version_uri,
            "show_unpublished": show_unpublished,
            "img_location": image_location,
            "xsl_filename": xsl_filename,
            "query": query,
        }

        return self._send_to_eval(vars, "xslt_transform.xqy")

    def accessible_judgment_transformation(
        self,
        judgment_uri: DocumentURIString,
        version_uri: Optional[DocumentURIString] = None,
        show_unpublished: bool = False,
    ) -> requests.Response:
        return self.eval_xslt(
            judgment_uri,
            version_uri,
            show_unpublished,
            xsl_filename=DEFAULT_XSL_TRANSFORM,
        )

    def original_judgment_transformation(
        self,
        judgment_uri: DocumentURIString,
        version_uri: Optional[DocumentURIString] = None,
        show_unpublished: bool = False,
    ) -> requests.Response:
        return self.eval_xslt(
            judgment_uri,
            version_uri,
            show_unpublished,
            xsl_filename="as-handed-down.xsl",
        )

    def get_property(self, judgment_uri: DocumentURIString, name: str) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetPropertyDict = {
            "uri": uri,
            "name": name,
        }
        return self._eval_and_decode(vars, "get_property.xqy")

    def get_property_as_node(self, judgment_uri: DocumentURIString, name: str) -> Optional[etree._Element]:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetPropertyAsNodeDict = {
            "uri": uri,
            "name": name,
        }
        value = self._eval_and_decode(vars, "get_property_as_node.xqy")
        if not value:
            return None
        return etree.fromstring(value)

    def get_version_annotation(self, judgment_uri: DocumentURIString) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetVersionAnnotationDict = {
            "uri": uri,
        }
        return self._eval_and_decode(vars, "get_version_annotation.xqy")

    def get_version_created_datetime(self, judgment_uri: DocumentURIString) -> datetime:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetVersionCreatedDict = {
            "uri": uri,
        }
        return datetime.strptime(
            self._eval_and_decode(vars, "get_version_created.xqy"),
            "%Y-%m-%dT%H:%M:%S.%f%z",
        )

    def set_property(
        self,
        judgment_uri: DocumentURIString,
        name: str,
        value: str,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.SetPropertyDict = {
            "uri": uri,
            "value": value,
            "name": name,
        }

        return self._send_to_eval(vars, "set_property.xqy")

    def set_property_as_node(
        self,
        judgment_uri: DocumentURIString,
        name: str,
        value: etree._Element,
    ) -> requests.Response:
        """Given a root node, set the value of the MarkLogic property for a document to the _contents_ of that root node. The root node itself is discarded."""
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.SetPropertyAsNodeDict = {
            "uri": uri,
            "value": etree.tostring(value).decode(),
            "name": name,
        }

        return self._send_to_eval(vars, "set_property_as_node.xqy")

    def set_boolean_property(
        self,
        judgment_uri: DocumentURIString,
        name: str,
        value: bool,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        string_value = "true" if value else "false"
        vars: query_dicts.SetBooleanPropertyDict = {
            "uri": uri,
            "value": string_value,
            "name": name,
        }
        return self._send_to_eval(vars, "set_boolean_property.xqy")

    def get_boolean_property(self, judgment_uri: DocumentURIString, name: str) -> bool:
        content = self.get_property(judgment_uri, name)
        return content == "true"

    def set_published(
        self,
        judgment_uri: DocumentURIString,
        published: bool,
    ) -> requests.Response:
        return self.set_boolean_property(judgment_uri, "published", published)

    def get_published(self, judgment_uri: DocumentURIString) -> bool:
        return self.get_boolean_property(judgment_uri, "published")

    def get_last_modified(self, judgment_uri: DocumentURIString) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.GetLastModifiedDict = {
            "uri": uri,
        }

        response = self._send_to_eval(vars, "get_last_modified.xqy")

        if not response.text:
            return ""

        content = str(decoder.MultipartDecoder.from_response(response).parts[0].text)
        return content

    def delete_judgment(self, judgment_uri: DocumentURIString) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.DeleteJudgmentDict = {"uri": uri}
        return self._send_to_eval(vars, "delete_judgment.xqy")

    def copy_document(
        self,
        old: DocumentURIString,
        new: DocumentURIString,
    ) -> requests.Response:
        old_uri = self._format_uri_for_marklogic(old)
        new_uri = self._format_uri_for_marklogic(new)

        vars: query_dicts.CopyDocumentDict = {
            "old_uri": old_uri,
            "new_uri": new_uri,
        }
        return self._send_to_eval(vars, "copy_document.xqy")

    def break_checkout(self, judgment_uri: DocumentURIString) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars: query_dicts.BreakJudgmentCheckoutDict = {
            "uri": uri,
        }
        return self._send_to_eval(vars, "break_judgment_checkout.xqy")

    def user_has_privilege(
        self,
        username: str,
        privilege_uri: MarkLogicPrivilegeURIString,
        privilege_action: str,
    ) -> requests.Response:
        vars: query_dicts.UserHasPrivilegeDict = {
            "user": username,
            "privilege_uri": privilege_uri,
            "privilege_action": privilege_action,
        }
        return self._send_to_eval(vars, "user_has_privilege.xqy")

    def user_can_view_unpublished_judgments(self, username: str) -> bool:
        if self.user_has_admin_role(username):
            return True

        check_privilege = self.user_has_privilege(
            username,
            MarkLogicPrivilegeURIString(
                "https://caselaw.nationalarchives.gov.uk/custom/privileges/can-view-unpublished-documents",
            ),
            "execute",
        )
        return get_single_string_from_marklogic_response(check_privilege).lower() == "true"

    def user_has_role(self, username: str, role: str) -> requests.Response:
        vars: query_dicts.UserHasRoleDict = {
            "user": username,
            "role": role,
        }
        return self._send_to_eval(vars, "user_has_role.xqy")

    def user_has_admin_role(self, username: str) -> bool:
        check_role = self.user_has_role(
            username,
            "admin",
        )
        multipart_data = decoder.MultipartDecoder.from_response(check_role)
        result = str(multipart_data.parts[0].text)
        return result.lower() == "true"

    def calculate_seconds_until_midnight(self, now: Optional[datetime] = None) -> int:
        """
        Get timedelta until end of day on the datetime passed, or current time.
        https://stackoverflow.com/questions/45986035/seconds-until-end-of-day-in-python
        """
        if not now:
            now = datetime.now()
        tomorrow = now + timedelta(days=1)
        difference = datetime.combine(tomorrow, time.min) - now

        return difference.seconds

    def verify_show_unpublished(self, show_unpublished: bool) -> bool:
        if show_unpublished and not self.user_can_view_unpublished_judgments(
            self.username,
        ):
            # The user cannot view unpublished judgments but is requesting to see them
            logging.warning(
                f"User {self.username} is attempting to view unpublished judgments but does not have that privilege.",
            )
            return False
        return show_unpublished

    def get_properties_for_search_results(
        self,
        judgment_uris: list[DocumentURIString],
    ) -> str:
        uris = [self._format_uri_for_marklogic(judgment_uri) for judgment_uri in judgment_uris]
        vars: query_dicts.GetPropertiesForSearchResultsDict = {"uris": uris}
        response = self._send_to_eval(vars, "get_properties_for_search_results.xqy")
        return get_single_string_from_marklogic_response(response)

    def search_and_decode_response(self, search_parameters: SearchParameters) -> bytes:
        response = self.advanced_search(search_parameters)
        return get_single_bytestring_from_marklogic_response(response)

    def search_judgments_and_decode_response(
        self,
        search_parameters: SearchParameters,
    ) -> bytes:
        search_parameters.collections = [DOCUMENT_COLLECTION_URI_JUDGMENT]
        return self.search_and_decode_response(search_parameters)

    def update_document_uri(self, old_uri: DocumentURIString, new_citation: NeutralCitationString) -> DocumentURIString:
        """
        Move the document at old_uri to the correct location based on the neutral citation
        The new neutral citation *must* not already exist (that is handled elsewhere)
        This might not be needed; changing the URI/neutral citation is vanishingly rare
        """
        return move.update_document_uri(old_uri, new_citation, api_client=self)

    def get_combined_stats_table(self) -> list[list[Any]]:
        """Run the combined statistics table xquery and return the result as a list of lists, each representing a table
        row."""
        results: list[list[Any]] = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval({}, "get_combined_stats_table.xqy"),
            ),
        )

        return results

    def get_highest_enrichment_version(self) -> tuple[int, int]:
        """This gets the highest enrichment version in the database,
        so if nothing has been enriched with the most recent version of enrichment,
        this won't reflect that change."""
        table = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    {},
                    "get_highest_enrichment_version.xqy",
                ),
            ),
        )

        return (int(table[1][1]), int(table[1][2]))

    def get_pending_enrichment_for_version(
        self,
        target_enrichment_version: tuple[int, int],
        target_parser_version: tuple[int, int],
        maximum_records: int = 1000,
    ) -> list[list[Any]]:
        """Retrieve documents which are not yet enriched with a given version."""
        vars: query_dicts.GetPendingEnrichmentForVersionDict = {
            "target_enrichment_major_version": target_enrichment_version[0],
            "target_enrichment_minor_version": target_enrichment_version[1],
            "target_parser_major_version": target_parser_version[0],
            "target_parser_minor_version": target_parser_version[1],
            "maximum_records": maximum_records,
        }
        results: list[list[Any]] = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    vars,
                    "get_pending_enrichment_for_version.xqy",
                ),
            ),
        )

        return results

    def get_recently_enriched(
        self,
    ) -> list[list[Any]]:
        """Retrieve documents which are not yet enriched with a given version."""
        results: list[list[Any]] = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    {},
                    "get_recently_enriched.xqy",
                ),
            ),
        )

        return results

    def get_highest_parser_version(self) -> tuple[int, int]:
        """This gets the highest parser version in the database, so if nothing has been parsed with the most recent version of the parser, this won't reflect that change."""
        table = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    {},
                    "get_highest_parser_version.xqy",
                ),
            ),
        )

        return (int(table[1][1]), int(table[1][2]))

    def get_pending_parse_for_version(
        self,
        target_version: tuple[int, int],
        maximum_records: int = 1000,
    ) -> list[list[Any]]:
        """Retrieve documents which are not yet parsed with a given version."""
        vars: query_dicts.GetPendingParseForVersionDict = {
            "target_major_version": target_version[0],
            "target_minor_version": target_version[1],
            "maximum_records": maximum_records,
        }
        results: list[list[Any]] = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    vars,
                    "get_pending_parse_for_version.xqy",
                ),
            ),
        )

        return results

    def get_recently_parsed(
        self,
    ) -> list[list[Any]]:
        """Retrieve documents which are not yet enriched with a given version."""
        results: list[list[Any]] = json.loads(
            get_single_string_from_marklogic_response(
                self._send_to_eval(
                    {},
                    "get_recently_parsed.xqy",
                ),
            ),
        )

        return results

    def get_missing_fclid(
        self,
        maximum_records: int = 50,
    ) -> list[str]:
        """Retrieve the URIs of published documents which do not have an identifier in the `fclid` schema."""
        vars: query_dicts.GetMissingFclidDict = {
            "maximum_records": maximum_records,
        }

        results: list[str] = get_multipart_strings_from_marklogic_response(
            self._send_to_eval(
                vars,
                "get_missing_fclid.xqy",
            )
        )

        return results

    def resolve_from_identifier_slug(
        self, identifier_slug: DocumentIdentifierSlug, published_only: bool = True
    ) -> IdentifierResolutions:
        """Given a PUI/EUI url, look up the precomputed slug and return the
        MarkLogic document URIs which match that slug. Multiple returns should be anticipated"""
        vars: query_dicts.ResolveFromIdentifierSlugDict = {
            "identifier_slug": identifier_slug,
            "published_only": int(published_only),
        }
        raw_results: list[str] = get_multipart_strings_from_marklogic_response(
            self._send_to_eval(
                vars,
                "resolve_from_identifier_slug.xqy",
            ),
        )
        return IdentifierResolutions.from_marklogic_output(raw_results)

    def resolve_from_identifier_value(
        self, identifier_value: DocumentIdentifierValue, published_only: bool = True
    ) -> IdentifierResolutions:
        """Given a PUI/EUI url, look up the precomputed slug and return the
        MarkLogic document URIs which match that slug. Multiple returns should be anticipated"""
        vars: query_dicts.ResolveFromIdentifierValueDict = {
            "identifier_value": identifier_value,
            "published_only": int(published_only),
        }
        raw_results: list[str] = get_multipart_strings_from_marklogic_response(
            self._send_to_eval(
                vars,
                "resolve_from_identifier_value.xqy",
            ),
        )
        return IdentifierResolutions.from_marklogic_output(raw_results)

    def get_next_document_sequence_number(self) -> int:
        """Increment the MarkLogic sequence number by one and return the value."""
        return int(self._eval_and_decode({}, "get_next_document_sequence_number.xqy"))
