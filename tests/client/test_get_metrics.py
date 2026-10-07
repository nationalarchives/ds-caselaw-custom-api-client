import json
from datetime import UTC, date, datetime
from typing import Any
from unittest.mock import patch

import pytest

from caselawclient.Client import MarklogicApiClient
from caselawclient.errors import MarklogicNotPermittedError
from caselawclient.metrics import get_metric_buckets
from caselawclient.search_parameters import SearchParameters


@pytest.mark.parametrize(
    ("bucketing", "start", "end", "labels", "bounds"),
    [
        (
            "daily",
            date(2024, 2, 28),
            date(2024, 3, 1),
            ["2024-02-28", "2024-02-29"],
            ["2024-02-28", "2024-02-29", "2024-03-01"],
        ),
        (
            "monthly",
            date(2025, 12, 15),
            date(2026, 2, 3),
            ["2025-12", "2026-01", "2026-02"],
            ["2025-12-15", "2026-01-01", "2026-02-01", "2026-02-03"],
        ),
        ("monthly", date(2026, 1, 1), date(2026, 2, 1), ["2026-01"], ["2026-01-01", "2026-02-01"]),
    ],
)
def test_bucket_boundaries(bucketing, start, end, labels, bounds):
    buckets = get_metric_buckets(start, end, bucketing)
    assert [bucket["label"] for bucket in buckets] == labels
    assert [bucket["start"] for bucket in buckets] == [f"{day}T00:00:00+00:00" for day in bounds[:-1]]
    assert [bucket["end"] for bucket in buckets] == [f"{day}T00:00:00+00:00" for day in bounds[1:]]


@pytest.mark.parametrize(
    ("metric", "date_property"),
    [
        ("tdr_to_first_publish", "first_published_datetime"),
        ("tdr_to_latest_publish", "latest_published_datetime"),
        ("submissions_before_first_publish", "first_published_datetime"),
    ],
)
def test_metrics_reuses_search_parameters_without_mutating_them(metric, date_property):
    client = MarklogicApiClient("", "", "", False)
    parameters = SearchParameters(court="EWHC/QB", date_from="2020-01-01", show_unpublished=True, page=3, order="date")
    original = parameters.as_marklogic_payload()
    expected = {"2026-01": {"count": 2, "sum": 3, "mean": 1.5, "median": 1.5}}
    with (
        patch.object(client, "_eval_and_decode", return_value=json.dumps(expected)) as evaluate,
        patch.object(client, "user_can_view_unpublished_judgments", return_value=False),
    ):
        assert (
            client.get_metrics(
                metric=metric,
                bucketing="monthly",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 2, 1),
                search_parameters=parameters,
            )
            == expected
        )
    variables, query = evaluate.call_args.args
    assert query == "get_metrics.xqy"
    assert variables["metric"] == metric
    assert variables["date_property"] == date_property
    search = json.loads(variables["search_parameters"])
    assert set(search["court"]) == {"ewhc/qb", "ewhc/kb"}
    assert search["from"] == "2020-01-01"
    assert search["show_unpublished"] == "false"
    assert search["page"] == 1
    assert search["order"] == ""
    assert parameters.as_marklogic_payload() == original
    evaluate.assert_called_once()


@pytest.mark.parametrize(
    "override",
    [
        {"metric": "unknown"},
        {"bucketing": "weekly"},
        {"end_date": date(2026, 1, 1)},
        {"end_date": date(2025, 1, 1)},
        {"start_date": datetime(2026, 1, 1, tzinfo=UTC)},
    ],
)
def test_invalid_metrics_request_does_not_query_marklogic(override):
    client = MarklogicApiClient("", "", "", False)
    parameters: dict[str, Any] = {
        "metric": "tdr_to_first_publish",
        "bucketing": "monthly",
        "start_date": date(2026, 1, 1),
        "end_date": date(2026, 2, 1),
    }
    parameters.update(override)
    with patch.object(client, "_eval_and_decode") as evaluate, pytest.raises(ValueError):
        client.get_metrics(**parameters)
    evaluate.assert_not_called()


def test_only_unpublished_requires_permission():
    client = MarklogicApiClient("", "", "", False)
    with (
        patch.object(client, "user_can_view_unpublished_judgments", return_value=False),
        patch.object(client, "_eval_and_decode") as evaluate,
        pytest.raises(MarklogicNotPermittedError),
    ):
        client.get_metrics(
            metric="tdr_to_first_publish",
            bucketing="daily",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 2),
            search_parameters=SearchParameters(only_unpublished=True),
        )
    evaluate.assert_not_called()
