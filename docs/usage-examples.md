# Usage Examples

## Basic Single Ticket Analysis

### Account/Credential Issue

```bash
$ ticket-triage analyze --ticket "I can't log into my laptop this morning. It says my password is incorrect but I haven't changed it."
────────────────────────────────────────────────────
Ticket:      I can't log into my laptop this morning. It says my password is…
Category:    ACCOUNT  (confidence: high)
Urgency:     MEDIUM
Likely Cause: Expired or incorrect credentials
Recommended Steps:
  1. Confirm the user's identity before any account action.
  2. Check Active Directory / IdP for lock status and last login.
  3. Reset password via self-service portal or helpdesk procedure.
  4. Verify MFA enrollment and re-enroll if needed.
  5. Document the reset and notify the user through a verified channel.

Escalation:  Escalate to IAM team if account cannot be unlocked through standard helpdesk tools.
────────────────────────────────────────────────────
```

### Network/Connectivity Issue

```bash
$ ticket-triage analyze --ticket "Our entire office lost internet access about 20 minutes ago. Nobody can connect to anything."
────────────────────────────────────────────────────
Ticket:      Our entire office lost internet access about 20 minutes ago.…
Category:    NETWORK  (confidence: high)
Urgency:     HIGH
Likely Cause: Network or connectivity issue
Recommended Steps:
  1. Verify physical cable or Wi-Fi association.
  2. Run `ping 8.8.8.8` to test basic connectivity.
  3. Check if VPN client is running if required.
  4. Restart router/switch if in scope; else escalate to network team.
  5. Review firewall and proxy settings for the affected user.

Escalation:  Escalate to network engineering if restart/reconfigure does not restore connectivity within 15 minutes.
────────────────────────────────────────────────────
```

### Security/Phishing Alert

```bash
$ ticket-triage analyze --ticket "I received a very suspicious email asking me to click a link and verify my credentials. I may have entered my password."
────────────────────────────────────────────────────
Ticket:      I received a very suspicious email asking me to click a link…
Category:    SECURITY  (confidence: high)
Urgency:     CRITICAL
Likely Cause: Malware or security compromise
Recommended Steps:
  1. Isolate the affected device from the network immediately.
  2. Preserve evidence — do not wipe the machine yet.
  3. Escalate to the security team and incident response lead.
  4. Collect logs: event viewer, browser history, email headers.
  5. Inform the user not to click further links or open attachments.

Escalation:  Escalate immediately — security incidents require dedicated IR team response.
────────────────────────────────────────────────────
```

## Batch Processing from File

Create `tickets.txt`:

```
My laptop screen just went completely black and won't turn on.
Excel keeps crashing every time I try to open a file larger than 10 MB.
The shared printer on floor 3 is showing a paper jam error.
I'm not receiving any emails from external senders.
```

Process the file:

```bash
$ ticket-triage analyze --file tickets.txt
```

Each ticket is analyzed and displayed with full triage results.

## JSON Output

For integration with ticketing systems or scripting:

```bash
$ ticket-triage analyze --ticket "ransomware detected" --format json
[
  {
    "ticket_text": "ransomware detected",
    "category": "security",
    "urgency": "critical",
    "likely_cause": "Malware or security compromise",
    "steps": [
      "Isolate the affected device from the network immediately.",
      "Preserve evidence — do not wipe the machine yet.",
      "Escalate to the security team and incident response lead.",
      "Collect logs: event viewer, browser history, email headers.",
      "Inform the user not to click further links or open attachments."
    ],
    "escalation": "Escalate immediately — security incidents require dedicated IR team response.",
    "confidence": "high",
    "matched_terms": ["ransomware"],
    "category_scores": {
      "security": 0.5774,
      "network": 0.0,
      "account": 0.0,
      "hardware": 0.0,
      "software": 0.0,
      "email": 0.0,
      "printer": 0.0
    }
  }
]
```

### Batch file in JSON:

```bash
$ ticket-triage analyze --file tickets.txt --format json > results.json
```

This writes results for all tickets to `results.json`.

## View Sample Tickets

See how the tool handles realistic scenarios:

```bash
$ ticket-triage samples
```

Outputs all 8 built-in samples with their classification. Sample outputs include:

- A user who cannot log in before an urgent client presentation (account issue, high urgency)
- An entire office without internet access (network issue, high urgency)
- A suspected phishing email with potential credential compromise (security, critical)
- A laptop with catastrophic hardware failure (hardware, medium urgency)
- Excel crashes after a Windows Update (software, medium urgency)
- Printer paper jam blocking multiple users (printer, high urgency)
- External email delivery failures (email, medium urgency)
- Ransomware detected with antivirus alert (security, critical)

Get samples in JSON format:

```bash
$ ticket-triage samples --format json | jq '.[] | {category, urgency, confidence}'
{
  "category": "account",
  "urgency": "high",
  "confidence": "high"
}
{
  "category": "network",
  "urgency": "high",
  "confidence": "high"
}
...
```

## Stats Summary

Print category and urgency counts after a batch run:

```bash
$ ticket-triage analyze --file tickets.txt --stats
```

With JSON output, the envelope changes to an object with `results` and `stats` keys:

```bash
$ ticket-triage analyze --file tickets.txt --format json --stats
{
  "results": [...],
  "stats": {
    "category_counts": {"hardware": 1, "network": 1, "software": 1},
    "urgency_counts": {"high": 1, "medium": 2}
  }
}
```

Also works with `samples`:

```bash
$ ticket-triage samples --stats
$ ticket-triage samples --format json --stats
```

## Disabling Color Output

For piping to other tools or logging:

```bash
$ ticket-triage analyze --ticket "vpn down" --no-color > ticket_report.txt
```

Removes ANSI color codes from output, suitable for plain-text logs or email.

## Confidence Levels

The tool assigns confidence based on keyword density:

- **High**: 4+ matching keywords for the category
- **Medium**: 2-3 matching keywords
- **Low**: 1 matching keyword

Example ticket with various confidence levels:

```bash
$ ticket-triage analyze --ticket "internet is slow" --format json
# Output shows confidence: low (only 1 network keyword: "internet")

$ ticket-triage analyze --ticket "cannot connect wifi offline no internet" --format json
# Output shows confidence: high (4+ network keywords)
```

## Urgency Levels

Tickets are scored on urgency:

- **Critical**: Ransomware, data breach, server down, entire office affected, security incidents
- **High**: Multiple users affected, VPN down, deadline/urgent requests, blocking work
- **Medium**: Standard operational issues (default)
- **Low**: No rush, minor cosmetic issues, low-priority requests

Example:

```bash
$ ticket-triage analyze --ticket "printer paper jam" --format json
# urgency: medium

$ ticket-triage analyze --ticket "entire office wifi down cannot work at all" --format json
# urgency: high

$ ticket-triage analyze --ticket "ransomware detected on my machine" --format json
# urgency: critical
```
