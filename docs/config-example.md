# Configuration Reference

This tool requires **no configuration files**. All behaviour is controlled through command-line flags.

## Command-line flags

| Flag | Applies to | Default | Description |
|------|-----------|---------|-------------|
| `--format text\|json` | `analyze`, `samples` | `text` | Output format |
| `--no-color` | `analyze`, `samples` | off | Disable ANSI colour codes |
| `--stats` | `analyze`, `samples` | off | Print category/urgency summary after results |
| `--ticket TEXT` | `analyze` | — | Single ticket text to classify |
| `--file PATH` | `analyze` | — | Plain-text file with one ticket per line |

## Output formats

### Text (default)

Human-readable output with ANSI urgency colours:

- Red — Critical
- Yellow — High
- Cyan — Medium
- Green — Low

Pass `--no-color` to strip colour codes (useful for logs and pipes).

### JSON

Machine-readable output, suitable for scripting and integration with ticketing systems:

```json
[
  {
    "ticket_text": "...",
    "category": "network",
    "urgency": "high",
    "likely_cause": "Network or connectivity issue",
    "steps": ["..."],
    "escalation": "...",
    "confidence": "high",
    "matched_terms": ["vpn", "cannot connect", "offline"],
    "category_scores": {
      "network": 0.5812,
      "account": 0.0,
      "security": 0.0,
      "hardware": 0.0,
      "software": 0.0,
      "email": 0.0,
      "printer": 0.0
    }
  }
]
```

When `--stats` is also passed, the JSON becomes an object:

```json
{
  "results": [...],
  "stats": {
    "category_counts": {"network": 2, "software": 1},
    "urgency_counts": {"high": 2, "medium": 1}
  }
}
```

## Extending the classifier

The category term profiles live in `src/ticket_triage/triage.py` in the `_CATEGORY_TERMS` dictionary. Each entry is a list of terms that represent a category; IDF weights are recomputed automatically at import time, so adding or removing terms is the only change needed.

### Add a term to a category

Open `src/ticket_triage/triage.py` and locate `_CATEGORY_TERMS`:

```python
_CATEGORY_TERMS: Final[dict[str, list[str]]] = {
    "network": [
        # existing terms ...
        "5g", "cellular",   # add new terms here
    ],
    # ...
}
```

After saving, run `pytest` to confirm nothing regresses:

```bash
pip install -e ".[dev]"
pytest
```

### Add urgency signals

High, critical, and low urgency signals are short keyword lists near the top of `triage.py`:

```python
_URGENCY_HIGH: Final[list[str]] = [
    # existing signals ...
    "all hands",   # add here
]
```

### Add troubleshooting steps

Steps are looked up by category in `_STEPS_MAP`. Append a step string to the relevant list.

## Sample tickets

Eight built-in sample tickets are defined in `SAMPLE_TICKETS` at the end of `triage.py`. Run them with:

```bash
ticket-triage samples
ticket-triage samples --format json --stats
```
