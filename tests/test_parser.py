"""Tests for logslice.parser module."""

import pytest
from logslice.parser import parse_json, parse_logfmt, parse_line, ParseError


class TestParseJson:
    def test_simple_object(self):
        result = parse_json('{"level": "info", "msg": "started"}')
        assert result == {"level": "info", "msg": "started"}

    def test_nested_fields(self):
        result = parse_json('{"ts": "2024-01-01T00:00:00Z", "code": 200}')
        assert result["code"] == 200

    def test_invalid_json_raises(self):
        with pytest.raises(ParseError, match="Invalid JSON"):
            parse_json("not json")

    def test_non_object_raises(self):
        with pytest.raises(ParseError, match="Expected JSON object"):
            parse_json('["a", "b"]')

    def test_strips_whitespace(self):
        result = parse_json('  {"k": "v"}  ')
        assert result == {"k": "v"}


class TestParseLogfmt:
    def test_simple_pairs(self):
        result = parse_logfmt('level=info msg=started')
        assert result == {"level": "info", "msg": "started"}

    def test_quoted_value(self):
        result = parse_logfmt('msg="hello world" level=warn')
        assert result["msg"] == "hello world"
        assert result["level"] == "warn"

    def test_boolean_flag(self):
        result = parse_logfmt('verbose level=debug')
        assert result["verbose"] is True
        assert result["level"] == "debug"

    def test_quoted_escaped(self):
        result = parse_logfmt('msg="say \\"hi\\""')
        assert result["msg"] == 'say "hi"'

    def test_empty_line_returns_empty(self):
        result = parse_logfmt('   ')
        assert result == {}


class TestParseLine:
    def test_auto_detect_json(self):
        result = parse_line('{"level": "error"}')
        assert result["level"] == "error"

    def test_auto_detect_logfmt(self):
        result = parse_line('level=error msg=oops')
        assert result == {"level": "error", "msg": "oops"}

    def test_force_json(self):
        result = parse_line('{"x": 1}', fmt="json")
        assert result["x"] == 1

    def test_force_logfmt(self):
        result = parse_line('a=1 b=2', fmt="logfmt")
        assert result == {"a": "1", "b": "2"}

    def test_empty_raises(self):
        with pytest.raises(ParseError, match="Empty line"):
            parse_line("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ParseError, match="Empty line"):
            parse_line("   ")
