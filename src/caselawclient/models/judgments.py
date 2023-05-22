import datetime
from functools import cached_property
from typing import Callable, Optional, TypedDict, Union

from ds_caselaw_utils import neutral_url
from requests_toolbelt.multipart import decoder

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import JudgmentNotFoundError

from .utilities import VersionsDict, get_judgment_root, render_versions
from .utilities.aws import (
    generate_docx_url,
    generate_pdf_url,
    notify_changed,
    publish_documents,
    unpublish_documents,
    uri_for_s3,
)

JUDGMENT_STATUS_HOLD = "On hold"
JUDGMENT_STATUS_PUBLISHED = "Published"
JUDGMENT_STATUS_IN_PROGRESS = "In progress"


class MarkLogicAttributeDict(TypedDict):
    getter: Callable[[str], Union[str, bool]]
    setter: None


MarkLogicValueType = Union[str, bool]


class CannotPublishUnpublishableJudgment(Exception):
    pass


class Judgment:
    marklogic_attribute_map: dict[str, MarkLogicAttributeDict]
    values_store: dict[str, MarkLogicValueType]

    uri: str
    api_client: MarklogicApiClient

    # These definitions make sure that downstream users of this class can rely on the types of attributes.
    name: str
    neutral_citation: str
    court: str
    judgment_date_as_string: str
    is_published: bool
    is_sensitive: bool
    is_anonymised: bool
    has_supplementary_materials: bool

    def __init__(self, uri: str, api_client: MarklogicApiClient):
        self.__dict__["uri"] = uri.strip("/")
        self.__dict__["api_client"] = api_client
        self.__dict__["values_store"] = {}

        if not self.judgment_exists():
            raise JudgmentNotFoundError(f"Judgment {self.uri} does not exist")

        # Callables for setter accept a single argument of the judgment URI
        self.__dict__["marklogic_attribute_map"] = {
            "name": {
                "getter": self.api_client.get_judgment_name,
                "setter": None,
            },
            "neutral_citation": {
                "getter": self.api_client.get_judgment_citation,
                "setter": None,
            },
            "court": {
                "getter": self.api_client.get_judgment_court,
                "setter": None,
            },
            "judgment_date_as_string": {
                "getter": self.api_client.get_judgment_work_date,
                "setter": None,
            },
            "is_published": {
                "getter": self.api_client.get_published,
                "setter": None,
            },
            "is_sensitive": {
                "getter": self.api_client.get_sensitive,
                "setter": None,
            },
            "is_anonymised": {
                "getter": self.api_client.get_anonymised,
                "setter": None,
            },
            "has_supplementary_materials": {
                "getter": self.api_client.get_supplemental,
                "setter": None,
            },
        }

    def judgment_exists(self) -> bool:
        return self.api_client.judgment_exists(self.uri)

    def __getattr__(self, attr_name: str) -> MarkLogicValueType:
        if attr_name not in self.marklogic_attribute_map:
            raise AttributeError

        attribute = self.marklogic_attribute_map[attr_name]

        if attr_name not in self.values_store:
            self.values_store[attr_name] = attribute["getter"](self.uri)

        return self.values_store[attr_name]

    def __setattr__(self, attr_name: str, value: MarkLogicValueType) -> None:
        if attr_name not in self.marklogic_attribute_map:
            raise AttributeError

        self.__dict__["values_store"][attr_name] = value

    @property
    def public_uri(self) -> str:
        return "https://caselaw.nationalarchives.gov.uk/{uri}".format(uri=self.uri)

    @cached_property
    def judgment_date_as_date(self) -> datetime.date:
        return datetime.datetime.strptime(
            self.judgment_date_as_string, "%Y-%m-%d"
        ).date()

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

    def content_as_xml(self) -> str:
        return self.api_client.get_judgment_xml(self.uri, show_unpublished=True)

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
    def is_editable(self) -> bool:
        if "error" in self._get_root():
            return False
        return True

    def _get_root(self) -> str:
        return get_judgment_root(self.content_as_xml())

    @cached_property
    def has_name(self) -> bool:
        if not self.name:
            return False

        return True

    @cached_property
    def has_ncn(self) -> bool:
        if not self.neutral_citation:
            return False

        return True

    @cached_property
    def has_valid_ncn(self) -> bool:
        # The checks that we can convert an NCN to a URI using the function from utils
        if not self.has_ncn or not neutral_url(self.neutral_citation):
            return False

        return True

    @cached_property
    def has_court(self) -> bool:
        if not self.court:
            return False

        return True

    @cached_property
    def is_publishable(self) -> bool:
        if (
            self.is_held
            or not self.has_name
            or not self.has_ncn
            or not self.has_valid_ncn
            or not self.has_court
        ):
            return False

        return True

    @property
    def status(self) -> str:
        if self.is_published:
            return JUDGMENT_STATUS_PUBLISHED

        if self.is_held:
            return JUDGMENT_STATUS_HOLD

        return JUDGMENT_STATUS_IN_PROGRESS

    def publish(self) -> None:
        if not self.is_publishable:
            raise CannotPublishUnpublishableJudgment

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
