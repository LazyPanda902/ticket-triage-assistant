# ticket-triage-assistant

[![CI](https://github.com/LazyPanda902/ticket-triage-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/LazyPanda902/ticket-triage-assistant/actions/workflows/ci.yml)

A command-line tool for classifying and triaging IT support tickets. The classifier uses a **stdlib-only TF-IDF / cosine-similarity** approach: each category has a profile of weighted terms, IDF weights penalise terms shared across categories, and the ticket is scored against every profile via cosine similarity. No external packages are required.

## Features

- **TF-IDF / cosine-similarity scoring** — discriminative term weighting, not raw keyword counts
- **Crash signal disambiguation** — hardware vs. software tickets resolved cleanly via per-category IDF weights
- **Automatic classification** into 8 categories (network, account, security, hardware, software, email, printer, other)
- **Urgency assessment** (critical / high / medium / low)
- **Root cause analysis** with likely-cause inference
- **Troubleshooting guidance** with category-specific steps
- **Escalation recommendations** for each issue type
- **Confidence scoring** and matched-term visibility in output
- **Per-category cosine scores** included in JSON for downstream use
- **Batch processing** from a plain-text file (one ticket per line)
- **Category/urgency stats** via `--stats`
- **Text and JSON output** formats
- **No external dependencies** — works offline with Python 3.11+

## Installation

```bash
pip install .
```

For development and testing:

```bash
pip install -e ".[dev]"
```

## Usage

### Analyze a single ticket

```bash
ticket-triage analyze --ticket "My laptop won't turn on and makes a clicking sound"
```

### Analyze tickets from a file

```bash
ticket-triage analyze --file tickets.txt
```

One ticket per line.

### JSON output

```bash
ticket-triage analyze --ticket "VPN is down" --format json
```

JSON includes `matched_terms` and `category_scores` in addition to the standard fields.

### Batch file in JSON

```bash
ticket-triage analyze --file tickets.txt --format json > results.json
```

### Stats summary

Print category and urgency counts after results:

```bash
ticket-triage analyze --file tickets.txt --stats
ticket-triage analyze --file tickets.txt --format json --stats
```

When `--stats` is combined with `--format json`, the output becomes an object with `"results"` and `"stats"` keys.

### View sample tickets

```bash
ticket-triage samples
ticket-triage samples --format json
ticket-triage samples --stats
```

### Disable color output

```bash
ticket-triage analyze --ticket "ransomware detected" --no-color
```

## How It Works

**Security-first routing** — before cosine scoring is evaluated, the classifier checks the ticket for a set of high-risk terms: `phishing`, `malware`, `ransomware`, `suspicious`, `breach`, `hack`, `hacked`, `unauthorized`, `intrusion`, `infected`, and `compromised`. If any of these terms appear, the ticket is immediately routed to the **security** category regardless of what the cosine scores say. This ensures that phishing attempts, suspicious login events, malware detections, system compromises, and similar incidents are never misclassified into lower-priority queues.

1. **Tokenization** — lowercase the ticket text.
2. **TF-IDF scoring** — for each category profile, compute term frequency × IDF for every vocabulary term present in the ticket.
3. **Cosine similarity** — normalise both the ticket vector and the pre-computed category vector, then take their dot product.  The category with the highest similarity wins.
4. **Crash disambiguation** — `"crash"` is assigned exclusively to the software profile; hardware tickets rely on high-IDF signals like `bsod`, `blue screen`, and `won't turn on`, so hardware and software tickets score clearly without overlap.
5. **Urgency and cause** — independent keyword passes over the same lowercased text.

## Categories and Examples

| Category | Discriminative signals | Example |
|----------|----------------------|---------|
| **network** | wifi, vpn, dns, packet loss, gateway | "Can't connect to VPN from home" |
| **account** | password, locked out, mfa, sso, credentials | "I'm locked out of my account" |
| **security** | ransomware, phishing, breach, intrusion | "I think I got phished, what do I do?" |
| **hardware** | bsod, blue screen, won't turn on, clicking sound | "My monitor won't turn on" |
| **software** | crash, freeze, not responding, driver, update | "Excel keeps crashing after the update" |
| **email** | inbox, outlook, delivery failure, mail flow | "I'm not receiving any emails" |
| **printer** | paper jam, toner, print queue, spooler | "The printer has a paper jam" |
| **other** | (no category matched) | Generic or mixed issues |

## JSON Output Schema

```json
[
  {
    "ticket_text": "...",
    "category": "software",
    "urgency": "medium",
    "likely_cause": "Software bug or incompatible update",
    "steps": ["..."],
    "escalation": "...",
    "confidence": "high",
    "matched_terms": ["excel", "crash", "update", "windows"],
    "category_scores": {
      "software": 0.6124,
      "hardware": 0.0812,
      "network": 0.0,
      "...": "..."
    }
  }
]
```

## Testing

```bash
pytest
pytest -v
pytest tests/test_triage.py::TestCrashDisambiguation
pytest tests/test_triage.py::TestStats
```

## Architecture

- **`src/ticket_triage/triage.py`** — TF-IDF/cosine engine, IDF precomputation, TriageResult dataclass
- **`src/ticket_triage/cli.py`** — argparse CLI, text/JSON rendering, stats summary
- **`tests/test_triage.py`** — 90 test functions across 14 test classes covering scoring, disambiguation, CLI, and stats

## License

MIT
