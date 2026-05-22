"""Time range parsing and filtering for log records."""

from datetime import datetime, timezone
from typing import Optional, Tuple

DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
]

TIMESTAMP_FIELDS = ("timestamp", "time", "ts", "@timestamp", "date")


class TimeRangeError(ValueError):
    """Raised when a time range expression cannot be parsed."""


def parse_datetime(value: str) -> datetime:
    """Parse a datetime string using known formats.

    Returns a timezone-aware datetime (UTC if no tz info present).
    """
    for fmt in DATETIME_FORMATS:
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    raise TimeRangeError(f"Cannot parse datetime: {value!r}")


def parse_time_range(
    since: Optional[str], until: Optional[str]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Parse optional since/until strings into datetime objects."""
    since_dt = parse_datetime(since) if since else None
    until_dt = parse_datetime(until) if until else None
    if since_dt and until_dt and since_dt > until_dt:
        raise TimeRangeError(
            f"'since' ({since}) must be before 'until' ({until})"
        )
    return since_dt, until_dt


def extract_timestamp(record: dict) -> Optional[datetime]:
    """Extract and parse the timestamp from a log record."""
    for field in TIMESTAMP_FIELDS:
        value = record.get(field)
        if value is not None:
            try:
                return parse_datetime(str(value))
            except TimeRangeError:
                continue
    return None


def in_time_range(
    record: dict,
    since: Optional[datetime],
    until: Optional[datetime],
) -> bool:
    """Return True if the record's timestamp falls within [since, until].

    Records with no parseable timestamp are always included.
    """
    if since is None and until is None:
        return True
    ts = extract_timestamp(record)
    if ts is None:
        return True
    if since and ts < since:
        return False
    if until and ts > until:
        return False
    return True
