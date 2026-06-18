"""Tests for ticket_triage core logic and CLI."""

import json
import pytest

from ticket_triage.triage import (
    triage,
    TriageResult,
    SAMPLE_TICKETS,
    _score_category,
    _score_urgency,
    _score_cause,
    _confidence,
    _tokenize,
    _compute_category_scores,
)
from ticket_triage.cli import build_parser, main, _render_text, _colorize


# ---------------------------------------------------------------------------
# TriageResult
# ---------------------------------------------------------------------------

class TestTriageResult:
    def test_fields_populated(self):
        result = triage("I cannot connect to the internet")
        assert isinstance(result, TriageResult)
        assert result.ticket_text == "I cannot connect to the internet"
        assert result.category
        assert result.urgency
        assert result.likely_cause
        assert len(result.steps) > 0
        assert result.escalation
        assert result.confidence

    def test_to_dict_keys(self):
        result = triage("password reset needed")
        d = result.to_dict()
        for key in ("ticket_text", "category", "urgency", "likely_cause", "steps", "escalation", "confidence"):
            assert key in d

    def test_to_dict_steps_is_list(self):
        result = triage("my printer has a paper jam")
        assert isinstance(result.to_dict()["steps"], list)

    def test_matched_terms_is_list(self):
        result = triage("I cannot connect to the internet")
        assert isinstance(result.matched_terms, list)

    def test_matched_terms_in_ticket(self):
        result = triage("laptop screen went black won't turn on")
        for term in result.matched_terms:
            assert term in result.ticket_text.lower()

    def test_category_scores_is_dict(self):
        result = triage("ransomware detected on my machine")
        assert isinstance(result.category_scores, dict)
        assert "security" in result.category_scores
        assert "network" in result.category_scores

    def test_category_scores_winner_matches_category(self):
        result = triage("printer paper jam toner low")
        best = max(result.category_scores, key=lambda c: result.category_scores[c])
        assert best == result.category

    def test_category_scores_in_to_dict(self):
        result = triage("vpn is down cannot connect")
        d = result.to_dict()
        assert "matched_terms" in d
        assert "category_scores" in d
        assert isinstance(d["category_scores"], dict)

    def test_category_scores_are_floats(self):
        result = triage("email inbox outlook")
        for score in result.category_scores.values():
            assert isinstance(score, float)

    def test_empty_ticket_matched_terms_empty(self):
        result = triage("")
        assert result.matched_terms == []


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------

class TestTokenize:
    def test_lowercases(self):
        assert _tokenize("VPN DOWN URGENT") == "vpn down urgent"

    def test_empty(self):
        assert _tokenize("") == ""


# ---------------------------------------------------------------------------
# _compute_category_scores
# ---------------------------------------------------------------------------

class TestComputeCategoryScores:
    def test_returns_all_categories(self):
        scores = _compute_category_scores("vpn is down")
        expected = {"network", "account", "security", "hardware", "software", "email", "printer"}
        assert set(scores.keys()) == expected

    def test_empty_text_all_zeros(self):
        scores = _compute_category_scores("")
        assert all(v == 0.0 for v in scores.values())

    def test_network_text_highest_for_network(self):
        scores = _compute_category_scores("cannot connect wifi vpn offline")
        assert scores["network"] == max(scores.values())

    def test_scores_are_non_negative(self):
        scores = _compute_category_scores("printer paper jam toner")
        assert all(v >= 0.0 for v in scores.values())

    def test_scores_at_most_one(self):
        scores = _compute_category_scores("ransomware malware virus phishing breach")
        assert all(v <= 1.0 for v in scores.values())


# ---------------------------------------------------------------------------
# _score_category
# ---------------------------------------------------------------------------

class TestScoreCategory:
    def test_network_ticket(self):
        assert _score_category("cannot connect to wifi") == "network"

    def test_account_ticket(self):
        assert _score_category("locked out of account password reset") == "account"

    def test_security_ticket(self):
        assert _score_category("phishing email suspicious") == "security"

    def test_hardware_ticket(self):
        assert _score_category("laptop blue screen bsod crash") == "hardware"

    def test_software_ticket(self):
        assert _score_category("excel freeze not responding") == "software"

    def test_email_ticket(self):
        assert _score_category("inbox outlook email attachment") == "email"

    def test_printer_ticket(self):
        assert _score_category("printer paper jam toner") == "printer"

    def test_unknown_returns_other(self):
        assert _score_category("xyz qrs") == "other"


