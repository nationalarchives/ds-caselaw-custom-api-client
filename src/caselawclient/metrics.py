from datetime import UTC, date, datetime, time, timedelta
from itertools import pairwise
from typing import Literal, TypedDict

MetricName = Literal["tdr_to_first_publish", "tdr_to_latest_publish", "submissions_before_first_publish"]
MetricBucketing = Literal["daily", "monthly"]

METRIC_DATE_PROPERTIES = {
    "tdr_to_first_publish": "first_published_datetime",
    "tdr_to_latest_publish": "latest_published_datetime",
    "submissions_before_first_publish": "first_published_datetime",
}


class MetricStatistics(TypedDict):
    count: int
    sum: int
    mean: float | None
    median: float | None


class MetricBucket(TypedDict):
    label: str
    start: str
    end: str


def get_metric_buckets(start_date: date, end_date: date, bucketing: MetricBucketing) -> list[MetricBucket]:
    """Build buckets clipped to the requested date range."""
    if type(start_date) is not date or type(end_date) is not date:
        raise ValueError("start_date and end_date must be dates, not datetimes")
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")
    if bucketing not in ("daily", "monthly"):
        raise ValueError("bucketing must be daily or monthly")

    if bucketing == "daily":
        boundaries = [start_date + timedelta(days=offset) for offset in range((end_date - start_date).days)]
    else:
        boundaries = [start_date]
        first_month = start_date.year * 12 + start_date.month - 1
        last_month = end_date.year * 12 + end_date.month - 1
        for month in range(first_month + 1, last_month + 1):
            year, month_index = divmod(month, 12)
            boundary = date(year, month_index + 1, 1)
            if boundary < end_date:
                boundaries.append(boundary)
    boundaries.append(end_date)
    return [
        {
            "label": start.isoformat() if bucketing == "daily" else start.isoformat()[:7],
            "start": datetime.combine(start, time.min, tzinfo=UTC).isoformat(),
            "end": datetime.combine(end, time.min, tzinfo=UTC).isoformat(),
        }
        for start, end in pairwise(boundaries)
    ]
