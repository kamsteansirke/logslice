"""Tests for logslice.summarize."""

from __future__ import annotations

import pytest

from logslice.summarize import format_summary, summarize_records


RECORDS = [
    {"level": "info",  "service": "api",    "status": 200, "msg": "ok"},
    {"level": "warn",  "service": "api",    "status": 429, "msg": "rate limited"},
    {"level": "error", "service": "worker", "status": 500, "msg": "boom"},
    {"level": "info",  "service": "api",    "status": 200, "msg": "ok"},
    {"level": "info",  "service": "worker", "status": 200, "msg": "done"},
]


class TestSummarizeRecords:
    def test_total_count(self):
        result = summarize_records(iter(RECORDS))
        assert result["total"] == 5

    def test_fields_collected(self):
        result = summarize_records(iter(RECORDS))
        assert set(result["fields"]) == {"level", "service", "status", "msg"}

    def test_fields_sorted(self):
        result = summarize_records(iter(RECORDS))
        assert result["fields"] == sorted(result["fields"])

    def test_frequency_for_explicit_field(self):
        result = summarize_records(iter(RECORDS), top_fields=["level"])
        freqs = dict(result["frequencies"]["level"])
        assert freqs["info"] == 3
        assert freqs["warn"] == 1
        assert freqs["error"] == 1

    def test_frequency_multiple_fields(self):
        result = summarize_records(iter(RECORDS), top_fields=["level", "service"])
        assert "level" in result["frequencies"]
        assert "service" in result["frequencies"]
        service_freqs = dict(result["frequencies"]["service"])
        assert service_freqs["api"] == 3
        assert service_freqs["worker"] == 2

    def test_top_n_limits_results(self):
        records = [{"x": str(i)} for i in range(50)]
        result = summarize_records(iter(records), top_fields=["x"], top_n=5)
        assert len(result["frequencies"]["x"]) == 5

    def test_empty_records(self):
        result = summarize_records(iter([]))
        assert result["total"] == 0
        assert result["fields"] == []
        assert result["frequencies"] == {}

    def test_missing_field_in_some_records(self):
        records = [
            {"level": "info"},
            {"msg": "hello"},
            {"level": "warn"},
        ]
        result = summarize_records(iter(records), top_fields=["level"])
        freqs = dict(result["frequencies"]["level"])
        assert freqs.get("info") == 1
        assert freqs.get("warn") == 1

    def test_no_top_fields_returns_empty_frequencies(self):
        # Without explicit top_fields and no second-pass buffering, frequencies empty
        result = summarize_records(iter(RECORDS), top_fields=[])
        assert result["frequencies"] == {}


class TestFormatSummary:
    def test_contains_total(self):
        summary = {"total": 42, "fields": ["a", "b"], "frequencies": {}}
        output = format_summary(summary)
        assert "42" in output

    def test_contains_field_names(self):
        summary = {"total": 1, "fields": ["level", "msg"], "frequencies": {}}
        output = format_summary(summary)
        assert "level" in output
        assert "msg" in output

    def test_contains_frequency_values(self):
        summary = {
            "total": 3,
            "fields": ["level"],
            "frequencies": {"level": [("info", 2), ("warn", 1)]},
        }
        output = format_summary(summary)
        assert "info" in output
        assert "2" in output

    def test_no_frequencies_section_when_empty(self):
        summary = {"total": 0, "fields": [], "frequencies": {}}
        output = format_summary(summary)
        assert "Value frequencies" not in output
