import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import requests
from requests.auth import HTTPBasicAuth
from requests_toolbelt.multipart import decoder
import environ

from . import xml_tools

env = environ.Env()
RESULTS_PER_PAGE = 10
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))


class MarklogicAPIError(requests.HTTPError):
    pass


class MarklogicBadRequestError(MarklogicAPIError):
    pass


class MarklogicUnauthorizedError(MarklogicAPIError):
    pass


class MarklogicNotPermittedError(MarklogicAPIError):
    pass


class MarklogicResourceNotFoundError(MarklogicAPIError):
    pass


class MarklogicCommunicationError(MarklogicAPIError):
    pass


class MarklogicApiClient:

    http_error_classes = {
        400: MarklogicBadRequestError,
        401: MarklogicUnauthorizedError,
        403: MarklogicNotPermittedError,
        404: MarklogicResourceNotFoundError,
    }
    error_code_classes = {
        'XDMP-DOCNOTFOUND': MarklogicResourceNotFoundError
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

    def _path_to_request_url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

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
                response_body = response.content

            if new_error_class == self.default_http_error_class:
                # Attempt to decode the error code from the response
                error_code = xml_tools.get_error_code(response.content.decode('utf-8'))

                new_error_class = self.error_code_classes.get(
                    error_code, self.default_http_error_class
                )

            new_exception = new_error_class(
                "{}. Response body:\n{}".format(e, response_body)
            )
            new_exception.response = response
            raise new_exception

    def _format_uri(self, uri):
        return f"/{uri.lstrip('/')}.xml"

    def prepare_request_kwargs(
        self, method: str, path: str, body=None, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        kwargs = dict(url=self._path_to_request_url(path))
        if data is not None:
            data = {k: v for k, v in data.items() if v is not None}
            if method == "GET":
                kwargs["params"] = data
            else:
                kwargs["data"] = json.dumps(data)
        if body is not None:
            kwargs["data"] = body
        return kwargs

    def make_request(
        self,
        method: str,
        path: str,
        headers: Dict[str, Any],
        body: str = None,
        data: Dict[str, Any] = None,
    ) -> requests.Response:
        kwargs = self.prepare_request_kwargs(method, path, body, data)
        self.session.headers = headers
        response = self.session.request(method, **kwargs)
        # Raise relevant exception for an erroneous response
        self._raise_for_status(response)
        return response

    def GET(self, path: str, headers: Dict[str, Any], **data: Any) -> requests.Response:
        return self.make_request("GET", path, headers, data)

    def POST(
        self, path: str, headers: Dict[str, Any], **data: Any
    ) -> requests.Response:
        return self.make_request("POST", path, headers, data)

    def get_judgment_xml(self, judgment_uri, version_uri=None, show_unpublished=False) -> str:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        if version_uri:
            version_uri = f"/{version_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "get_judgment.xqy"
        )
        vars = {
            "uri": uri,
            "version_uri": version_uri,
            "show_unpublished": str(show_unpublished).lower()
        }

        response = self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )
        if not response.text:
            return ''

        multipart_data = decoder.MultipartDecoder.from_response(response)
        return multipart_data.parts[0].text

    def get_judgment_name(self, judgment_uri) -> str:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "get_metadata_name.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri":"{uri}"}}', accept_header="application/xml"
        )
        if not response.text:
            return ''

        multipart_data = decoder.MultipartDecoder.from_response(response)
        return multipart_data.parts[0].text

    def set_judgment_name(self, judgment_uri, content):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_metadata_name.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri":"{uri}", "content":"{content}"}}', accept_header="application/xml"
        )
        return response

    def set_judgment_date(self, judgment_uri, content):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_metadata_date.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri":"{uri}", "content":"{content}"}}', accept_header="application/xml"
        )
        return response

    def set_judgment_citation(self, judgment_uri, content):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_metadata_citation.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri":"{uri}", "content":"{content}"}}', accept_header="application/xml"
        )
        return response

    def set_judgment_court(self, judgment_uri, content):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_metadata_court.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri":"{uri}", "content":"{content}"}}', accept_header="application/xml"
        )
        return response

    def set_judgment_this_uri(self, judgment_uri):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        content_with_id = f"https://caselaw.nationalarchives.gov.uk/id/{judgment_uri.lstrip('/')}"
        content_without_id = f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}"
        content_with_xml = f"https://caselaw.nationalarchives.gov.uk/{judgment_uri.lstrip('/')}/data.xml"

        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_metadata_this_uri.xqy"
        )

        response = self.eval(
            xquery_path, vars=f'{{"uri": "{uri}", "content_with_id": "{content_with_id}", "content_without_id": "{content_without_id}", "content_with_xml": "{content_with_xml}"}}', accept_header="application/xml"
        )
        return response

    def save_judgment_xml(self, judgment_uri: str, judgment_xml: Element) -> requests.Response:
        xml = ElementTree.tostring(judgment_xml)

        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "update_judgment.xqy"
        )
        vars = {
            "uri": uri,
            "judgment": xml.decode("utf-8") ,
            "annotation": ""
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def insert_judgment_xml(self, judgment_uri: str, judgment_xml: Element) -> requests.Response:
        xml = ElementTree.tostring(judgment_xml)

        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "insert_judgment.xqy"
        )
        vars = {
            "uri": uri,
            "judgment": xml.decode("utf-8") ,
            "annotation": ""
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def list_judgment_versions(self, judgment_uri: str) -> requests.Response:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "list_judgment_versions.xqy"
        )
        vars = {
            "uri": uri
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def checkout_judgment(self, judgment_uri: str) -> requests.Response:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "checkout_judgment.xqy"
        )
        vars = {
            "uri": uri
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def checkin_judgment(self, judgment_uri: str) -> requests.Response:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "checkin_judgment.xqy"
        )
        vars = {
            "uri": uri
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def get_judgment_version(self, judgment_uri: str, version: int) -> requests.Response:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "get_judgment_version.xqy"
        )
        vars = {
            "uri": uri,
            "version": str(version)
        }

        return self.eval(
            xquery_path,
            vars=json.dumps(vars),
            accept_header="application/xml",
        )

    def eval(
        self, xquery_path, vars, accept_header="multipart/mixed"
    ):
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": accept_header,
        }
        data = {
            "xquery": Path(xquery_path).read_text(),
            "vars": vars,
        }
        path = f"LATEST/eval"
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
        path = f"LATEST/invoke"
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
        only_unpublished=False
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
        module = '/judgments/search/search.xqy' # as stored on Marklogic
        vars = json.dumps({
            "court": str(court or ""),
            "judge": str(judge or ""),
            "page": page,
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
        })

        return self.invoke(module, vars)

    def eval_xslt(self, judgment_uri, version_uri=None, show_unpublished=False, xsl_filename="judgment2.xsl") -> requests.Response:
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        if version_uri:
            version_uri = f"/{version_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(ROOT_DIR, "xquery", "xslt_transform.xqy")
        if os.getenv('XSLT_IMAGE_LOCATION'):
            image_location = os.getenv('XSLT_IMAGE_LOCATION')
        else:
            image_location = ""

        vars = json.dumps({
            "uri": uri,
            "version_uri": version_uri,
            "show_unpublished": str(show_unpublished).lower(),
            "img_location": image_location,
            "xsl_filename": xsl_filename
        })
        return self.eval(xquery_path, vars=vars, accept_header="application/xml")

    def accessible_judgment_transformation(self, judgment_uri, version_uri=None, show_unpublished=False):
        return self.eval_xslt(judgment_uri, version_uri, show_unpublished, xsl_filename="judgment2.xsl")

    def original_judgment_transformation(self, judgment_uri, version_uri=None, show_unpublished=False):
        return self.eval_xslt(judgment_uri, version_uri, show_unpublished, xsl_filename="judgment0.xsl")

    def get_property(self, judgment_uri, name):
        uri = self._format_uri(judgment_uri)
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "get_property.xqy"
        )
        vars = json.dumps({
            "uri": uri,
            "name": name,
        })
        response = self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )

        if not response.text:
            return ""

        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        return content

    def set_property(self, judgment_uri, name, value):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_property.xqy"
        )
        vars = json.dumps({
            "uri": uri,
            "value": value,
            "name": name,
        })
        return self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )

    def set_boolean_property(self, judgment_uri, name, value):
        uri = f"/{judgment_uri.lstrip('/')}.xml"
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "set_boolean_property.xqy"
        )
        string_value = "true" if value else "false"
        vars = json.dumps({
            "uri": uri,
            "value": string_value,
            "name": name,
        })
        return self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )

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
        uri = self._format_uri(judgment_uri)
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "get_last_modified.xqy"
        )
        vars = json.dumps({
            "uri": uri,
        })
        response = self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )

        if not response.text:
            return ""

        content = decoder.MultipartDecoder.from_response(response).parts[0].text
        return content

    def delete_judgment(self, judgment_uri):
        uri = self._format_uri(judgment_uri)
        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "delete_judgment.xqy"
        )
        vars = json.dumps({
            "uri": uri
        })
        self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )

    def copy_judgment(self, old, new):
        old_uri = self._format_uri(old)
        new_uri = self._format_uri(new)

        xquery_path = os.path.join(
            ROOT_DIR, "xquery", "copy_judgment.xqy"
        )
        vars = json.dumps({
            "old_uri": old_uri,
            "new_uri": new_uri,
        })
        return self.eval(
            xquery_path,
            vars=vars,
            accept_header="application/xml",
        )


api_client = MarklogicApiClient(
    host=env("MARKLOGIC_HOST"),
    username=env("MARKLOGIC_USER"),
    password=env("MARKLOGIC_PASSWORD"),
    use_https=env("MARKLOGIC_USE_HTTPS", default=False),
)