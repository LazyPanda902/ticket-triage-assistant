# Testing Guide

## Running Tests

### Install test dependencies

```bash
pip install -e ".[dev]"
```

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_triage.py
```

### Run a specific test class

```bash
pytest tests/test_triage.py::TestTriageIntegration -v
```

### Run a specific test function

```bash
pytest tests/test_triage.py::TestTriageIntegration::test_network_ticket -v
```

### Run tests with coverage

```bash
pytest --cov=ticket_triage --cov-report=html
```

## Test Coverage

The test suite includes **90 test functions** organized into 14 test classes:

### TestTriageResult

Verifies the `TriageResult` dataclass:

- All fields are populated correctly
- `to_dict()` serialization includes all required keys
- Steps are returned as a list

```bash
pytest tests/test_triage.py::TestTriageResult -v
```

### TestTokenize

Tests the text preprocessing function:

- Lowercases uppercase text
- Handles empty strings

```bash
pytest tests/test_triage.py::TestTokenize -v
```

### TestScoreCategory

Verifies category classification for each category:

- Network tickets (wifi, vpn, internet)
- Account tickets (password, login, credentials)
- Security tickets (phishing, ransomware, breach)
- Hardware tickets (blue screen, won't turn on)
- Software tickets (crash, freeze, error)
- Email tickets (inbox, outlook, attachment)
- Printer tickets (paper jam, toner, print)
- Unknown/other tickets

```bash
pytest tests/test_triage.py::TestScoreCategory -v
```

### TestScoreUrgency

Verifies urgency classification:

- Critical urgency (ransomware, data breach, server down)
- High urgency (urgent, asap, multiple users)
- Low urgency (no rush, when possible)
- Medium urgency (default when no signals match)

```bash
pytest tests/test_triage.py::TestScoreUrgency -v
```

### TestScoreCause

Tests root cause inference:

- Credential/authentication causes
- Network/connectivity causes
- Malware/security causes
- Undetermined/fallback causes

```bash
pytest tests/test_triage.py::TestScoreCause -v
```

### TestConfidence

Verifies confidence scoring based on keyword density:

- High confidence (4+ keyword matches)
- Medium confidence (2-3 keyword matches)
- Low confidence (1 keyword match)

```bash
pytest tests/test_triage.py::TestConfidence -v
```

### TestTriageIntegration

End-to-end integration tests:

- Complete classification workflow for each category
- Security tickets are marked critical
- All 8 sample tickets classify without errors
- Empty tickets don't raise exceptions
- JSON serialization round-trips correctly

```bash
pytest tests/test_triage.py::TestTriageIntegration -v
```

### TestComputeCategoryScores

Verifies the TF-IDF scoring engine:

- All categories are represented in returned scores
- Empty text produces all-zero scores
- Scores are non-negative and ≤ 1.0
- Top-scoring category matches the expected classification

```bash
pytest tests/test_triage.py::TestComputeCategoryScores -v
```

### TestCrashDisambiguation

Verifies hardware vs. software tie-breaking:

- `"crash"` with hardware signals (bsod, blue screen) → hardware
- `"crash"` with software signals (excel, update) → software
- `"keeps crashing"` alone → software

```bash
pytest tests/test_triage.py::TestCrashDisambiguation -v
```

### TestStats

Verifies `--stats` behaviour for both `analyze` and `samples`:

- Text mode prints a stats summary block
- JSON mode wraps output in `{"results": [...], "stats": {...}}`
- `--stats` counts match the number of tickets processed

```bash
pytest tests/test_triage.py::TestStats -v
```

### TestMain

CLI end-to-end tests:

- Analyze single tickets
- Batch file processing
- JSON output format
- Text output format
- Sample tickets command
- Error handling for missing files
- Color output control
- Urgency classification in JSON output

Run a specific CLI test:

```bash
pytest tests/test_triage.py::TestMain::test_analyze_ticket_json_output -v
```

## Sample Test Runs

### All tests pass

```bash
$ pytest -q
90 passed in 0.5s
```

## What Tests Cover

The test suite verifies:

✅ **Classification accuracy** — tickets are assigned correct categories  
✅ **Urgency scoring** — critical/high/medium/low levels are appropriate  
✅ **Root cause inference** — likely causes match ticket symptoms  
✅ **Confidence calculation** — confidence levels reflect keyword density  
✅ **Troubleshooting steps** — steps are category-appropriate and detailed  
✅ **Escalation guidance** — escalation paths are correct per category  
✅ **CLI parsing** — all command-line arguments work correctly  
✅ **Output formatting** — text and JSON output are well-formed  
✅ **Color handling** — ANSI codes are applied or removed correctly  
✅ **Batch processing** — multiple tickets are handled in one run  
✅ **Error handling** — missing files and invalid inputs are handled gracefully  
✅ **Sample tickets** — all built-in samples classify without errors  

## Common Testing Tasks

### Verify a bug fix

After making a change to `triage.py` or `cli.py`, run tests to ensure no regressions:

```bash
pytest -x  # Stop on first failure
```

### Test a new category or keyword

Add a test case and verify it passes:

```python
# In tests/test_triage.py
def test_new_signal(self):
    result = _score_category("keyword related to new category")
    assert result == "new_category"
```

Then run:

```bash
pytest tests/test_triage.py::TestScoreCategory::test_new_signal -v
```

### Debug a failing test

Run a test with print statements:

```bash
pytest tests/test_triage.py::TestTriageIntegration::test_network_ticket -v -s
```

The `-s` flag captures stdout/print output.

### Generate a coverage report

```bash
pytest --cov=ticket_triage --cov-report=term-missing
```

Shows which lines of code are not covered by tests.
