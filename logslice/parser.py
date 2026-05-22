"""Structured log line parser supporting JSON and logfmt formats."""

import json
from typing import Optional


class ParseError(Exception):
    """Raised when a log line cannot be parsed."""


def parse_json(line: str) -> dict:
    """Parse a JSON-formatted log line."""
    try:
        data = json.loads(line.strip())
        if not isinstance(data, dict):
            raise ParseError(f"Expected JSON object, got {type(data).__name__}")
        return data
    except json.JSONDecodeError as exc:
        raise ParseError(f"Invalid JSON: {exc}") from exc


def parse_logfmt(line: str) -> dict:
    """Parse a logfmt-formatted log line (key=value pairs)."""
    result = {}
    line = line.strip()
    i = 0
    while i < len(line):
        # Skip leading whitespace
        while i < len(line) and line[i] == " ":
            i += 1
        if i >= len(line):
            break
        # Read key
        key_start = i
        while i < len(line) and line[i] not in ("=", " "):
            i += 1
        key = line[key_start:i]
        if not key:
            break
        if i >= len(line) or line[i] != "=":
            result[key] = True
            continue
        i += 1  # skip '='
        # Read value
        if i < len(line) and line[i] == '"':
            i += 1
            val_start = i
            while i < len(line) and line[i] != '"':
                if line[i] == "\\":
                    i += 1
                i += 1
            value = line[val_start:i].replace('\\"', '"')
            i += 1  # skip closing quote
        else:
            val_start = i
            while i < len(line) and line[i] != " ":
                i += 1
            value = line[val_start:i]
        result[key] = value
    return result


def parse_line(line: str, fmt: Optional[str] = None) -> dict:
    """Auto-detect or use specified format to parse a log line."""
    line = line.strip()
    if not line:
        raise ParseError("Empty line")
    if fmt == "json":
        return parse_json(line)
    if fmt == "logfmt":
        return parse_logfmt(line)
    # Auto-detect
    if line.startswith("{"):
        return parse_json(line)
    return parse_logfmt(line)