# ---------------------------------------------------------------------------
# Crash disambiguation: hardware vs software
# ---------------------------------------------------------------------------

class TestCrashDisambiguation:
    def test_crash_with_strong_hardware_context_is_hardware(self):
        # "laptop", "blue screen" are hardware-exclusive → hardware wins
        result = triage("My laptop has a blue screen and the system crashed")
        assert result.category == "hardware"

    def test_crash_with_software_context_is_software(self):
        result = triage("Excel crashed after the Windows update")
        assert result.category == "software"

    def test_app_keeps_crashing_is_software(self):
        result = triage("The application keeps crashing every single day")
        assert result.category == "software"

    def test_bsod_alone_is_hardware(self):
        result = triage("Got a bsod this morning, laptop restarted")
        assert result.category == "hardware"


# ---------------------------------------------------------------------------
# _score_urgency
# ---------------------------------------------------------------------------

class TestScoreUrgency:
    def test_critical_on_ransomware(self):
        assert _score_urgency("ransomware detected on laptop") == "critical"

    def test_critical_on_breach(self):
        assert _score_urgency("data breach reported") == "critical"

    def test_high_on_urgent(self):
        assert _score_urgency("urgent fix needed asap") == "high"

    def test_high_on_multiple_users(self):
        assert _score_urgency("multiple users affected") == "high"

    def test_low_on_no_rush(self):
        assert _score_urgency("no rush whenever you get a chance") == "low"

    def test_medium_default(self):
        assert _score_urgency("my keyboard is slow") == "medium"


# ---------------------------------------------------------------------------
# _score_cause
# ---------------------------------------------------------------------------

class TestScoreCause:
    def test_credential_cause(self):
        cause = _score_cause("forgot password locked out")
        assert "credential" in cause.lower() or "Expired" in cause

    def test_network_cause(self):
        cause = _score_cause("cannot connect vpn offline internet")
        assert "network" in cause.lower() or "connectivity" in cause.lower()

    def test_malware_cause(self):
        cause = _score_cause("virus malware ransomware infected")
        assert "malware" in cause.lower() or "security" in cause.lower() or "Malware" in cause

    def test_undetermined_on_blank(self):
        cause = _score_cause("    ")
        assert "undetermined" in cause.lower() or "investigation" in cause.lower()


# ---------------------------------------------------------------------------
# _confidence
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_high_confidence(self):
        tokens = "password login locked out credentials reset password authentication"
        assert _confidence(tokens, "account") == "high"

    def test_medium_confidence(self):
        tokens = "password locked out"
        assert _confidence(tokens, "account") == "medium"

    def test_low_confidence(self):
        tokens = "password"
        assert _confidence(tokens, "account") == "low"


# ---------------------------------------------------------------------------
# triage() integration
# ---------------------------------------------------------------------------

class TestTriageIntegration:
    def test_network_ticket(self):
        result = triage("I can't connect to the internet, WiFi is down and VPN fails")
        assert result.category == "network"
        assert any("ping" in s.lower() or "vpn" in s.lower() or "cable" in s.lower() for s in result.steps)

    def test_security_ticket_is_critical(self):
        result = triage("Our server has been hacked and there is a data breach")
        assert result.category == "security"
        assert result.urgency == "critical"

    def test_account_ticket(self):
        result = triage("I forgot my password and I am locked out of my account")
        assert result.category == "account"

    def test_hardware_ticket_cause(self):
        result = triage("My laptop has a blue screen and won't turn on")
        assert result.category == "hardware"

    def test_printer_ticket(self):
        result = triage("The printer has a paper jam and toner is low")
        assert result.category == "printer"

    def test_sample_tickets_all_produce_results(self):
        for ticket in SAMPLE_TICKETS:
            result = triage(ticket)
            assert isinstance(result, TriageResult)
            assert result.category
            assert result.urgency in ("critical", "high", "medium", "low")

    def test_empty_ticket_does_not_raise(self):
        result = triage("")
        assert isinstance(result, TriageResult)

    def test_to_dict_round_trip(self):
        result = triage("My email inbox is not loading in Outlook")
        d = result.to_dict()
        assert d["category"] == result.category
        assert d["urgency"] == result.urgency
        assert d["steps"] == result.steps

    def test_excel_crash_after_update_is_software(self):
        result = triage(
            "Excel keeps crashing every time I try to open a file. "
            "It started happening after this morning's Windows Update."
        )
        assert result.category == "software"

    def test_ransomware_sample_is_security_critical(self):
        result = triage(SAMPLE_TICKETS[7])  # ransomware sample
        assert result.category == "security"
        assert result.urgency == "critical"


