"""Tests for logslice.filter module."""

import pytest
from logslice.filter import (
    FilterError,
    apply_filters,
    build_filters,
    matches_filter,
    parse_filter_expr,
)


class TestParseFilterExpr:
    def test_equality(self):
        assert parse_filter_expr("level=error") == ("level", "=", "error")

    def test_not_equal(self):
        assert parse_filter_expr("status!=200") == ("status", "!=", "200")

    def test_greater_than_equal(self):
        assert parse_filter_expr("status>=400") == ("status", ">=", "400")

    def test_less_than(self):
        assert parse_filter_expr("duration<100") == ("duration", "<", "100")

    def test_whitespace_trimmed(self):
        assert parse_filter_expr(" level = warn ") == ("level", "=", "warn")

    def test_no_operator_raises(self):
        with pytest.raises(FilterError, match="No valid operator"):
            parse_filter_expr("levelwarn")

    def test_missing_field_raises(self):
        with pytest.raises(FilterError, match="Missing field name"):
            parse_filter_expr("=error")

    def test_missing_value_raises(self):
        with pytest.raises(FilterError, match="Missing value"):
            parse_filter_expr("level=")


class TestMatchesFilter:
    def test_string_equality_match(self):
        assert matches_filter({"level": "error"}, "level", "=", "error") is True

    def test_string_equality_no_match(self):
        assert matches_filter({"level": "info"}, "level", "=", "error") is False

    def test_numeric_greater_than(self):
        assert matches_filter({"status": 500}, "status", ">=", "400") is True

    def test_numeric_less_than(self):
        assert matches_filter({"duration": 50}, "duration", "<", "100") is True

    def test_missing_field_returns_false(self):
        assert matches_filter({"level": "info"}, "status", "=", "200") is False

    def test_not_equal(self):
        assert matches_filter({"env": "prod"}, "env", "!=", "dev") is True

    def test_float_comparison(self):
        assert matches_filter({"latency": 1.5}, "latency", "<=", "2.0") is True


class TestApplyFilters:
    def test_all_match(self):
        record = {"level": "error", "status": 500}
        filters = [("level", "=", "error"), ("status", ">=", "500")]
        assert apply_filters(record, filters) is True

    def test_one_fails(self):
        record = {"level": "info", "status": 200}
        filters = [("level", "=", "error"), ("status", "=", "200")]
        assert apply_filters(record, filters) is False

    def test_empty_filters_always_true(self):
        assert apply_filters({"level": "debug"}, []) is True


class TestBuildFilters:
    def test_builds_multiple(self):
        result = build_filters(["level=error", "status>=500"])
        assert result == [("level", "=", "error"), ("status", ">=", "500")]

    def test_invalid_expr_propagates(self):
        with pytest.raises(FilterError):
            build_filters(["level=error", "badexpr"])
