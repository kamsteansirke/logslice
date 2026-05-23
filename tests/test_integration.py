"""Integration tests for the full logslice pipeline.

These tests exercise the end-to-end flow: parsing log lines, applying
time range filters, field filters, and formatting output.
"""

import io
import json
import unittest
from unittest.mock import patch

from logslice.cli import run


def _json_lines(*records):
    """Return a newline-separated string of JSON-encoded records."""
    return "\n".join(json.dumps(r) for r in records) + "\n"


SAMPLE_JSON_LOG = _json_lines(
    {"ts": "2024-01-15T10:00:00Z", "level": "info",  "msg": "server started",  "port": 8080},
    {"ts": "2024-01-15T10:01:00Z", "level": "debug", "msg": "request received", "path": "/health"},
    {"ts": "2024-01-15T10:02:00Z", "level": "error", "msg": "database timeout", "latency_ms": 5000},
    {"ts": "2024-01-15T10:03:00Z", "level": "info",  "msg": "request received", "path": "/api/v1"},
    {"ts": "2024-01-15T10:04:00Z", "level": "info",  "msg": "server stopped",   "port": 8080},
)

SAMPLE_LOGFMT_LOG = (
    'ts=2024-01-15T10:00:00Z level=info msg="server started" port=8080\n'
    'ts=2024-01-15T10:01:00Z level=debug msg="request received" path=/health\n'
    'ts=2024-01-15T10:02:00Z level=error msg="database timeout" latency_ms=5000\n'
)


class TestFullPipelineJson(unittest.TestCase):
    """End-to-end tests using JSON-formatted log input."""

    def _run(self, args, stdin_text):
        """Run the CLI with given args and stdin content, return stdout."""
        stdin = io.StringIO(stdin_text)
        stdout = io.StringIO()
        with patch("sys.stdin", stdin), patch("sys.stdout", stdout):
            run(args)
        return stdout.getvalue()

    def test_passthrough_all_records(self):
        """With no filters, all records are emitted."""
        out = self._run([], SAMPLE_JSON_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 5)

    def test_filter_by_level(self):
        """Filter to only error-level records."""
        out = self._run(["--filter", "level=error"], SAMPLE_JSON_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["msg"], "database timeout")

    def test_filter_by_numeric_gt(self):
        """Filter records where latency_ms > 1000."""
        out = self._run(["--filter", "latency_ms>1000"], SAMPLE_JSON_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["latency_ms"], 5000)

    def test_time_range_from(self):
        """Records before --from are excluded."""
        out = self._run(["--from", "2024-01-15T10:03:00Z"], SAMPLE_JSON_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(r["ts"] >= "2024-01-15T10:03:00Z" for r in records))

    def test_time_range_to(self):
        """Records after --to are excluded."""
        out = self._run(["--to", "2024-01-15T10:01:00Z"], SAMPLE_JSON_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 2)

    def test_time_range_from_and_to(self):
        """Only records within the time window are emitted."""
        out = self._run(
            ["--from", "2024-01-15T10:01:00Z", "--to", "2024-01-15T10:03:00Z"],
            SAMPLE_JSON_LOG,
        )
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 3)

    def test_multiple_filters(self):
        """Multiple --filter flags are ANDed together."""
        out = self._run(
            ["--filter", "level=info", "--filter", "port=8080"],
            SAMPLE_JSON_LOG,
        )
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertTrue(all(r["level"] == "info" for r in records))

    def test_output_format_logfmt(self):
        """Output in logfmt format contains key=value pairs."""
        out = self._run(["--filter", "level=error", "--format", "logfmt"], SAMPLE_JSON_LOG)
        self.assertIn("level=error", out)
        self.assertIn("latency_ms=5000", out)

    def test_empty_input(self):
        """Empty input produces empty output without error."""
        out = self._run([], "")
        self.assertEqual(out.strip(), "")

    def test_filter_no_matches(self):
        """Filter that matches nothing produces empty output."""
        out = self._run(["--filter", "level=critical"], SAMPLE_JSON_LOG)
        self.assertEqual(out.strip(), "")


class TestFullPipelineLogfmt(unittest.TestCase):
    """End-to-end tests using logfmt-formatted log input."""

    def _run(self, args, stdin_text):
        stdin = io.StringIO(stdin_text)
        stdout = io.StringIO()
        with patch("sys.stdin", stdin), patch("sys.stdout", stdout):
            run(args)
        return stdout.getvalue()

    def test_passthrough_logfmt_records(self):
        """logfmt input is parsed and re-emitted as JSON by default."""
        out = self._run([], SAMPLE_LOGFMT_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 3)

    def test_filter_logfmt_by_level(self):
        """Filter logfmt records by field value."""
        out = self._run(["--filter", "level=error"], SAMPLE_LOGFMT_LOG)
        records = [json.loads(line) for line in out.strip().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["msg"], "database timeout")


if __name__ == "__main__":
    unittest.main()
