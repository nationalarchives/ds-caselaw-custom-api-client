from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, fields

from lxml import etree

from caselawclient.models.documents.metrics.base import Metric
from caselawclient.models.documents.metrics.types.submissions_before_first_publish import (
    SubmissionsBeforeFirstPublishMetric,
)
from caselawclient.models.documents.metrics.types.tdr_to_first_publish import TdrToFirstPublishMetric
from caselawclient.models.documents.metrics.types.tdr_to_latest_publish import TdrToLatestPublishMetric
from caselawclient.xml_helpers import Element


@dataclass(slots=True)
class DocumentMetrics:
    """Typed reporting metrics stored in the document's ``metrics`` property."""

    tdr_to_first_publish: TdrToFirstPublishMetric = field(default_factory=TdrToFirstPublishMetric)
    tdr_to_latest_publish: TdrToLatestPublishMetric = field(default_factory=TdrToLatestPublishMetric)
    submissions_before_first_publish: SubmissionsBeforeFirstPublishMetric = field(
        default_factory=SubmissionsBeforeFirstPublishMetric
    )

    def __iter__(self) -> Iterator[Metric]:
        for metric_field in fields(self):
            yield getattr(self, metric_field.name)

    @property
    def as_etree(self) -> Element:
        root = etree.Element("metrics")
        for metric in self:
            if metric.value is not None:
                etree.SubElement(root, metric.key).text = str(metric.value)
        return root

    @classmethod
    def from_etree(cls, root: Element | None) -> DocumentMetrics:
        """Load stored metrics; an absent property means no metrics have been recorded."""
        result = cls()
        if root is None:
            return result
        if root.tag != "metrics":
            raise ValueError("Expected a metrics property")
        registered = {metric.key: metric for metric in result}
        seen: set[str] = set()
        for child in root:
            if child.tag not in registered:
                raise ValueError(f"Unknown metric: {child.tag!r}")
            if child.tag in seen:
                raise ValueError(f"Duplicate metric: {child.tag!r}")
            seen.add(child.tag)
            if len(child):
                raise ValueError(f"Expected an integer value for {child.tag!r}")
            try:
                registered[child.tag].value = int(child.text or "")
            except ValueError as exc:
                raise ValueError(f"Invalid value for {child.tag!r}: {child.text!r}") from exc
        return result
