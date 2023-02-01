import json
import logging
import os
import re
import warnings
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import environ
import requests
from memoization import cached
from requests.auth import HTTPBasicAuth
from requests.structures import CaseInsensitiveDict
from requests_toolbelt.multipart import decoder

from . import xml_tools
from .content_hash import validate_content_hash
from .errors import MarklogicAPIError  # noqa: F401
from .errors import (
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
RESULTS_PER_PAGE = 10
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DEFAULT_XSL_TRANSFORM = "accessible-html.xsl"


def decode_multipart(response):
    """Decode a multipart response and return just the text inside it.
    Note that it is possible for multiple responses to be returned, if
    multiple top-level returns exist in the XQuery."""
    if not (response.content):
        return ""
    multipart_data = decoder.MultipartDecoder.from_response(response)
    part_count = len(multipart_data.parts)
    if part_count > 1:
        logging.warning(
            f"Throwing away multipart data ({part_count} items, expected 1)"
        )
    return multipart_data.parts[0].text


class MarklogicApiClient:

    http_error_classes = {
        400: MarklogicBadRequestError,
        401: MarklogicUnauthorizedError,
        403: MarklogicNotPermittedError,
        404: MarklogicResourceNotFoundError,
    }
    error_code_classes = {
        "XDMP-DOCNOTFOUND": MarklogicResourceNotFoundError,
        "XDMP-LOCKCONFLICT": MarklogicResourceLockedError,
        "DLS-UNMANAGED": MarklogicResourceUnmanagedError,
        "DLS-NOTCHECKEDOUT": MarklogicResourceNotCheckedOutError,
        "DLS-CHECKOUTCONFLICT": MarklogicCheckoutConflictError,
        "SEC-PRIVDNE": MarklogicNotPermittedError,
        "XDMP-VALIDATE.*": MarklogicValidationFailedError,
    }

    default_http_error_class = MarklogicCommunicationError

    def __init__(self, host: str, username: str, password: str, use_https: bool):
        self.host = host
        self.username = username
        self.password = password
        self.base_url = f"{'https' if use_https else 'http'}://{self.host}:8011"
        # Apply auth / common headers to the session
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)

    def _get_error_code_class(self, error_code):
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

    def _court_list_splitter(self, court_text: str) -> Set[str]:
        return set(court_text.lower().replace(" ", "").split(","))

    def _court_list(self, court_text: str) -> Optional[List[str]]:
        if not court_text.strip():
            return None
        alt_names = {
            "ewhc/qb": "ewhc/kb",
            "ewhc/kb": "ewhc/qb",
            "ewhc/scco": "ewhc/costs",
            "ewhc/costs": "ewhc/scco",
        }
        new_names = set()
        courts = self._court_list_splitter(court_text)
        for primary_name, secondary_name in alt_names.items():
            if primary_name in courts and secondary_name not in courts:
                new_names.add(secondary_name)
        return list(courts | new_names)

    def _raise_for_status(self, response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            new_error_class = self.http_error_classes.get(
                status_code, self.default_http_error_class
            )
            try:
                response_body = json.dumps(response.json(), indent=4)
            except requests.JSONDecodeError:
                response_body = response.text

            if new_error_class == self.default_http_error_class:
                # Attempt to decode the error code from the response
                error_code = xml_tools.get_error_code(response.content.decode("utf-8"))

                new_error_class = self._get_error_code_class(error_code)

            new_exception = new_error_class(
                "{}. Response body:\n{}".format(e, response_body)
            )
            new_exception.response = response
            raise new_exception

    def _format_uri_for_marklogic(self, uri):
        """
        Marklogic requires a document URI that begins with a slash `/` and ends in `.xml`.
        This method ensures any URI passed into the client matches this format.
        """
        return f"/{uri.lstrip('/').rstrip('/')}.xml"

    def _xquery_path(self, xquery_file_name):
        return os.path.join(ROOT_DIR, "xquery", xquery_file_name)

    def _send_to_eval(self, vars, xquery_file_name):
        return self.eval(
            self._xquery_path(xquery_file_name),
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def prepare_request_kwargs(
        self, method: str, path: str, body=None, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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
        data: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        kwargs = self.prepare_request_kwargs(method, path, body, data)
        self.session.headers = headers
        response = self.session.request(method, **kwargs)
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def GET(self, path: str, headers: Dict[str, Any], **data: Any) -> requests.Response:
        logging.warning("GET() is deprecated, use eval() or invoke()")
        return self.make_request("GET", path, headers, data)  # type: ignore

    def POST(
        self, path: str, headers: Dict[str, Any], **data: Any
    ) -> requests.Response:
        logging.warning("POST() is deprecated, use eval() or invoke()")
        return self.make_request("POST", path, headers, data)  # type: ignore

    def get_judgment_xml(
        self, judgment_uri, version_uri=None, show_unpublished=False
    ) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        show_unpublished = self.verify_show_unpublished(show_unpublished)
        if version_uri:
            version_uri = f"/{version_uri.lstrip('/')}.xml"
        vars = {
            "uri": uri,
            "version_uri": version_uri,
            "show_unpublished": str(show_unpublished).lower(),
        }

        response = self._send_to_eval(vars, "get_judgment.xqy")

        if not response.text:
            raise MarklogicNotPermittedError(
                "The document is not published and show_unpublished was not set"
            )

        return decode_multipart(response)

    def get_judgment_name(self, judgment_uri) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}

        response = self._send_to_eval(vars, "get_metadata_name.xqy")
        if not response.text:
            return ""

        return decode_multipart(response)

    def set_judgment_name(self, judgment_uri, content):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "content": content}

        return self._send_to_eval(vars, "set_metadata_name.xqy")

    def set_judgment_date(self, judgment_uri, content):
        warnings.warn(
            "set_judgment_date() is deprecated, use set_judgment_work_expression_date()",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.set_judgment_work_expression_date(judgment_uri, content)

    def set_judgment_work_expression_date(self, judgment_uri, content):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "content": content}

        return self._send_to_eval(vars, "set_metadata_work_expression_date.xqy")

    def set_judgment_citation(self, judgment_uri, content):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "content": content}

        return self._send_to_eval(vars, "set_metadata_citation.xqy")

    def set_judgment_court(self, judgment_uri, content):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "content": content}

        return self._send_to_eval(vars, "set_metadata_court.xqy")

    def set_judgment_this_uri(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        content_with_id = (
            f"https://caselaw.nationalarchives.gov.uk/id/{judgment_uri.lstrip('/')}"
        )
        content_without_id = (
            f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}"
        )
        content_with_xml = f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}/data.xml"
        vars = {
            "uri": uri,
            "content_with_id": content_with_id,
            "content_without_id": content_without_id,
            "content_with_xml": content_with_xml,
        }

        return self._send_to_eval(vars, "set_metadata_this_uri.xqy")

    def save_locked_judgment_xml(
        self, judgment_uri: str, judgment_xml: bytes, annotation=None
    ) -> requests.Response:
        """assumes the judgment is already locked, does not unlock/check in
        note this version assumes the XML is raw bytes, rather than a tree..."""
        validate_content_hash(judgment_xml)
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
            "judgment": judgment_xml.decode("utf-8"),
            "annotation": annotation or "edited by save_judgment_xml",
        }

        return self._send_to_eval(vars, "update_locked_judgment.xqy")

    def save_judgment_xml(
        self, judgment_uri: str, judgment_xml: Element, annotation=None
    ) -> requests.Response:
        """update_judgment uses dls:document-checkout-update-checkin as a single operation"""
        xml = ElementTree.tostring(judgment_xml)

        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
            "judgment": xml.decode("utf-8"),
            "annotation": annotation or "edited by save_judgment_xml",
        }

        return self._send_to_eval(vars, "update_judgment.xqy")

    def insert_judgment_xml(
        self, judgment_uri: str, judgment_xml: Element
    ) -> requests.Response:
        xml = ElementTree.tostring(judgment_xml)

        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "judgment": xml.decode("utf-8"), "annotation": ""}

        return self._send_to_eval(vars, "insert_judgment.xqy")

    def list_judgment_versions(self, judgment_uri: str) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}

        return self._send_to_eval(vars, "list_judgment_versions.xqy")

    def checkout_judgment(
        self, judgment_uri: str, annotation="", expires_at_midnight=False
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
            "annotation": annotation,
        }

        if expires_at_midnight:
            timeout = self.calculate_seconds_until_midnight()
            vars["timeout"] = timeout
        else:
            vars["timeout"] = -1

        return self._send_to_eval(vars, "checkout_judgment.xqy")

    def checkin_judgment(self, judgment_uri: str) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}

        return self._send_to_eval(vars, "checkin_judgment.xqy")

    def get_judgment_checkout_status(self, judgment_uri: str) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}

        return self._send_to_eval(vars, "get_judgment_checkout_status.xqy")

    def get_judgment_checkout_status_message(self, judgment_uri: str):
        """Return the annotation of the lock or `None` if there is no lock."""
        response = self.get_judgment_checkout_status(judgment_uri)
        if not response.content:
            return None
        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        if content == "":
            return None
        response_xml = ElementTree.fromstring(content)
        return response_xml.find(
            "dls:annotation", namespaces={"dls": "http://marklogic.com/xdmp/dls"}
        ).text  # type: ignore

    def get_judgment_version(
        self, judgment_uri: str, version: int
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri, "version": str(version)}

        return self._send_to_eval(vars, "get_judgment_version.xqy")

    def eval(self, xquery_path, vars, accept_header="multipart/mixed"):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": accept_header,
        }
        data = {
            "xquery": Path(xquery_path).read_text(),
            "vars": vars,
        }
        path = "LATEST/eval"
        response = self.session.request(
            "POST", url=self._path_to_request_url(path), headers=headers, data=data
        )
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def invoke(self, module, vars, accept_header="multipart/mixed"):
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
            "POST", url=self._path_to_request_url(path), headers=headers, data=data
        )
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def advanced_search(
        self,
        q=None,
        court=None,
        judge=None,
        party=None,
        neutral_citation=None,
        specific_keyword=None,
        order=None,
        date_from=None,
        date_to=None,
        page=1,
        page_size=RESULTS_PER_PAGE,
        show_unpublished=False,
        only_unpublished=False,
    ) -> requests.Response:
        """
        Performs a search on the entire document set.

        :param q:
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
        :return:
        """
        module = "/judgments/search/search-v2.xqy"  # as stored on Marklogic
        show_unpublished = self.verify_show_unpublished(show_unpublished)
        vars = json.dumps(
            {
                "court": self._court_list(court or ""),
                "judge": str(judge or ""),
                "page": max(1, int(page)),
                "page-size": int(page_size),
                "q": str(q or ""),
                "party": str(party or ""),
                "neutral_citation": str(neutral_citation or ""),
                "specific_keyword": str(specific_keyword or ""),
                "order": str(order or ""),
                "from": str(date_from or ""),
                "to": str(date_to or ""),
                "show_unpublished": str(show_unpublished).lower(),
                "only_unpublished": str(only_unpublished).lower(),
            }
        )
        return self.invoke(module, vars)

    def eval_xslt(
        self,
        judgment_uri,
        version_uri=None,
        show_unpublished=False,
        xsl_filename=DEFAULT_XSL_TRANSFORM,
    ) -> requests.Response:
        uri = self._format_uri_for_marklogic(judgment_uri)
        if version_uri:
            version_uri = self._format_uri_for_marklogic(version_uri)
        if os.getenv("XSLT_IMAGE_LOCATION"):
            image_location = os.getenv("XSLT_IMAGE_LOCATION")
        else:
            image_location = ""

        show_unpublished = self.verify_show_unpublished(show_unpublished)

        vars = {
            "uri": uri,
            "version_uri": version_uri,
            "show_unpublished": str(show_unpublished).lower(),
            "img_location": image_location,
            "xsl_filename": xsl_filename,
        }

        return self._send_to_eval(vars, "xslt_transform.xqy")

    def accessible_judgment_transformation(
        self, judgment_uri, version_uri=None, show_unpublished=False
    ):
        return self.eval_xslt(
            judgment_uri,
            version_uri,
            show_unpublished,
            xsl_filename=DEFAULT_XSL_TRANSFORM,
        )

    def original_judgment_transformation(
        self, judgment_uri, version_uri=None, show_unpublished=False
    ):
        return self.eval_xslt(
            judgment_uri,
            version_uri,
            show_unpublished,
            xsl_filename="as-handed-down.xsl",
        )

    def get_property(self, judgment_uri, name):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
            "name": name,
        }
        response = self._send_to_eval(vars, "get_property.xqy")

        if not response.text:
            return ""

        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        return content

    def set_property(self, judgment_uri, name, value):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        vars = {
            "uri": uri,
            "value": value,
            "name": name,
        }

        return self._send_to_eval(vars, "set_property.xqy")

    def set_boolean_property(self, judgment_uri, name, value):
        uri = self._format_uri_for_marklogic(judgment_uri)
        string_value = "true" if value else "false"
        vars = {
            "uri": uri,
            "value": string_value,
            "name": name,
        }
        return self._send_to_eval(vars, "set_boolean_property.xqy")

    def get_boolean_property(self, judgment_uri, name):
        content = self.get_property(judgment_uri, name)
        return content == "true"

    def set_published(self, judgment_uri, published=False):
        return self.set_boolean_property(judgment_uri, "published", published)

    def set_sensitive(self, judgment_uri, sensitive=False):
        return self.set_boolean_property(judgment_uri, "sensitive", sensitive)

    def set_supplemental(self, judgment_uri, supplemental=False):
        return self.set_boolean_property(judgment_uri, "supplemental", supplemental)

    def set_anonymised(self, judgment_uri, anonymised=False):
        return self.set_boolean_property(judgment_uri, "anonymised", anonymised)

    def get_published(self, judgment_uri):
        return self.get_boolean_property(judgment_uri, "published")

    def get_sensitive(self, judgment_uri):
        return self.get_boolean_property(judgment_uri, "sensitive")

    def get_supplemental(self, judgment_uri):
        return self.get_boolean_property(judgment_uri, "supplemental")

    def get_anonymised(self, judgment_uri):
        return self.get_boolean_property(judgment_uri, "anonymised")

    def get_last_modified(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
        }

        response = self._send_to_eval(vars, "get_last_modified.xqy")

        if not response.text:
            return ""

        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        return content

    def delete_judgment(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}
        return self._send_to_eval(vars, "delete_judgment.xqy")

    def copy_judgment(self, old, new):
        old_uri = self._format_uri_for_marklogic(old)
        new_uri = self._format_uri_for_marklogic(new)

        vars = {
            "old_uri": old_uri,
            "new_uri": new_uri,
        }
        return self._send_to_eval(vars, "copy_judgment.xqy")

    def break_checkout(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {
            "uri": uri,
        }
        return self._send_to_eval(vars, "break_judgment_checkout.xqy")

    def user_has_privilege(self, username, privilege_uri, privilege_action):
        vars = {
            "user": username,
            "privilege_uri": privilege_uri,
            "privilege_action": privilege_action,
        }
        return self._send_to_eval(vars, "user_has_privilege.xqy")

    @cached
    def user_can_view_unpublished_judgments(self, username):
        if self.user_has_admin_role(username):
            return True

        check_privilege = self.user_has_privilege(
            username,
            "https://caselaw.nationalarchives.gov.uk/custom/privileges/can-view-unpublished-documents",
            "execute",
        )
        return decode_multipart(check_privilege).lower() == "true"

    def user_has_role(self, username, role):
        vars = {
            "user": username,
            "role": role,
        }
        return self._send_to_eval(vars, "user_has_role.xqy")

    @cached
    def user_has_admin_role(self, username):
        check_role = self.user_has_role(
            username,
            "admin",
        )
        multipart_data = decoder.MultipartDecoder.from_response(check_role)
        result = multipart_data.parts[0].text
        return result.lower() == "true"

    def calculate_seconds_until_midnight(self, now=None):
        """
        Get timedelta until end of day on the datetime passed, or current time.
        https://stackoverflow.com/questions/45986035/seconds-until-end-of-day-in-python
        """
        if not now:
            now = datetime.now()
        tomorrow = now + timedelta(days=1)
        difference = datetime.combine(tomorrow, time.min) - now

        return difference.seconds

    def verify_show_unpublished(self, show_unpublished):
        if show_unpublished and not self.user_can_view_unpublished_judgments(
            self.username
        ):
            # The user cannot view unpublished judgments but is requesting to see them
            logging.warning(
                f"User {self.username} is attempting to view unpublished judgments but does not have that privilege."
            )
            return False
        return show_unpublished

    def get_judgment_citation(self, judgment_uri) -> str:
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}

        response = self._send_to_eval(vars, "get_metadata_citation.xqy")
        return decode_multipart(response)

    def get_judgment_court(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}
        response = self._send_to_eval(vars, "get_metadata_court.xqy")
        return decode_multipart(response)

    def get_judgment_work_date(self, judgment_uri):
        uri = self._format_uri_for_marklogic(judgment_uri)
        vars = {"uri": uri}
        response = self._send_to_eval(vars, "get_metadata_work_date.xqy")
        return decode_multipart(response)

    def get_properties_for_search_results(self, judgment_uris):
        uris = [
            self._format_uri_for_marklogic(judgment_uri)
            for judgment_uri in judgment_uris
        ]
        vars = {"uris": uris}
        response = self._send_to_eval(vars, "get_properties_for_search_results.xqy")
        return decode_multipart(response)


api_client = MarklogicApiClient(
    host=env("MARKLOGIC_HOST", default=None),
    username=env("MARKLOGIC_USER", default=None),
    password=env("MARKLOGIC_PASSWORD", default=None),
    use_https=env("MARKLOGIC_USE_HTTPS", default=False),
)
