# Security Policy

## What Not to Commit

Never commit the following to this repository:

- Real IT support tickets containing sensitive information
- Customer data or personally identifiable information (PII)
- Actual system logs or diagnostic data
- API keys, authentication tokens, or credentials
- Real usernames, email addresses, or internal IP addresses
- Real employee names or personal details
- Actual breach reports or security incident details
- Passwords or secret keys

## Sample Data Guidelines

This tool is designed to work with **anonymized or synthetic ticket data only**. When testing or contributing:

- Use placeholder names (e.g., "User123", "Employee01")
- Use example domains (e.g., "example.com", "company.internal")
- Create realistic but fictional scenarios
- Never reference real security incidents or breaches involving your organization
- Do not include real system identifiers or serial numbers

## Reporting Security Issues

If you discover a security vulnerability in this tool:

1. **Do not open a public issue** on GitHub
2. **Contact the maintainer** directly via email at `alibidhendi2000@gmail.com`
3. **Include a detailed description** of the vulnerability, but avoid publishing working exploits
4. **Allow 30 days** for a response and patch before public disclosure

## Security Considerations

This tool performs **local keyword matching only** — it does not:

- Send ticket data to external services
- Store any data persistently
- Connect to networks or APIs
- Write to system logs or databases
- Modify system configuration

The classification results are advisory only and should not be treated as authoritative incident response guidance. Always follow your organization's incident response procedures and escalation policies.

## Data Handling

- All analysis is performed in-memory on the local machine
- Ticket text is not logged, cached, or persisted unless explicitly written to a file by the user
- JSON output can be piped to files or external systems at the user's discretion
- No telemetry or usage data is collected
