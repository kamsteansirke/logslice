# logslice

Stream and filter structured log files by time range or field values from the terminal.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Filter logs by time range
logslice app.log --from "2024-01-15T10:00:00" --to "2024-01-15T11:00:00"

# Filter by field value
logslice app.log --field level=error

# Combine filters and stream from stdin
cat app.log | logslice --field service=api --from "2024-01-15T09:00:00"

# Output as pretty-printed JSON
logslice app.log --field level=warn --pretty
```

logslice expects newline-delimited JSON (NDJSON) log files by default. Each line should be a valid JSON object with at least a timestamp field (configurable via `--time-field`).

```bash
# Use a custom timestamp field name
logslice app.log --time-field ts --from "2024-01-15T10:00:00"
```

---

## Options

| Flag | Description |
|------|-------------|
| `--from` | Start of time range (ISO 8601) |
| `--to` | End of time range (ISO 8601) |
| `--field` | Filter by `key=value` pair (repeatable) |
| `--time-field` | Timestamp field name (default: `timestamp`) |
| `--pretty` | Pretty-print JSON output |

---

## License

MIT © 2024 yourname