# Privacy Policy

## Data Collection

This tool collects **no data**. It does not:

- Send information to external servers
- Collect usage statistics or telemetry
- Track user behavior or ticket content
- Store any data between runs
- Write logs to disk without explicit user action

## Processing

All ticket analysis is performed:

- **Locally** on the user's machine
- **In-memory** during execution
- **Without persistence** unless the user saves output to a file

Ticket text provided via `--ticket` or `--file` is processed only during the current command execution and is not retained after the tool exits.

## Sample Data

The tool includes 8 built-in sample tickets that are:

- **Fictional and anonymized** — they do not represent real incidents
- **Generic examples** — they illustrate ticket categories and urgency levels
- **Distributed with the tool** — running `ticket-triage samples` is equivalent to reading them from the source code

No real customer data, real incident reports, or sensitive information is included.

## Output Privacy

When using `--format json` or `--file` output:

- Users are responsible for securing output files
- JSON data is not encrypted by the tool
- Sensitive ticket information should be redacted before analysis if privacy is a concern

## Third-Party Dependencies

This tool has **zero runtime dependencies** and does not rely on external packages. It uses only the Python standard library.

## Contact

Questions about privacy or data handling should be directed to `alibidhendi2000@gmail.com`.
