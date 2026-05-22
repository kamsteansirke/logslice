"""Tests for logslice.time_range module."""

import pytest
from datetime import datetime, timezone
from logslice.time_range import (
    TimeRangeError,
    parse_datetime,
    parse_time_range,
    extract_timestamp,
    in_time_range,
)


class TestParseDatetime:
    def test_iso_utc_z(self):
        dt = parse_datetime("2024-01-15T10:30:00Z")
        assert dt == datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_iso_with_microseconds(self):
        dt = parse_datetime("2024-01-15T10:30:00.123456Z")
        assert dt.microsecond == 123456

    def test_date_only(self):
        dt = parse_datetime("2024-01-15")
        assert dt.year == 2024 and dt.month == 1 and dt.day == 15
        assert dt.tzinfo == timezone.utc

    def test_space_separated(self):
        dt = parse_datetime("2024-01-15 10:30:00")
        assert dt.hour == 10

    def test_invalid_raises(self):
        with pytest.raises(TimeRangeError, match="Cannot parse datetime"):
            parse_datetime("not-a-date")

    def test_naive_datetime_gets_utc(self):
        dt = parse_datetime("2024-06-01 00:00:00")
        assert dt.tzinfo == timezone.utc


class TestParseTimeRange:
    def test_both_none(self):
        since, until = parse_time_range(None, None)
        assert since is None and until is None

    def test_since_only(self):
        since, until = parse_time_range("2024-01-01", None)
        assert since is not None
        assert until is None

    def test_until_only(self):
        since, until = parse_time_range(None, "2024-12-31")
        assert until is not None

    def test_valid_range(self):
        since, until = parse_time_range("2024-01-01", "2024-12-31")
        assert since < until

    def test_inverted_range_raises(self):
        with pytest.raises(TimeRangeError, match="must be before"):
            parse_time_range("2024-12-31", "2024-01-01")


class TestExtractTimestamp:
    def test_timestamp_field(self):
        record = {"timestamp": "2024-03-10T12:00:00Z", "msg": "hello"}
        dt = extract_timestamp(record)
        assert dt is not None
        assert dt.year == 2024

    def test_ts_field(self):
        record = {"ts": "2024-03-10T12:00:00Z"}
        dt = extract_timestamp(record)
        assert dt is not None

    def test_no_timestamp_returns_none(self):
        record = {"level": "info", "msg": "no time here"}
        assert extract_timestamp(record) is None

    def test_unparseable_timestamp_returns_none(self):
        record = {"timestamp": "garbage"}
        assert extract_timestamp(record) is None


class TestInTimeRange:
    def _dt(self, s):
        from logslice.time_range import parse_datetime
        return parse_datetime(s)

    def test_no_range_always_true(self):
        assert in_time_range({"msg": "hi"}, None, None) is True

    def test_within_range(self):
        record = {"timestamp": "2024-06-15T00:00:00Z"}
        assert in_time_range(record, self._dt("2024-01-01"), self._dt("2024-12-31")) is True

    def test_before_since(self):
        record = {"timestamp": "2023-01-01T00:00:00Z"}
        assert in_time_range(record, self._dt("2024-01-01"), None) is False

    def test_after_until(self):
        record = {"timestamp": "2025-01-01T00:00:00Z"}
        assert in_time_range(record, None, self._dt("2024-12-31")) is False

    def test_no_timestamp_field_included(self):
        record = {"msg": "no time"}
        assert in_time_range(record, self._dt("2024-01-01"), self._dt("2024-12-31")) is True
