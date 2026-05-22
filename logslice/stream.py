"""Stream and filter log lines from a file or stdin."""

import sys
from typing import IO, Iterator, List, Optional, Tuple

from logslice.filter import apply_filters, build_filters
from logslice.parser import ParseError, parse_line


def iter_records(
    source: IO[str],
    filters: Optional[List[Tuple[str, str, str]]] = None,
    skip_invalid: bool = True,
) -> Iterator[dict]:
    """Yield parsed log records from *source* that match all *filters*.

    Args:
        source: A readable text stream (file or stdin).
        filters: Pre-built list of (field, op, value) tuples from build_filters.
        skip_invalid: When True, unparseable lines are silently skipped;
                      when False, ParseError is re-raised.
    """
    active_filters = filters or []

    for line in source:
        line = line.rstrip("\n")
        if not line:
            continue
        try:
            record = parse_line(line)
        except ParseError:
            if not skip_invalid:
                raise
            continue

        if apply_filters(record, active_filters):
            yield record


def stream_logs(
    path: Optional[str],
    filter_exprs: Optional[List[str]] = None,
    skip_invalid: bool = True,
) -> Iterator[dict]:
    """Open *path* (or stdin when None) and yield matching log records.

    Args:
        path: Filesystem path to a log file, or None to read from stdin.
        filter_exprs: Raw filter expression strings, e.g. ["level=error"].
        skip_invalid: Passed through to iter_records.
    """
    filters = build_filters(filter_exprs) if filter_exprs else []

    if path is None:
        yield from iter_records(sys.stdin, filters=filters, skip_invalid=skip_invalid)
    else:
        with open(path, "r", encoding="utf-8") as fh:
            yield from iter_records(fh, filters=filters, skip_invalid=skip_invalid)
