import datetime
from functools import cached_property
from typing import Optional

from ds_caselaw_utils import courts, neutral_url
from ds_caselaw_utils.courts import CourtNotFoundException
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


class CannotPublishUnpublishableJudgment(Exception):
    pass


class Judgment:
    def __init__(self, uri: str, api_client: MarklogicApiClient):
        self.uri = uri.strip("/")
        self.api_client = api_client
        if not self.judgment_exists():
            raise JudgmentNotFoundError(f"Judgment {self.uri} does not exist")

    def judgment_exists(self) -> bool:
        return self.api_client.judgment_exists(self.uri)

    @property
    def public_uri(self) -> str:
        return "https://caselaw.nationalarchives.gov.uk/{uri}".format(uri=self.uri)

    @cached_property
    def neutral_citation(self) -> str:
        return self.api_client.get_judgment_citation(self.uri)

    @cached_property
    def name(self) -> str:
        return self.api_client.get_judgment_name(self.uri)

    @cached_property
    def court(self) -> str:
        return self.api_client.get_judgment_court(self.uri)

    @cached_property
    def judgment_date_as_string(self) -> str:
        return self.api_client.get_judgment_work_date(self.uri)

    @cached_property
    def judgment_date_as_date(self) -> datetime.date:
        return datetime.datetime.strptime(
            self.judgment_date_as_string, "%Y-%m-%d"
        ).date()

    @cached_property
    def is_published(self) -> bool:
        return self.api_client.get_published(self.uri)

    @cached_property
    def is_held(self) -> bool:
        return self.api_client.get_property(self.uri, "editor-hold") == "true"

    @cached_property
    def is_sensitive(self) -> bool:
        return self.api_client.get_sensitive(self.uri)

    @cached_property
    def is_anonymised(self) -> bool:
        return self.api_client.get_anonymised(self.uri)

    @cached_property
    def has_supplementary_materials(self) -> bool:
        return self.api_client.get_supplemental(self.uri)

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
    def is_parked(self) -> bool:
        if "parked" in self.uri:
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
    def has_valid_court(self) -> bool:
        try:
            return bool(courts.get_by_code(self.court))
        except CourtNotFoundException:
            return False

    # attribute name, value which passes validation, error message
    VALIDATION_ATTRIBUTES: list[tuple[str, bool, str]] = [
        (
            "is_failure",
            False,
            "This judgment has failed to parse",
        ),
        (
            "is_parked",
            False,
            "This judgment is currently parked at a temporary URI",
        ),
        (
            "is_held",
            False,
            "This judgment is currently on hold",
        ),
        (
            "has_name",
            True,
            "This judgment has no name",
        ),
        (
            "has_ncn",
            True,
            "This judgment has no neutral citation number",
        ),
        (
            "has_valid_ncn",
            True,
            "The neutral citation number of this judgment is not valid",
        ),
        (
            "has_valid_court",
            True,
            "The court is not valid",
        ),
    ]

    @cached_property
    def is_publishable(self) -> bool:
        # If there are any validation failures, there will be no messages in the list.
        # An empty list (which is falsy) therefore means the judgment can be published safely.
        return not self.validation_failure_messages

    @cached_property
    def validation_failure_messages(self) -> list[str]:
        exception_list = []
        for function_name, pass_value, message in self.VALIDATION_ATTRIBUTES:
            if getattr(self, function_name) != pass_value:
                exception_list.append(message)
        return sorted(exception_list)

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
