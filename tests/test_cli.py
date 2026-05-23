"""Integration-level tests for the CLI entry point (build_parser / run)."""

import json
import sys
from io import StringIO
from unittest import TestCase
from unittest.mock import patch, MagicMock

import pytest

from logslice.cli import build_parser, run, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_lines(*records):
    """Return a list of JSON-encoded strings, one per record."""
    return [json.dumps(r) for r in records]


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser(TestCase):
    def setUp(self):
        self.parser = build_parser()

    def test_returns_argument_parser(self):
        import argparse
        self.assertIsInstance(self.parser, argparse.ArgumentParser)

    def test_default_format_is_json(self):
        args = self.parser.parse_args([])
        self.assertEqual(args.format, "json")

    def test_format_choices(self):
        for fmt in ("json", "logfmt", "text"):
            args = self.parser.parse_args(["--format", fmt])
            self.assertEqual(args.format, fmt)

    def test_filter_accumulates(self):
        args = self.parser.parse_args(["-f", "level=error", "-f", "status>=400"])
        self.assertEqual(args.filter, ["level=error", "status>=400"])

    def test_filter_default_empty(self):
        args = self.parser.parse_args([])
        self.assertEqual(args.filter, [])

    def test_since_and_until(self):
        args = self.parser.parse_args(["--since", "2024-01-01", "--until", "2024-01-02"])
        self.assertEqual(args.since, "2024-01-01")
        self.assertEqual(args.until, "2024-01-02")

    def test_summarize_flag(self):
        args = self.parser.parse_args(["--summarize"])
        self.assertTrue(args.summarize)

    def test_summarize_default_false(self):
        args = self.parser.parse_args([])
        self.assertFalse(args.summarize)

    def test_fields_option(self):
        args = self.parser.parse_args(["--fields", "level,msg"])
        self.assertEqual(args.fields, "level,msg")

    def test_file_positional(self):
        args = self.parser.parse_args(["app.log"])
        self.assertEqual(args.file, "app.log")

    def test_file_defaults_to_none(self):
        args = self.parser.parse_args([])
        self.assertIsNone(args.file)


# ---------------------------------------------------------------------------
# run() — uses mocked pipeline so we don't need real files
# ---------------------------------------------------------------------------

class TestRun(TestCase):
    """Smoke-test run() with a minimal in-memory setup."""

    def _make_args(self, **kwargs):
        defaults = dict(
            file=None,
            format="json",
            filter=[],
            since=None,
            until=None,
            summarize=False,
            fields=None,
        )
        defaults.update(kwargs)
        return MagicMock(**defaults)

    def test_run_reads_stdin_when_no_file(self):
        records = [{"level": "info", "msg": "hello"}]
        fake_stdin = StringIO("\n".join(json.dumps(r) for r in records) + "\n")
        args = self._make_args()

        with patch("logslice.cli._pipeline") as mock_pipeline:
            mock_pipeline.return_value = iter(records)
            with patch("sys.stdin", fake_stdin):
                with patch("logslice.output.write_records") as mock_write:
                    run(args)
                    mock_pipeline.assert_called_once()

    def test_run_opens_file_when_provided(self, tmp_path=None):
        import tempfile, os
        record = {"level": "warn", "msg": "disk full"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            f.write(json.dumps(record) + "\n")
            fname = f.name
        try:
            args = self._make_args(file=fname)
            with patch("logslice.cli._pipeline") as mock_pipeline:
                mock_pipeline.return_value = iter([record])
                with patch("logslice.output.write_records"):
                    run(args)
                mock_pipeline.assert_called_once()
        finally:
            os.unlink(fname)


# ---------------------------------------------------------------------------
# main() — ensure it delegates to run() without crashing
# ---------------------------------------------------------------------------

class TestMain(TestCase):
    def test_main_calls_run(self):
        with patch("logslice.cli.run") as mock_run:
            with patch("sys.argv", ["logslice"]):
                with patch("sys.stdin", StringIO("")):
                    main()
            mock_run.assert_called_once()
