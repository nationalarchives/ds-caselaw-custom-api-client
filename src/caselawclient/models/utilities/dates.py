from datetime import UTC, datetime, tzinfo

from dateutil.parser import isoparse


def require_aware_utc(value: datetime, name: str = "datetime") -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def parse_string_date_as_utc(iso_string: str, timezone: tzinfo) -> datetime:
    """iso_string might be aware or unaware:
    ensure that it is converted to a UTC-aware datetime"""

    mixed_date = isoparse(iso_string)
    aware_date = mixed_date if mixed_date.tzinfo else mixed_date.replace(tzinfo=timezone)

    # make UTC
    utc_date = aware_date.astimezone(UTC)
    return utc_date
