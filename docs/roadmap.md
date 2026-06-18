# Roadmap

## Current (v0.1)

- Stdlib-only TF-IDF / cosine-similarity classifier across 7 IT categories
- Urgency scoring (critical / high / medium / low)
- Root cause inference via keyword-weighted cause map
- Category-specific troubleshooting steps and escalation guidance
- Text and JSON output with matched terms and per-category cosine scores
- Batch processing from file, `--stats` summary flag
- GitHub Actions CI on Python 3.11 and 3.12

## Near-term (v0.2)

- **Weighted term profiles** — assign per-term weights within a category profile (e.g., `bsod` > `screen`) rather than uniform IDF weight, for finer score tuning.
- **Multi-label output** — return secondary categories when two profiles score within a small margin (e.g., a ticket about an Outlook crash scoring high for both `email` and `software`).
- **Custom term profiles via TOML** — let operators supply a local `profiles.toml` file that overrides or extends the built-in term lists without touching source code.
- **Structured log output** — `--format ndjson` for streaming one JSON object per line, useful for log aggregators.

## Medium-term (v0.3)

- **History file** — append triage results to a local JSONL log so operators can review classification trends over time.
- **Feedback loop CLI** — `ticket-triage feedback --id <id> --correct-category <cat>` to record misclassifications for offline review.
- **Minimal test corpus** — a small labelled dataset of anonymised tickets to measure F1 per category and catch regressions in the scoring algorithm.

## Long-term / Research

- **Lightweight TF-IDF trained from corpus** — if a labelled corpus is available, refit IDF weights from real ticket frequencies rather than from the hand-crafted profile documents.
- **Plugin categories** — a stable interface for adding entirely new categories (e.g., `cloud`, `mobile`) as installable plugins without forking the core package.
- **REST API mode** — optional `ticket-triage serve` subcommand exposing `POST /triage` for integration with web-based ticketing portals.

## Out of scope

- Machine-learning model serving (adds runtime dependencies and deployment complexity)
- Cloud connectivity or telemetry of any kind
- Storage of PII or ticket content beyond the local session
