from datetime import datetime
from zoneinfo import ZoneInfo

from caselawclient.models.utilities.dates import parse_string_date_as_utc

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
