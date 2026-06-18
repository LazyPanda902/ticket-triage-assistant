"""Argparse CLI entry point for ticket-triage-assistant."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from collections import Counter

from .triage import triage, SAMPLE_TICKETS, TriageResult

_URGENCY_COLORS = {
    "critical": "\033[91m",  # bright red
    "high": "\033[93m",      # yellow
    "medium": "\033[96m",    # cyan
    "low": "\033[92m",       # green
}
_RESET = "\033[0m"


def _colorize(urgency: str, text: str, use_color: bool) -> str:
    if not use_color:
        return text
    color = _URGENCY_COLORS.get(urgency, "")
    return f"{color}{text}{_RESET}"


def _render_text(result: TriageResult, use_color: bool) -> str:
    lines: list[str] = []
    sep = "─" * 60
    lines.append(sep)
    lines.append(f"Ticket:      {textwrap.shorten(result.ticket_text, 72)}")
    lines.append(
        f"Category:    {result.category.upper()}  "
        f"(confidence: {result.confidence})"
    )
    if result.matched_terms:
        terms_str = ", ".join(result.matched_terms[:6])
        lines.append(f"Matched:     {terms_str}")
    urgency_label = _colorize(result.urgency, result.urgency.upper(), use_color)
    lines.append(f"Urgency:     {urgency_label}")
    lines.append(f"Likely Cause: {result.likely_cause}")
    lines.append("")
    lines.append("Recommended Steps:")
    for i, step in enumerate(result.steps, 1):
        lines.append(f"  {i}. {step}")
    lines.append("")
    lines.append(f"Escalation:  {result.escalation}")
    lines.append(sep)
    return "\n".join(lines)


def _stats_dict(results: list[TriageResult]) -> dict:
    return {
        "category_counts": dict(Counter(r.category for r in results)),
        "urgency_counts": dict(Counter(r.urgency for r in results)),
    }


def _print_stats(results: list[TriageResult]) -> None:
    stats = _stats_dict(results)
    sep = "─" * 40
    lines = [sep, "Stats Summary:", "  Categories:"]
    for cat, count in sorted(stats["category_counts"].items()):
        lines.append(f"    {cat:<14} {count}")
    lines.append("  Urgency:")
    for urg in ("critical", "high", "medium", "low"):
        count = stats["urgency_counts"].get(urg, 0)
        if count:
            lines.append(f"    {urg:<14} {count}")
    lines.append(sep)
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def _cmd_analyze(args: argparse.Namespace) -> int:
    use_color = sys.stdout.isatty() and not args.no_color

    if args.file:
        try:
            raw = args.file.read()
        except OSError as exc:
            print(f"Error reading file: {exc}", file=sys.stderr)
            return 1
        tickets = [line.strip() for line in raw.splitlines() if line.strip()]
    elif args.ticket:
        tickets = [args.ticket]
    else:
        print("Error: provide --ticket TEXT or --file PATH.", file=sys.stderr)
        return 1

    results = [triage(t) for t in tickets]

    if args.format == "json":
        if args.stats:
            out = {"results": [r.to_dict() for r in results], "stats": _stats_dict(results)}
        else:
            out = [r.to_dict() for r in results]
        print(json.dumps(out, indent=2))
    else:
        for r in results:
            print(_render_text(r, use_color))
        if args.stats:
            _print_stats(results)

    return 0


def _cmd_samples(args: argparse.Namespace) -> int:
    use_color = sys.stdout.isatty() and not args.no_color

    results = [triage(t) for t in SAMPLE_TICKETS]

    if args.format == "json":
        if args.stats:
            out = {"results": [r.to_dict() for r in results], "stats": _stats_dict(results)}
        else:
            out = [r.to_dict() for r in results]
        print(json.dumps(out, indent=2))
    else:
        print(f"Running triage on {len(results)} sample tickets...\n")
        for r in results:
            print(_render_text(r, use_color))
        if args.stats:
            _print_stats(results)

    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parent.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    parent.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Print a category/urgency summary after results.",
    )

    parser = argparse.ArgumentParser(
        prog="ticket-triage",
        description="Classify IT support tickets by category, urgency, and recommended steps.",
        parents=[parent],
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # analyze subcommand
    analyze = sub.add_parser(
        "analyze",
        parents=[parent],
        help="Triage one ticket or a file of tickets (one per line).",
    )
    src = analyze.add_mutually_exclusive_group(required=True)
    src.add_argument("--ticket", metavar="TEXT", help="Ticket text to classify.")
    src.add_argument(
        "--file",
        metavar="PATH",
        type=argparse.FileType("r"),
        help="Path to a plain-text file with one ticket per line.",
    )

    # samples subcommand
    sub.add_parser(
        "samples",
        parents=[parent],
        help="Run triage on built-in sample tickets and display results.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _cmd_analyze(args)
    if args.command == "samples":
        return _cmd_samples(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
