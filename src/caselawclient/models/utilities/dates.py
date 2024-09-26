from datetime import datetime

from dateutil.parser import isoparse
from pytz import UTC, tzinfo


def parse_string_date_as_utc(iso_string: str, timezone: tzinfo.BaseTzInfo) -> datetime:
    """iso_string might be aware or unaware:
    ensure that it is converted to a UTC-aware datetime"""

    mixed_date = isoparse(iso_string)
    aware_date = mixed_date if mixed_date.tzinfo else timezone.localize(mixed_date)

    # make UTC
    utc_date = aware_date.astimezone(UTC)
    return utc_date
