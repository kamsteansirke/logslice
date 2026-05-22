"""Tests for logslice.output module."""

import io
import json
import pytest
from logslice.output import (
    OutputError,
    format_record,
    write_records,
    FORMAT_JSON,
    FORMAT_LOGFMT,
    FORMAT_TEXT,
)


SAMPLE = {
    "timestamp": "2024-06-01T10:00:00Z",
    "level": "info",
    "msg": "server started",
    "port": 8080,
}


class TestFormatRecord:
    def test_json_roundtrip(self):
        line = format_record(SAMPLE, FORMAT_JSON)
        parsed = json.loads(line)
        assert parsed == SAMPLE

    def test_logfmt_contains_key_value(self):
        line = format_record(SAMPLE, FORMAT_LOGFMT)
        assert "level=info" in line
        assert "port=8080" in line

    def test_logfmt_quotes_values_with_spaces(self):
        record = {"msg": "hello world"}
        line = format_record(record, FORMAT_LOGFMT)
        assert 'msg="hello world"' in line

    def test_logfmt_nested_dict_serialized(self):
        record = {"meta": {"a": 1}}
        line = format_record(record, FORMAT_LOGFMT)
        assert "meta=" in line

    def test_text_includes_known_fields(self):
        line = format_record(SAMPLE, FORMAT_TEXT)
        assert "info" in line
        assert "server started" in line
        assert "2024-06-01T10:00:00Z" in line

    def test_text_includes_extra_fields(self):
        line = format_record(SAMPLE, FORMAT_TEXT)
        assert "port=8080" in line

    def test_unknown_format_raises(self):
        with pytest.raises(OutputError, match="Unknown format"):
            format_record(SAMPLE, "xml")


class TestWriteRecords:
    def _run(self, records, fmt=FORMAT_JSON, count=None):
        buf = io.StringIO()
        n = write_records(records, fmt=fmt, out=buf, count=count)
        return n, buf.getvalue()

    def test_writes_all_records(self):
        records = [SAMPLE, {"msg": "second"}]
        n, output = self._run(records)
        assert n == 2
        lines = output.strip().splitlines()
        assert len(lines) == 2

    def test_count_limits_output(self):
        records = [{"n": i} for i in range(10)]
        n, output = self._run(records, count=3)
        assert n == 3
        assert len(output.strip().splitlines()) == 3

    def test_empty_records(self):
        n, output = self._run([])
        assert n == 0
        assert output == ""

    def test_logfmt_output(self):
        n, output = self._run([SAMPLE], fmt=FORMAT_LOGFMT)
        assert n == 1
        assert "level=info" in output

    def test_unknown_format_raises(self):
        with pytest.raises(OutputError):
            write_records([SAMPLE], fmt="yaml", out=io.StringIO())

    def test_returns_written_count(self):
        records = [{"i": i} for i in range(5)]
        n, _ = self._run(records, count=100)
        assert n == 5
