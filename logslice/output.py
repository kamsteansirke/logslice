"""Output formatting for log records."""

import json
import sys
from typing import IO, Iterable, Optional

FORMAT_JSON = "json"
FORMAT_LOGFMT = "logfmt"
FORMAT_TEXT = "text"

SUPPORTED_FORMATS = (FORMAT_JSON, FORMAT_LOGFMT, FORMAT_TEXT)

DEFAULT_TEXT_FIELDS = ("timestamp", "time", "ts", "level", "severity", "msg", "message")


class OutputError(ValueError):
    """Raised for invalid output configuration."""


def _to_logfmt(record: dict) -> str:
    """Serialize a record to logfmt."""
    parts = []
    for key, value in record.items():
        key = str(key).replace(" ", "_")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        else:
            value = str(value)
        if " " in value or "=" in value or '"' in value:
            value = json.dumps(value)
        parts.append(f"{key}={value}")
    return " ".join(parts)


def _to_text(record: dict) -> str:
    """Serialize a record to a human-readable single line."""
    parts = []
    seen = set()
    for field in DEFAULT_TEXT_FIELDS:
        if field in record:
            parts.append(str(record[field]))
            seen.add(field)
    extras = [
        f"{k}={v}" for k, v in record.items() if k not in seen
    ]
    if extras:
        parts.append(" ".join(extras))
    return "  ".join(parts)


def format_record(record: dict, fmt: str = FORMAT_JSON) -> str:
    """Format a single record according to the chosen format."""
    if fmt == FORMAT_JSON:
        return json.dumps(record, ensure_ascii=False)
    elif fmt == FORMAT_LOGFMT:
        return _to_logfmt(record)
    elif fmt == FORMAT_TEXT:
        return _to_text(record)
    else:
        raise OutputError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )


def write_records(
    records: Iterable[dict],
    fmt: str = FORMAT_JSON,
    out: Optional[IO[str]] = None,
    count: Optional[int] = None,
) -> int:
    """Write formatted records to *out* (defaults to stdout).

    Returns the number of records written.
    """
    if out is None:
        out = sys.stdout
    if fmt not in SUPPORTED_FORMATS:
        raise OutputError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    written = 0
    for record in records:
        if count is not None and written >= count:
            break
        out.write(format_record(record, fmt))
        out.write("\n")
        written += 1
    return written
