"""Tests for logslice.stream — iter_records and stream_logs."""

import io
import json
import pytest

from logslice.stream import iter_records, stream_logs
from logslice.parser import ParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _lines(*lines):
    """Return a StringIO containing the given lines joined by newlines."""
    return io.StringIO("\n".join(lines) + "\n")


def _json_line(**kwargs):
    return json.dumps(kwargs)


# ---------------------------------------------------------------------------
# iter_records
# ---------------------------------------------------------------------------

class TestIterRecords:
    def test_yields_parsed_json_objects(self):
        src = _lines(
            _json_line(level="info", msg="hello"),
            _json_line(level="error", msg="boom"),
        )
        records = list(iter_records(src))
        assert len(records) == 2
        assert records[0]["msg"] == "hello"
        assert records[1]["level"] == "error"

    def test_yields_parsed_logfmt_objects(self):
        src = _lines(
            'level=info msg=hello',
            'level=error msg=boom',
        )
        records = list(iter_records(src, fmt="logfmt"))
        assert len(records) == 2
        assert records[0]["msg"] == "hello"

    def test_skips_blank_lines(self):
        src = _lines(
            _json_line(msg="a"),
            "",
            "   ",
            _json_line(msg="b"),
        )
        records = list(iter_records(src))
        assert len(records) == 2

    def test_skips_unparseable_lines_by_default(self):
        src = _lines(
            _json_line(msg="ok"),
            "not valid json at all",
            _json_line(msg="also ok"),
        )
        records = list(iter_records(src))
        assert len(records) == 2

    def test_raises_on_parse_error_when_strict(self):
        src = _lines(
            _json_line(msg="ok"),
            "not valid json at all",
        )
        with pytest.raises(ParseError):
            list(iter_records(src, strict=True))

    def test_empty_file_yields_nothing(self):
        src = io.StringIO("")
        assert list(iter_records(src)) == []

    def test_auto_detects_logfmt_when_fmt_is_auto(self):
        src = _lines('level=warn msg="disk full"')
        records = list(iter_records(src, fmt="auto"))
        assert records[0]["level"] == "warn"

    def test_auto_detects_json(self):
        src = _lines(_json_line(level="debug", msg="trace"))
        records = list(iter_records(src, fmt="auto"))
        assert records[0]["level"] == "debug"


# ---------------------------------------------------------------------------
# stream_logs  (integration: iter_records + filter + time-range)
# ---------------------------------------------------------------------------

class TestStreamLogs:
    def test_no_filters_returns_all(self):
        src = _lines(
            _json_line(level="info", msg="a"),
            _json_line(level="error", msg="b"),
        )
        results = list(stream_logs(src))
        assert len(results) == 2

    def test_filter_by_field_equality(self):
        src = _lines(
            _json_line(level="info", msg="keep"),
            _json_line(level="error", msg="drop"),
        )
        results = list(stream_logs(src, filters=["level=info"]))
        assert len(results) == 1
        assert results[0]["msg"] == "keep"

    def test_multiple_filters_are_anded(self):
        src = _lines(
            _json_line(level="info", service="web", msg="yes"),
            _json_line(level="info", service="db",  msg="no"),
            _json_line(level="error", service="web", msg="no"),
        )
        results = list(stream_logs(src, filters=["level=info", "service=web"]))
        assert len(results) == 1
        assert results[0]["msg"] == "yes"

    def test_time_range_filters_records(self):
        src = _lines(
            _json_line(ts="2024-01-01T10:00:00Z", msg="before"),
            _json_line(ts="2024-01-01T12:00:00Z", msg="during"),
            _json_line(ts="2024-01-01T14:00:00Z", msg="after"),
        )
        results = list(
            stream_logs(
                src,
                time_field="ts",
                start="2024-01-01T11:00:00Z",
                end="2024-01-01T13:00:00Z",
            )
        )
        assert len(results) == 1
        assert results[0]["msg"] == "during"

    def test_invalid_filter_expression_raises(self):
        src = _lines(_json_line(msg="x"))
        from logslice.filter import FilterError
        with pytest.raises(FilterError):
            list(stream_logs(src, filters=["%%%invalid"]))