# ---------------------------------------------------------------------------
# _colorize
# ---------------------------------------------------------------------------

class TestColorize:
    def test_no_color_returns_plain(self):
        assert _colorize("critical", "CRITICAL", False) == "CRITICAL"

    def test_color_wraps_with_ansi(self):
        out = _colorize("critical", "CRITICAL", True)
        assert "\033[" in out
        assert "CRITICAL" in out

    def test_unknown_urgency_no_color_code(self):
        out = _colorize("unknown_level", "TEXT", True)
        assert "TEXT" in out


# ---------------------------------------------------------------------------
# _render_text
# ---------------------------------------------------------------------------

class TestRenderText:
    def test_contains_category(self):
        result = triage("I cannot connect to VPN")
        rendered = _render_text(result, use_color=False)
        assert result.category.upper() in rendered

    def test_contains_urgency(self):
        result = triage("urgent: server down production outage")
        rendered = _render_text(result, use_color=False)
        assert result.urgency.upper() in rendered

    def test_contains_steps_numbered(self):
        result = triage("printer paper jam")
        rendered = _render_text(result, use_color=False)
        assert "1." in rendered

    def test_contains_escalation(self):
        result = triage("printer paper jam")
        rendered = _render_text(result, use_color=False)
        assert "Escalation" in rendered

    def test_matched_terms_shown_when_present(self):
        result = triage("printer paper jam toner ink")
        rendered = _render_text(result, use_color=False)
        # At least one matched term should appear in the Matched line
        assert "Matched" in rendered


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_builds_without_error(self):
        parser = build_parser()
        assert parser is not None

    def test_analyze_requires_ticket_or_file(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["analyze"])
        assert exc.value.code == 2

    def test_analyze_with_ticket_parses(self):
        parser = build_parser()
        args = parser.parse_args(["analyze", "--ticket", "password reset"])
        assert args.ticket == "password reset"
        assert args.command == "analyze"

    def test_format_default_is_text(self):
        parser = build_parser()
        args = parser.parse_args(["samples"])
        assert args.format == "text"

    def test_format_json_accepted(self):
        parser = build_parser()
        args = parser.parse_args(["analyze", "--ticket", "test ticket", "--format=json"])
        assert args.format == "json"

    def test_no_color_flag(self):
        parser = build_parser()
        args = parser.parse_args(["analyze", "--ticket", "test", "--no-color"])
        assert args.no_color is True

    def test_invalid_format_raises_system_exit(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["analyze", "--ticket", "test", "--format=xml"])
        assert exc.value.code == 2

    def test_samples_command_parses(self):
        parser = build_parser()
        args = parser.parse_args(["samples"])
        assert args.command == "samples"

    def test_ticket_and_file_are_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc:
            parser.parse_args(["analyze", "--ticket", "foo", "--file", "/dev/null"])
        assert exc.value.code == 2

    def test_stats_flag_parses_on_analyze(self):
        parser = build_parser()
        args = parser.parse_args(["analyze", "--ticket", "test", "--stats"])
        assert args.stats is True

    def test_stats_flag_parses_on_samples(self):
        parser = build_parser()
        args = parser.parse_args(["samples", "--stats"])
        assert args.stats is True

    def test_stats_default_false(self):
        parser = build_parser()
        args = parser.parse_args(["samples"])
        assert args.stats is False


# ---------------------------------------------------------------------------
# main() CLI entry point
# ---------------------------------------------------------------------------

