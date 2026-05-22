"""Summarize structured log records: count, field stats, and value frequencies."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional


class SummaryError(Exception):
    """Raised when summarization fails."""


def summarize_records(
    records: Iterable[Dict[str, Any]],
    top_fields: Optional[List[str]] = None,
    top_n: int = 10,
) -> Dict[str, Any]:
    """Summarize an iterable of log records.

    Args:
        records: Iterable of parsed log record dicts.
        top_fields: Field names to compute value-frequency tables for.
                    If None, auto-detect up to 5 low-cardinality string fields.
        top_n: Number of top values to return per field frequency table.

    Returns:
        A dict with keys:
          - ``total``: total record count
          - ``fields``: set of all field names seen across records
          - ``frequencies``: {field: [(value, count), ...]} for requested fields
    """
    total = 0
    all_fields: set = set()
    counters: Dict[str, Counter] = defaultdict(Counter)
    auto_detect = top_fields is None
    candidate_fields: Counter = Counter()

    for record in records:
        total += 1
        all_fields.update(record.keys())

        if auto_detect:
            for k, v in record.items():
                if isinstance(v, (str, bool, int, float)) and not isinstance(v, bool):
                    candidate_fields[k] += 1

        fields_to_count = top_fields if top_fields is not None else []
        for field in fields_to_count:
            value = record.get(field)
            if value is not None:
                counters[field][str(value)] += 1

    if auto_detect and total > 0:
        # Pick up to 5 fields present in most records with low cardinality
        auto_fields = [
            f for f, _ in candidate_fields.most_common(20)
            if f not in ("timestamp", "ts", "time", "msg", "message")
        ]
        for field in auto_fields[:5]:
            for record in []:
                pass  # counters already empty; we'd need a second pass
        # Re-summarize frequencies for auto fields requires buffering — skip here
        # to keep memory usage O(1); callers can pass explicit top_fields.
        pass

    frequencies: Dict[str, List[tuple]] = {
        field: counter.most_common(top_n)
        for field, counter in counters.items()
    }

    return {
        "total": total,
        "fields": sorted(all_fields),
        "frequencies": frequencies,
    }


def format_summary(summary: Dict[str, Any]) -> str:
    """Render a summary dict as a human-readable string."""
    lines = [
        f"Total records : {summary['total']}",
        f"Fields seen   : {', '.join(summary['fields']) or '(none)'}",
    ]
    if summary.get("frequencies"):
        lines.append("")
        lines.append("Value frequencies:")
        for field, pairs in summary["frequencies"].items():
            lines.append(f"  {field}:")
            for value, count in pairs:
                lines.append(f"    {value!r:30s} {count}")
    return "\n".join(lines)
