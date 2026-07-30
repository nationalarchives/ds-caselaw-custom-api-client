from datetime import UTC, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from caselawclient.models.utilities.dates import parse_string_date_as_utc, require_aware_utc

TOKYO = ZoneInfo("Asia/Tokyo")
PLUS_4 = ZoneInfo("Etc/GMT+4")
LONDON = ZoneInfo("Europe/London")


def test_parse_string_date():
    assert parse_string_date_as_utc("2002-06-01T12:00:00Z", LONDON) == datetime.fromisoformat(
        "2002-06-01T12:00:00+00:00",
    )
    assert parse_string_date_as_utc("2002-01-01T12Z", LONDON) == datetime.fromisoformat("2002-01-01T12:00:00+00:00")
    assert parse_string_date_as_utc("2002-06-01T13", LONDON) == datetime.fromisoformat("2002-06-01T12:00:00+00:00")
    assert parse_string_date_as_utc("2002-01-01T13", LONDON) == datetime.fromisoformat("2002-01-01T13:00:00+00:00")
    assert parse_string_date_as_utc("2002-06-01T12-05:00", LONDON) == datetime.fromisoformat(
        "2002-06-01T17:00:00+00:00",
    )
    assert parse_string_date_as_utc("2002-06-01T12-05:00", TOKYO) == datetime.fromisoformat("2002-06-01T17:00:00+00:00")
    assert parse_string_date_as_utc("2002", timezone=TOKYO) == datetime.fromisoformat("2001-12-31T15:00:00+00:00")
    assert parse_string_date_as_utc("2002", timezone=PLUS_4) == datetime.fromisoformat("2002-01-01T04:00:00+00:00")


def test_require_aware_utc_rejects_naive_datetime():
    naive_datetime = datetime.fromisoformat("2025-08-19T08:00:00")
    with pytest.raises(ValueError, match="timestamp must be timezone-aware"):
        require_aware_utc(naive_datetime, name="timestamp")


def test_require_aware_utc_normalizes_to_utc():
    offset_datetime = datetime(2025, 8, 19, 9, 0, tzinfo=timezone(timedelta(hours=1)))
    assert require_aware_utc(offset_datetime) == datetime(2025, 8, 19, 8, 0, tzinfo=UTC)
