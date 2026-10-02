import datetime

import pytest
from lxml import etree

from caselawclient.models.documents.metrics import DocumentMetrics
from caselawclient.models.documents.metrics.metrics_state import (
    DLS_NAMESPACE,
    FIRST_SUBMISSION_PROPERTY,
    LATEST_SUBMISSION_PROPERTY,
    SUBMISSION_AFTER_PUBLICATION_PROPERTY,
    MetricsState,
)
from caselawclient.models.documents.versions import VersionType

NOW = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
EARLIER = "2026-01-01T00:00:00+00:00"


def make_state(properties=None, version_types=None):
    root = etree.Element("properties")
    for name, value in (properties or {}).items():
        etree.SubElement(root, name).text = value
    return MetricsState(root, version_types)


def test_initial_submission_sets_first_and_latest():
    updates = MetricsState.for_new_document().submission_properties(NOW)
    assert updates[FIRST_SUBMISSION_PROPERTY] == NOW
    assert updates[LATEST_SUBMISSION_PROPERTY] == NOW
    assert SUBMISSION_AFTER_PUBLICATION_PROPERTY not in updates


def test_existing_first_submission_is_not_overwritten():
    state = make_state({FIRST_SUBMISSION_PROPERTY: EARLIER}, [])
    updates = state.submission_properties(NOW)
    assert FIRST_SUBMISSION_PROPERTY not in updates
    assert updates[LATEST_SUBMISSION_PROPERTY] == NOW


@pytest.mark.parametrize("history", [None, [VersionType.SUBMISSION]])
def test_legacy_history_does_not_invent_first_submission(history):
    updates = make_state(version_types=history).submission_properties(NOW)
    assert FIRST_SUBMISSION_PROPERTY not in updates
    assert updates[LATEST_SUBMISSION_PROPERTY] == NOW


def test_first_submission_after_edits_sets_first_timestamp():
    updates = make_state(version_types=[VersionType.EDIT, VersionType.ENRICHMENT]).submission_properties(NOW)
    assert updates[FIRST_SUBMISSION_PROPERTY] == NOW


@pytest.mark.parametrize(
    "properties",
    [
        {"first_published_datetime": EARLIER},
        {"latest_published_datetime": EARLIER},
        {"published": "true"},
    ],
)
def test_first_submission_after_publication_is_recorded_once(properties):
    state = make_state(properties)
    assert state.submission_properties(NOW)[SUBMISSION_AFTER_PUBLICATION_PROPERTY] == NOW
    etree.SubElement(state.properties, SUBMISSION_AFTER_PUBLICATION_PROPERTY).text = EARLIER
    assert SUBMISSION_AFTER_PUBLICATION_PROPERTY not in state.submission_properties(NOW)


def test_first_publication_calculates_durations_and_counts_submissions_only():
    state = make_state(
        {FIRST_SUBMISSION_PROPERTY: EARLIER, "transfer-received-at": "1900-01-01T00:00:00Z"},
        [VersionType.SUBMISSION, VersionType.EDIT, VersionType.ENRICHMENT, VersionType.RESTORE, VersionType.SUBMISSION],
    )
    dates = state.publication_dates(NOW)
    metrics = state.publication_metrics(NOW)
    assert metrics.tdr_to_first_publish.value == 86400
    assert metrics.tdr_to_latest_publish.value == 86400
    assert metrics.submissions_before_first_publish.value == 2
    assert dates["first_published_datetime"] == NOW
    assert dates["latest_published_datetime"] == NOW


def test_republication_preserves_first_metrics_and_uses_first_submission_after_publication():
    state = make_state(
        {
            FIRST_SUBMISSION_PROPERTY: "2025-01-01T00:00:00Z",
            "first_published_datetime": "2025-02-01T00:00:00Z",
            SUBMISSION_AFTER_PUBLICATION_PROPERTY: EARLIER,
        },
        [VersionType.SUBMISSION] * 5,
    )
    stored = DocumentMetrics()
    stored.tdr_to_first_publish.value = 10
    stored.submissions_before_first_publish.value = 2
    state.properties.append(stored.as_etree)
    dates = state.publication_dates(NOW)
    metrics = state.publication_metrics(NOW)
    assert metrics.tdr_to_first_publish.value == 10
    assert metrics.submissions_before_first_publish.value == 2
    assert metrics.tdr_to_latest_publish.value == 86400
    assert "first_published_datetime" not in dates


def test_republication_without_submission_clears_latest_metric():
    state = make_state({"first_published_datetime": EARLIER})
    stored = DocumentMetrics()
    stored.tdr_to_latest_publish.value = 60
    state.properties.append(stored.as_etree)
    assert state.publication_metrics(NOW).tdr_to_latest_publish.value is None


def test_empty_first_publication_timestamp_is_set():
    state = make_state({"first_published_datetime": "", "latest_published_datetime": EARLIER})
    dates = state.publication_dates(NOW)
    assert dates["first_published_datetime"] == NOW
    # Repairing the timestamp must not invent first metrics for a previously published document.
    assert all(metric.value is None for metric in state.publication_metrics(NOW))


def test_legacy_sentinel_is_preserved_without_inventing_first_metrics():
    state = make_state({"first_published_datetime": "1970-01-01T00:00:00Z"}, [VersionType.SUBMISSION])
    dates = state.publication_dates(NOW)
    assert "first_published_datetime" not in dates
    assert all(metric.value is None for metric in state.publication_metrics(NOW))


@pytest.mark.parametrize(
    ("start", "expected"),
    [
        (None, None),
        ("unparseable", None),
        ("2026-01-01T00:00:00", None),
        ("2026-01-03T00:00:00Z", None),
        ("2026-01-01T23:59:59.900000Z", 0),
        ("2026-01-02T01:59:58.900000+02:00", 1),
    ],
)
def test_duration_from_submission_date(start, expected):
    metrics = make_state({FIRST_SUBMISSION_PROPERTY: start}).publication_metrics(NOW)
    assert metrics.tdr_to_first_publish.value == expected
    assert metrics.tdr_to_latest_publish.value == expected


def test_unknown_history_omits_count():
    assert make_state().publication_metrics(NOW).submissions_before_first_publish.value is None


def test_no_submissions_is_a_real_zero_count():
    state = make_state(version_types=[VersionType.EDIT])
    assert state.publication_metrics(NOW).submissions_before_first_publish.value == 0


@pytest.mark.parametrize(
    ("numbers", "annotations", "expected"),
    [
        ([1, 2], ['{"type":"submission"}', '{"type":"edit"}'], [VersionType.SUBMISSION, VersionType.EDIT]),
        ([1, 3], ['{"type":"edit"}'] * 2, None),
        ([2], ['{"type":"edit"}'], None),
        ([1], ["Legacy annotation"], None),
        ([1], ['{"type":"unknown"}'], None),
        ([], [], None),
    ],
)
def test_parses_version_types_from_history(numbers, annotations, expected):
    root = etree.Element("state")
    etree.SubElement(root, "properties")
    history = etree.SubElement(root, f"{DLS_NAMESPACE}document-history")
    for number, annotation in zip(numbers, annotations):
        version = etree.SubElement(history, f"{DLS_NAMESPACE}version")
        etree.SubElement(version, f"{DLS_NAMESPACE}version-id").text = str(number)
        etree.SubElement(version, f"{DLS_NAMESPACE}annotation").text = annotation
    state = MetricsState.from_etree(root)
    assert state.version_types == expected
