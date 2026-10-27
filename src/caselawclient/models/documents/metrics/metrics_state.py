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
FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY = "first_submission_tdr_receipt_datetime"
LATEST_SUBMISSION_PROPERTY = "latest_submission_datetime"
SUBMISSION_AFTER_PUBLICATION_PROPERTY = "first_submission_after_latest_publication_datetime"
SUBMISSION_AFTER_PUBLICATION_TDR_RECEIPT_PROPERTY = "first_submission_after_latest_publication_tdr_receipt_datetime"
DLS_NAMESPACE = "{http://marklogic.com/xdmp/dls}"


@dataclass
class MetricsState:
    """Stored properties and version history used to calculate reporting updates."""

    properties: Element
    version_types: list[VersionType] | None
    signature: str = ""

    @classmethod
    def for_new_document(cls) -> "MetricsState":
        return cls(etree.Element("properties"), [])

    @classmethod
    def from_etree(cls, root: Element) -> "MetricsState":
        properties = root.find("properties")
        if properties is None:
            raise ValueError("Expected document metrics state with properties")
        return cls(
            properties, cls._version_types(root.find(f"{DLS_NAMESPACE}document-history")), root.attrib["signature"]
        )

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

    def _tdr_receipt_datetime(self) -> datetime | None:
        value = self.properties.findtext("transfer-received-at")
        if not value:
            return None
        try:
            return require_aware_utc(isoparse(value), name="transfer-received-at")
        except (ValueError, OverflowError):
            return None

    @property
    def has_ever_been_published(self) -> bool:
        return bool(
            self.properties.findtext("first_published_datetime")
            or self.properties.findtext("latest_published_datetime")
            or self.properties.findtext("published") == "true"
        )

    def submission_properties(self, now: datetime) -> dict[str, datetime | None]:
        """Calculate submission date updates.

        The historically named ``first_submission_datetime`` and
        ``latest_submission_datetime`` properties record ingestion/save times,
        not timestamps supplied by TDR. Keep those names for compatibility.
        """
        now = require_aware_utc(now, name="now")
        updates: dict[str, datetime | None] = {}
        if self._is_first_submission():
            updates[FIRST_SUBMISSION_PROPERTY] = now
            tdr_received_at = self._tdr_receipt_datetime()
            if tdr_received_at:
                updates[FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY] = tdr_received_at
        updates[LATEST_SUBMISSION_PROPERTY] = now
        if self._is_first_submission_after_publication():
            updates[SUBMISSION_AFTER_PUBLICATION_PROPERTY] = now
            # Replace the previous cycle's marker; clear it if the new receipt
            # time is absent or invalid so it cannot be reused accidentally.
            updates[SUBMISSION_AFTER_PUBLICATION_TDR_RECEIPT_PROPERTY] = self._tdr_receipt_datetime()
        return updates

    def _is_first_submission(self) -> bool:
        return (
            not self.properties.findtext(FIRST_SUBMISSION_PROPERTY)
            and self.version_types is not None
            and VersionType.SUBMISSION not in self.version_types
        )

    def _is_first_submission_after_publication(self) -> bool:
        return self.has_ever_been_published and not self.properties.findtext(SUBMISSION_AFTER_PUBLICATION_PROPERTY)

    def publication_dates(self, now: datetime) -> dict[str, datetime | None]:
        """Calculate publication date updates."""
        now = require_aware_utc(now, name="now")
        updates: dict[str, datetime | None] = {}
        first_published = self.properties.findtext("first_published_datetime")
        # Match the existing get_datetime_property()/publish() behaviour, including empty values.
        if not first_published:
            updates["first_published_datetime"] = now
        else:
            require_aware_utc(isoparse(first_published), name="first_published_datetime")
        tdr_received_at = self._tdr_receipt_datetime()
        if self.has_ever_been_published:
            if self.properties.findtext(SUBMISSION_AFTER_PUBLICATION_PROPERTY) and not self.properties.findtext(
                SUBMISSION_AFTER_PUBLICATION_TDR_RECEIPT_PROPERTY
            ):
                updates[SUBMISSION_AFTER_PUBLICATION_TDR_RECEIPT_PROPERTY] = tdr_received_at
        elif self._has_submission() and not self.properties.findtext(FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY):
            updates[FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY] = tdr_received_at
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
        receipt_marker = self.properties.find(FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY)
        tdr_receipt = receipt_marker.text if receipt_marker is not None else None
        if not tdr_receipt and self._has_submission():
            tdr_receipt = self.properties.findtext("transfer-received-at")
        metrics.tdr_to_first_publish.value = self._duration_seconds(tdr_receipt, now)
        metrics.submissions_before_first_publish.value = (
            self.version_types.count(VersionType.SUBMISSION) if self.version_types is not None else None
        )

    def _set_latest_publication_metric(self, metrics: DocumentMetrics, now: datetime) -> None:
        has_resubmission = bool(self.properties.findtext(SUBMISSION_AFTER_PUBLICATION_PROPERTY))
        if self.has_ever_been_published:
            start = None
            if has_resubmission:
                receipt_marker = self.properties.find(SUBMISSION_AFTER_PUBLICATION_TDR_RECEIPT_PROPERTY)
                start = (
                    receipt_marker.text
                    if receipt_marker is not None and receipt_marker.text
                    else self.properties.findtext("transfer-received-at")
                )
        else:
            receipt_marker = self.properties.find(FIRST_SUBMISSION_TDR_RECEIPT_PROPERTY)
            start = receipt_marker.text if receipt_marker is not None else None
            if not start and self._has_submission():
                start = self.properties.findtext("transfer-received-at")
        metrics.tdr_to_latest_publish.value = self._duration_seconds(start, now)

    def _has_submission(self) -> bool:
        return bool(self.properties.findtext(FIRST_SUBMISSION_PROPERTY)) or (
            self.version_types is not None and VersionType.SUBMISSION in self.version_types
        )