class TestMain:
    def test_no_command_returns_zero(self, capsys):
        result = main([])
        assert result == 0

    def test_analyze_ticket_returns_zero(self, capsys):
        result = main(["analyze", "--ticket", "I cannot connect to the internet"])
        assert result == 0

    def test_analyze_ticket_json_output(self, capsys):
        result = main(["analyze", "--ticket", "vpn is down", "--format=json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == 1
        assert "category" in data[0]

    def test_analyze_ticket_json_includes_matched_terms(self, capsys):
        main(["analyze", "--ticket", "vpn is down cannot connect", "--format=json"])
        data = json.loads(capsys.readouterr().out)
        assert "matched_terms" in data[0]
        assert "category_scores" in data[0]

    def test_analyze_no_ticket_or_file_returns_one(self, capsys):
        result = main(["analyze", "--ticket", ""])
        assert isinstance(result, int)

    def test_samples_returns_zero(self, capsys):
        result = main(["samples"])
        assert result == 0

    def test_samples_json_output(self, capsys):
        result = main(["samples", "--format=json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert len(data) == len(SAMPLE_TICKETS)
        for item in data:
            assert "urgency" in item
            assert "steps" in item

    def test_analyze_from_file(self, tmp_path, capsys):
        ticket_file = tmp_path / "tickets.txt"
        ticket_file.write_text("VPN is down\nprinter paper jam\n")
        result = main(["analyze", f"--file={ticket_file}", "--format=json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2

    def test_analyze_from_missing_file_returns_error(self, tmp_path):
        missing = tmp_path / "nonexistent.txt"
        with pytest.raises(SystemExit) as exc:
            main(["analyze", f"--file={missing}"])
        assert exc.value.code == 2

    def test_ransomware_ticket_urgency_critical(self, capsys):
        result = main(["analyze", "--ticket", "ransomware detected on my machine", "--format=json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data[0]["urgency"] == "critical"

    def test_no_color_flag_suppresses_ansi(self, capsys):
        result = main(["analyze", "--ticket", "critical ransomware breach", "--no-color"])
        assert result == 0
        captured = capsys.readouterr()
        assert "\033[" not in captured.out


# ---------------------------------------------------------------------------
# --stats option
# ---------------------------------------------------------------------------

class TestStats:
    def test_analyze_stats_text_prints_summary(self, tmp_path, capsys):
        f = tmp_path / "tickets.txt"
        f.write_text("VPN is down\nprinter paper jam\n")
        result = main(["analyze", f"--file={f}", "--stats"])
        assert result == 0
        out = capsys.readouterr().out
        assert "Stats" in out

    def test_analyze_stats_json_has_results_and_stats_keys(self, tmp_path, capsys):
        f = tmp_path / "tickets.txt"
        f.write_text("VPN is down\nprinter paper jam\n")
        result = main(["analyze", f"--file={f}", "--format=json", "--stats"])
        assert result == 0
        data = json.loads(capsys.readouterr().out)
        assert "results" in data
        assert "stats" in data
        assert "category_counts" in data["stats"]
        assert "urgency_counts" in data["stats"]

    def test_analyze_stats_json_results_count_correct(self, tmp_path, capsys):
        f = tmp_path / "tickets.txt"
        f.write_text("VPN is down\nprinter paper jam\nexcel crash\n")
        main(["analyze", f"--file={f}", "--format=json", "--stats"])
        data = json.loads(capsys.readouterr().out)
        total = sum(data["stats"]["category_counts"].values())
        assert total == 3

    def test_samples_stats_text(self, capsys):
        result = main(["samples", "--stats"])
        assert result == 0
        out = capsys.readouterr().out
        assert "Stats" in out

    def test_samples_stats_json_structure(self, capsys):
        result = main(["samples", "--format=json", "--stats"])
        assert result == 0
        data = json.loads(capsys.readouterr().out)
        assert "results" in data
        assert len(data["results"]) == len(SAMPLE_TICKETS)
        total = sum(data["stats"]["category_counts"].values())
        assert total == len(SAMPLE_TICKETS)

    def test_samples_no_stats_returns_plain_list(self, capsys):
        main(["samples", "--format=json"])
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)

    def test_analyze_no_stats_returns_plain_list(self, tmp_path, capsys):
        f = tmp_path / "t.txt"
        f.write_text("VPN is down\n")
        main(["analyze", f"--file={f}", "--format=json"])
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
