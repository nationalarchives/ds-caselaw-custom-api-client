import json
from dataclasses import dataclass
from datetime import datetime

from dateutil.parser import isoparse
from lxml import etree

from caselawclient.models.documents.metrics.registry import DocumentMetrics
from caselawclient.models.documents.versions import VersionType
from caselawclient.models.utilities.dates import require_aware_utc
from caselawclient.xml_helpers import Element

FIRST_SUBMISSION_PROPERTY = "first_submission_datetime"
LATEST_SUBMISSION_PROPERTY = "latest_submission_datetime"
SUBMISSION_AFTER_PUBLICATION_PROPERTY = "first_submission_after_latest_publication_datetime"
DLS_NAMESPACE = "{http://marklogic.com/xdmp/dls}"


@dataclass
class MetricsState:
    """Stored properties and version history used to calculate reporting updates."""

    properties: Element
    version_types: list[VersionType] | None

    @classmethod
    def for_new_document(cls) -> "MetricsState":
        return cls(etree.Element("properties"), [])

    @classmethod
    def from_etree(cls, root: Element) -> "MetricsState":
        properties = root.find("properties")
        if properties is None:
            raise ValueError("Expected document metrics state with properties")
        return cls(properties, cls._version_types(root.find(f"{DLS_NAMESPACE}document-history")))

    @staticmethod
    def _version_types(history: Element | None) -> list[VersionType] | None:
        """Unknown annotations or incomplete history cannot give an accurate count."""
        if history is None:
            return None
        versions = history.findall(f"{DLS_NAMESPACE}version")
        try:
            numbers = sorted(int(version.findtext(f"{DLS_NAMESPACE}version-id", "")) for version in versions)
            if not numbers or numbers != list(range(1, len(numbers) + 1)):
                return None
            return [
                VersionType(json.loads(version.findtext(f"{DLS_NAMESPACE}annotation", ""))["type"])
                for version in versions
            ]
        except (ValueError, TypeError, KeyError):
            return None

    @staticmethod
    def _duration_seconds(start: str | None, end: datetime) -> int | None:
        if not start:
            return None
        try:
            duration = (end - require_aware_utc(isoparse(start), name="submission time")).total_seconds()
        except (ValueError, OverflowError):
            return None
        return int(duration) if duration >= 0 else None

    @property
    def has_ever_been_published(self) -> bool:
        return bool(
            self.properties.findtext("first_published_datetime")
            or self.properties.findtext("latest_published_datetime")
            or self.properties.findtext("published") == "true"
        )

    def submission_properties(self, now: datetime) -> dict[str, datetime]:
        """Calculate date updates for this submission."""
        now = require_aware_utc(now, name="now")
        updates = {}
        if self._is_first_submission():
            updates[FIRST_SUBMISSION_PROPERTY] = now
        updates[LATEST_SUBMISSION_PROPERTY] = now
        if self._is_first_submission_after_publication():
            updates[SUBMISSION_AFTER_PUBLICATION_PROPERTY] = now
        return updates

    def _is_first_submission(self) -> bool:
        return (
            not self.properties.findtext(FIRST_SUBMISSION_PROPERTY)
            and self.version_types is not None
            and VersionType.SUBMISSION not in self.version_types
        )

    def _is_first_submission_after_publication(self) -> bool:
        return self.has_ever_been_published and not self.properties.findtext(SUBMISSION_AFTER_PUBLICATION_PROPERTY)

    def publication_dates(self, now: datetime) -> dict[str, datetime]:
        """Calculate publication date updates."""
        now = require_aware_utc(now, name="now")
        updates = {}
        first_published = self.properties.findtext("first_published_datetime")
        # Match the existing get_datetime_property()/publish() behaviour, including empty values.
        if not first_published:
            updates["first_published_datetime"] = now
        else:
            require_aware_utc(isoparse(first_published), name="first_published_datetime")
        updates["latest_published_datetime"] = now
        return updates

    def publication_metrics(self, now: datetime) -> DocumentMetrics:
        """Calculate durations/counts."""
        now = require_aware_utc(now, name="now")
        metrics = DocumentMetrics.from_etree(self.properties.find("metrics"))
        if not self.has_ever_been_published:
            self._set_first_publication_metrics(metrics, now)
        self._set_latest_publication_metric(metrics, now)
        return metrics

    def _set_first_publication_metrics(self, metrics: DocumentMetrics, now: datetime) -> None:
        metrics.tdr_to_first_publish.value = self._duration_seconds(
            self.properties.findtext(FIRST_SUBMISSION_PROPERTY), now
        )
        metrics.submissions_before_first_publish.value = (
            self.version_types.count(VersionType.SUBMISSION) if self.version_types is not None else None
        )

    def _set_latest_publication_metric(self, metrics: DocumentMetrics, now: datetime) -> None:
        submission_property = (
            SUBMISSION_AFTER_PUBLICATION_PROPERTY if self.has_ever_been_published else FIRST_SUBMISSION_PROPERTY
        )
        metrics.tdr_to_latest_publish.value = self._duration_seconds(self.properties.findtext(submission_property), now)
