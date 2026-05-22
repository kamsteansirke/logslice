"""Command-line interface for logslice."""

import argparse
import sys
from typing import List, Optional

from logslice.filter import FilterError, parse_filter_expr, apply_filters
from logslice.output import OutputError, write_records, SUPPORTED_FORMATS, FORMAT_JSON
from logslice.stream import stream_logs
from logslice.time_range import TimeRangeError, parse_time_range, in_time_range


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Stream and filter structured log files by time range or field values.",
    )
    p.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Log files to read. Reads from stdin if none given.",
    )
    p.add_argument(
        "--since",
        metavar="DATETIME",
        help="Include records at or after this timestamp (e.g. 2024-01-01T00:00:00Z).",
    )
    p.add_argument(
        "--until",
        metavar="DATETIME",
        help="Include records at or before this timestamp.",
    )
    p.add_argument(
        "-f", "--filter",
        dest="filters",
        action="append",
        metavar="EXPR",
        help="Filter expression, e.g. level=error or status>=400. May be repeated.",
    )
    p.add_argument(
        "-o", "--output",
        choices=SUPPORTED_FORMATS,
        default=FORMAT_JSON,
        help="Output format (default: json).",
    )
    p.add_argument(
        "-n", "--count",
        type=int,
        metavar="N",
        help="Stop after emitting N records.",
    )
    return p


def run(argv: Optional[List[str]] = None) -> int:
    """Entry point. Returns an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        since_dt, until_dt = parse_time_range(args.since, args.until)
    except TimeRangeError as exc:
        print(f"logslice: time range error: {exc}", file=sys.stderr)
        return 2

    filter_exprs = []
    for raw in args.filters or []:
        try:
            filter_exprs.append(parse_filter_expr(raw))
        except FilterError as exc:
            print(f"logslice: filter error: {exc}", file=sys.stderr)
            return 2

    def _pipeline(records):
        for record in records:
            if not in_time_range(record, since_dt, until_dt):
                continue
            if not apply_filters(record, filter_exprs):
                continue
            yield record

    sources = args.files if args.files else [sys.stdin]
    try:
        all_records = stream_logs(sources)
        filtered = _pipeline(all_records)
        write_records(filtered, fmt=args.output, count=args.count)
    except OutputError as exc:
        print(f"logslice: output error: {exc}", file=sys.stderr)
        return 1
    except (OSError, IOError) as exc:
        print(f"logslice: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        pass

    return 0


def main() -> None:
    sys.exit(run())
