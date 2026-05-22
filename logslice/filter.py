"""Field-based filtering for structured log entries."""

from typing import Any, Dict, List, Optional, Tuple


class FilterError(Exception):
    """Raised when a filter expression is invalid."""
    pass


OPERATORS = ("<=", ">=", "!=", "=", "<", ">")


def parse_filter_expr(expr: str) -> Tuple[str, str, str]:
    """Parse a filter expression like 'level=error' or 'status>=400'.

    Returns a (field, operator, value) tuple.
    Raises FilterError if the expression is malformed.
    """
    for op in OPERATORS:
        if op in expr:
            parts = expr.split(op, 1)
            field = parts[0].strip()
            value = parts[1].strip()
            if not field:
                raise FilterError(f"Missing field name in expression: {expr!r}")
            if not value:
                raise FilterError(f"Missing value in expression: {expr!r}")
            return field, op, value
    raise FilterError(
        f"No valid operator found in expression: {expr!r}. "
        f"Supported operators: {', '.join(OPERATORS)}"
    )


def _coerce(a: Any, b: str) -> Tuple[Any, Any]:
    """Try to coerce b to the same type as a for comparison."""
    if isinstance(a, (int, float)):
        try:
            return a, type(a)(b)
        except (ValueError, TypeError):
            pass
    return str(a), b


def matches_filter(record: Dict[str, Any], field: str, op: str, value: str) -> bool:
    """Return True if record[field] satisfies the operator/value condition."""
    if field not in record:
        return False

    rec_val, cmp_val = _coerce(record[field], value)

    try:
        if op == "=":
            return rec_val == cmp_val
        elif op == "!=":
            return rec_val != cmp_val
        elif op == "<":
            return rec_val < cmp_val
        elif op == "<=":
            return rec_val <= cmp_val
        elif op == ">":
            return rec_val > cmp_val
        elif op == ">=":
            return rec_val >= cmp_val
    except TypeError:
        return False
    return False


def apply_filters(
    record: Dict[str, Any], filters: List[Tuple[str, str, str]]
) -> bool:
    """Return True only if the record satisfies ALL filters."""
    return all(matches_filter(record, f, op, v) for f, op, v in filters)


def build_filters(expressions: List[str]) -> List[Tuple[str, str, str]]:
    """Parse a list of filter expression strings into (field, op, value) tuples."""
    return [parse_filter_expr(expr) for expr in expressions]
