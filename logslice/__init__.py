"""logslice — Stream and filter structured log files by time range or field values."""

__version__ = "0.1.0"
__author__ = "logslice contributors"

from logslice.parser import parse_line, parse_json, parse_logfmt, ParseError

__all__ = [
    "parse_line",
    "parse_json",
    "parse_logfmt",
    "ParseError",
]
