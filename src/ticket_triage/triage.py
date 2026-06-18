"""Core triage engine: classify IT support tickets without external dependencies."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Final

# ---------------------------------------------------------------------------
# Category term profiles
# Each list is a "profile document" for the category.  Scoring uses a
# TF-IDF / cosine-similarity approach: terms that appear in only one
# category receive a higher IDF weight and dominate the classification.
# "crash" lives exclusively in software so that hardware tickets are
# disambiguated by their own high-IDF signals (bsod, blue screen, etc.).
# ---------------------------------------------------------------------------

_CATEGORY_TERMS: Final[dict[str, list[str]]] = {
    "network": [
        "internet", "wifi", "wi-fi", "vpn", "connection", "network", "ethernet",
        "dns", "ip address", "firewall", "bandwidth", "latency", "ping",
        "no access", "can't connect", "cannot connect", "offline", "disconnected",
        "router", "switch", "gateway", "packet loss", "connectivity",
    ],
    "account": [
        "password", "login", "locked out", "account", "credentials", "2fa",
        "mfa", "multi-factor", "access denied", "permission", "single sign-on",
        "sso", "reset password", "forgot password", "authentication",
        "active directory", "sign in", "identity",
    ],
    "security": [
        "virus", "malware", "ransomware", "phishing", "suspicious", "breach",
        "hack", "hacked", "unauthorized", "data leak", "spam", "scam",
        "anomalous", "intrusion", "threat", "infected", "suspicious email",
        "security incident", "compromised",
    ],
    "hardware": [
        "laptop", "computer", "monitor", "keyboard", "mouse", "screen",
        "blue screen", "bsod", "hardware", "battery", "charger",
        "won't turn on", "not turning on", "overheating", "fan", "ram", "disk",
        "hard drive", "ssd", "usb", "port", "clicking sound",
        "dell", "lenovo", "physical damage",
    ],
    "software": [
        "software", "application", "app", "install", "update", "upgrade",
        "error", "crash", "freeze", "frozen", "not responding", "slow",
        "driver", "windows", "macos", "linux", "office", "excel", "word",
        "browser", "chrome", "firefox", "edge",
        "not opening", "keeps crashing",
    ],
    "email": [
        "email", "e-mail", "inbox", "outlook", "gmail", "mail", "attachment",
        "send", "receive", "calendar", "meeting invite", "spam folder",
        "delivery failure", "mail flow",
    ],
    "printer": [
        "print", "printer", "scanner", "scan", "paper jam", "toner",
        "ink", "fax", "copier", "print queue", "print spooler",
    ],
}

_URGENCY_CRITICAL: Final[list[str]] = [
    "ransomware", "data breach", "breach", "hack", "hacked", "server down",
    "production down", "entire office", "all users", "everyone affected",
    "company-wide", "total outage", "business stopped", "security incident",
    "infected", "intrusion",
]

_URGENCY_HIGH: Final[list[str]] = [
    "multiple users", "several users", "team", "department", "vpn down",
    "cannot work", "urgent", "asap", "immediately", "critical", "blocked",
    "deadline", "meeting in", "presentation",
]

_URGENCY_LOW: Final[list[str]] = [
    "when possible", "low priority", "not urgent", "minor", "cosmetic",
    "nice to have", "whenever", "no rush", "eventually",
]

_CAUSE_MAP: Final[dict[str, list[str]]] = {
    "Expired or incorrect credentials": [
        "password", "locked out", "login", "credentials", "forgot password",
        "reset password", "authentication",
    ],
    "Hardware failure or damage": [
        "blue screen", "bsod", "won't turn on", "not turning on", "overheating",
        "fan", "hard drive", "ssd", "battery", "hardware",
    ],
    "Software bug or incompatible update": [
        "after update", "after upgrade", "error", "freeze", "frozen",
        "not responding", "crash", "driver",
    ],
    "Network or connectivity issue": [
        "internet", "wifi", "vpn", "disconnected", "offline", "no access",
        "cannot connect", "dns", "ip address",
    ],
    "Malware or security compromise": [
        "virus", "malware", "ransomware", "phishing", "suspicious", "hack",
        "hacked", "unauthorized", "infected", "scam",
    ],
    "Misconfiguration or permissions error": [
        "permission", "access denied", "not allowed", "cannot access",
        "group policy", "firewall", "blocked",
    ],
    "Hardware peripheral or driver issue": [
        "printer", "scanner", "usb", "keyboard", "mouse", "monitor",
        "screen", "port", "toner", "paper jam",
    ],
    "Email system or mail flow issue": [
        "email", "inbox", "outlook", "gmail", "attachment", "calendar",
        "spam folder",
    ],
}

_STEPS_MAP: Final[dict[str, list[str]]] = {
    "network": [
        "Verify physical cable or Wi-Fi association.",
        "Run `ping 8.8.8.8` to test basic connectivity.",
        "Check if VPN client is running if required.",
        "Restart router/switch if in scope; else escalate to network team.",
        "Review firewall and proxy settings for the affected user.",
    ],
    "account": [
        "Confirm the user's identity before any account action.",
        "Check Active Directory / IdP for lock status and last login.",
        "Reset password via self-service portal or helpdesk procedure.",
        "Verify MFA enrollment and re-enroll if needed.",
        "Document the reset and notify the user through a verified channel.",
    ],
    "security": [
        "Isolate the affected device from the network immediately.",
        "Preserve evidence — do not wipe the machine yet.",
        "Escalate to the security team and incident response lead.",
        "Collect logs: event viewer, browser history, email headers.",
        "Inform the user not to click further links or open attachments.",
    ],
    "hardware": [
        "Ask user for exact symptoms and any recent physical events.",
        "Attempt a forced restart; check for BIOS/POST error codes.",
        "Run built-in hardware diagnostics if available (e.g., Dell SupportAssist).",
        "Test with known-good peripherals to isolate the fault.",
        "Log serial number and initiate RMA or hardware replacement if confirmed.",
    ],
    "software": [
        "Identify the exact application and version producing the error.",
        "Capture the full error message or screenshot.",
        "Attempt a clean restart of the application.",
        "Check for pending OS/application updates and apply them.",
        "Reinstall the application if issues persist after updates.",
    ],
    "email": [
        "Confirm whether the issue affects sending, receiving, or both.",
        "Check mail server status and user's mailbox quota.",
        "Test webmail access to isolate client vs. server-side problem.",
        "Review spam/junk filters and safe-sender lists.",
        "Re-configure the mail profile if the desktop client is corrupted.",
    ],
    "printer": [
        "Check printer status on the control panel for error codes.",
        "Clear any paper jams and verify toner/ink levels.",
        "Confirm the printer is online in the print queue.",
        "Delete stuck jobs from the print spooler and restart the service.",
        "Reinstall or update the printer driver if queue issues persist.",
    ],
    "other": [
        "Gather a detailed description of the issue and reproduction steps.",
        "Check recent changes: updates, new installs, config changes.",
        "Attempt a system restart as a first remediation step.",
        "Search the internal knowledge base for similar incidents.",
        "Escalate if no resolution found within 30 minutes.",
    ],
}

_ESCALATION_TRIGGERS: Final[dict[str, str]] = {
    "security": "Escalate immediately — security incidents require dedicated IR team response.",
    "network": (
        "Escalate to network engineering if restart/reconfigure does not restore"
        " connectivity within 15 minutes."
    ),
    "hardware": "Escalate to hardware procurement/repair if on-site diagnostics confirm failure.",
    "account": "Escalate to IAM team if account cannot be unlocked through standard helpdesk tools.",
    "software": "Escalate to application owner or vendor support if reinstall does not resolve.",
    "email": "Escalate to mail admin or Microsoft/Google support for server-side mail flow issues.",
    "printer": "Escalate to facilities or vendor if hardware fault is confirmed.",
    "other": "Escalate to Tier 2 if issue cannot be reproduced or resolved in the first session.",
}


# ---------------------------------------------------------------------------
# TF-IDF infrastructure — built once at import time
# IDF = log((N+1) / (df+1)) + 1  (smoothed), where N = number of categories
# ---------------------------------------------------------------------------

def _build_idf(category_terms: dict[str, list[str]]) -> dict[str, float]:
    n = len(category_terms)
    df: Counter[str] = Counter()
    for terms in category_terms.values():
        for term in set(terms):
            df[term] += 1
    return {
        term: math.log((n + 1) / (count + 1)) + 1.0
        for term, count in df.items()
    }


def _normalize_vec(vec: dict[str, float]) -> dict[str, float]:
    mag = math.sqrt(sum(v * v for v in vec.values()))
    if mag == 0.0:
        return dict(vec)
    return {k: v / mag for k, v in vec.items()}


_IDF: Final[dict[str, float]] = _build_idf(_CATEGORY_TERMS)

# Pre-normalized category profile vectors (each has unit L2 norm)
_CATEGORY_VECTORS: Final[dict[str, dict[str, float]]] = {
    cat: _normalize_vec({term: _IDF.get(term, 1.0) for term in terms})
    for cat, terms in _CATEGORY_TERMS.items()
}

_SECURITY_OVERRIDE_TERMS: Final[set[str]] = {
    "phishing",
    "malware",
    "ransomware",
    "suspicious",
    "breach",
    "hack",
    "hacked",
    "unauthorized",
    "intrusion",
    "infected",
    "compromised",
}


def _category_from_scores(tokens: str, scores: dict[str, float]) -> str:
    """Choose final category with safety-first handling for security incidents."""
    if any(term in tokens for term in _SECURITY_OVERRIDE_TERMS):
        return "security"

    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0.0 else "other"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class TriageResult:
    ticket_text: str
    category: str
    urgency: str
    likely_cause: str
    steps: list[str] = field(default_factory=list)
    escalation: str = ""
    confidence: str = ""
    matched_terms: list[str] = field(default_factory=list)
    category_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> str:
    """Lowercase text for case-insensitive term matching."""
    return text.lower()


def _compute_category_scores(text: str) -> dict[str, float]:
    """Return cosine similarity of *text* against each category profile vector."""
    # Build ticket TF-IDF vector over the shared vocabulary
    ticket_vec: dict[str, float] = {}
    for terms in _CATEGORY_TERMS.values():
        for term in terms:
            if term in text:
                count = text.count(term)
                ticket_vec[term] = count * _IDF.get(term, 1.0)

    if not ticket_vec:
        return {cat: 0.0 for cat in _CATEGORY_TERMS}

    ticket_norm = _normalize_vec(ticket_vec)

    return {
        cat: round(
            sum(ticket_norm.get(t, 0.0) * w for t, w in cat_vec.items()),
            4,
        )
        for cat, cat_vec in _CATEGORY_VECTORS.items()
    }


def _score_category(tokens: str) -> str:
    """Return the best-matching category name for pre-tokenized ticket text."""
    scores = _compute_category_scores(tokens)
    return _category_from_scores(tokens, scores)


def _score_urgency(tokens: str) -> str:
    for signal in _URGENCY_CRITICAL:
        if signal in tokens:
            return "critical"
    for signal in _URGENCY_HIGH:
        if signal in tokens:
            return "high"
    for signal in _URGENCY_LOW:
        if signal in tokens:
            return "low"
    return "medium"


def _score_cause(tokens: str) -> str:
    scores: dict[str, int] = {cause: 0 for cause in _CAUSE_MAP}
    for cause, keywords in _CAUSE_MAP.items():
        for kw in keywords:
            if kw in tokens:
                scores[cause] += 1
    best = max(scores, key=lambda c: scores[c])
    return best if scores[best] > 0 else "Undetermined — further investigation required"


def _confidence(tokens: str, category: str) -> str:
    """Estimate classification confidence from matched term count."""
    hits = sum(1 for term in _CATEGORY_TERMS.get(category, []) if term in tokens)
    if hits >= 4:
        return "high"
    if hits >= 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def triage(ticket_text: str) -> TriageResult:
    """Classify a single free-text IT support ticket.

    Returns a TriageResult with category, urgency, likely cause, recommended
    steps, escalation guidance, confidence, matched terms, and per-category
    cosine similarity scores — all computed via stdlib-only TF-IDF scoring.
    """
    tokens = _tokenize(ticket_text)
    scores = _compute_category_scores(tokens)
    category = _category_from_scores(tokens, scores)

    matched = [t for t in _CATEGORY_TERMS.get(category, []) if t in tokens]

    return TriageResult(
        ticket_text=ticket_text,
        category=category,
        urgency=_score_urgency(tokens),
        likely_cause=_score_cause(tokens),
        steps=_STEPS_MAP.get(category, _STEPS_MAP["other"]),
        escalation=_ESCALATION_TRIGGERS.get(category, _ESCALATION_TRIGGERS["other"]),
        confidence=_confidence(tokens, category),
        matched_terms=matched,
        category_scores=scores,
    )


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_TICKETS: Final[list[str]] = [
    (
        "Hi, I can't log into my laptop this morning. It says my password is incorrect "
        "but I haven't changed it. I also can't get into Outlook or Teams. I have an "
        "urgent client presentation in 2 hours."
    ),
    (
        "Our entire office lost internet access about 20 minutes ago. Nobody can connect "
        "to anything — WiFi shows connected but no data. Even the wired machines are down. "
        "We cannot work at all."
    ),
    (
        "I received a very suspicious email asking me to click a link and verify my "
        "credentials. When I clicked it the page looked like our IT portal but the URL "
        "looked wrong. I may have entered my password. Please help."
    ),
    (
        "My laptop screen just went completely black and won't turn on anymore. I heard "
        "a clicking sound right before it died. I have important files on it. The laptop "
        "is a Dell Latitude issued last year."
    ),
    (
        "Excel keeps crashing every time I try to open a file larger than 10 MB. It "
        "started happening after this morning's Windows Update. Other Office apps seem "
        "fine. Running Office 365 on Windows 11."
    ),
    (
        "The shared printer on floor 3 is showing a paper jam error but there is no "
        "paper stuck inside. All jobs are queued and nobody can print. Several people "
        "on the floor need to print documents for a meeting."
    ),
    (
        "I'm not receiving any emails from external senders. Internal emails come through "
        "fine. People say they get delivery failure notices when emailing me. This started "
        "about 3 hours ago."
    ),
    (
        "My computer is running extremely slowly and the antivirus popped up saying it "
        "detected ransomware. I clicked dismiss by accident. The fan is running loudly. "
        "Please help immediately."
    ),
]
