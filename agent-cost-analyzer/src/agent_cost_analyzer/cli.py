"""CLI entry point for agent-cost-analyzer."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from agent_cost_analyzer.analyzer.comparison import compare_projects
from agent_cost_analyzer.analyzer.cost import analyze_costs
from agent_cost_analyzer.analyzer.failures import detect_failures
from agent_cost_analyzer.analyzer.tokens import analyze_tokens
from agent_cost_analyzer.models import AnalysisResult
from agent_cost_analyzer.parser.build_log import parse_session_logs
from agent_cost_analyzer.parser.cost_log import parse_cost_log
from agent_cost_analyzer.parser.phase_log import parse_phase_log
from agent_cost_analyzer.parser.progress import parse_progress
from agent_cost_analyzer.report.html import generate_comparison_html, generate_html_report
from agent_cost_analyzer.report.json_report import (
    generate_comparison_json,
    generate_json_report,
)
from agent_cost_analyzer.report.markdown import (
    generate_comparison_markdown,
    generate_markdown_report,
)

_ALL_FORMATS = {"html", "json", "md"}


def _parse_date(value: str) -> date:
    """Parse YYYY-MM-DD date string; raises ArgumentTypeError on failure."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {value!r}. Expected YYYY-MM-DD."
        )


def _parse_formats(value: str) -> set[str]:
    """Parse comma-separated format list, validate each token."""
    parts = {p.strip().lower() for p in value.split(",") if p.strip()}
    unknown = parts - _ALL_FORMATS
    if unknown:
        raise argparse.ArgumentTypeError(
            f"Unknown format(s): {', '.join(sorted(unknown))}. "
            f"Valid options: html, json, md"
        )
    return parts


def _analyze_project(
    project_dir: Path,
    after: date | None,
    before: date | None,
) -> AnalysisResult:
    """Run full analysis pipeline on a single project directory.

    Expects .harness-logs/ subdirectory inside project_dir containing cost.log.
    Raises FileNotFoundError if cost.log is missing.
    """
    logs_dir = project_dir / ".harness-logs"
    cost_log_path = logs_dir / "cost.log"
    phase_log_path = logs_dir / "phase.log"
    progress_path = project_dir / "progress.txt"

    # Parsers
    cost_entries = parse_cost_log(cost_log_path, after=after, before=before)
    phase_events = parse_phase_log(phase_log_path)
    session_errors = parse_session_logs(logs_dir)
    progress = parse_progress(progress_path)

    # Analyzers
    cost_breakdown = analyze_costs(cost_entries)
    token_analysis = analyze_tokens(cost_entries)
    failure_patterns = detect_failures(cost_entries, phase_events, session_errors)

    # Summary dict
    timeline = cost_breakdown.timeline
    duration_minutes: float = 0.0
    if len(timeline) >= 2:
        delta = timeline[-1][0] - timeline[0][0]
        duration_minutes = delta.total_seconds() / 60.0

    summary: dict = {
        "total_cost": cost_breakdown.total_cost,
        "total_iterations": cost_breakdown.total_iterations,
        "duration_minutes": duration_minutes,
        "stuck_count": len(failure_patterns.stuck_events),
        "build_failure_rate": failure_patterns.build_failure_rate,
    }

    return AnalysisResult(
        project=progress,
        summary=summary,
        cost_breakdown=cost_breakdown,
        token_analysis=token_analysis,
        failure_patterns=failure_patterns,
        timeline=timeline,
    )


def _run_analyze(args: argparse.Namespace) -> int:
    """Execute the analyze subcommand. Returns exit code."""
    project_dir = Path(args.project).resolve()
    output_dir = Path(args.output).resolve()
    formats: set[str] = args.format

    try:
        result = _analyze_project(project_dir, args.after, args.before)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    if "json" in formats:
        path = generate_json_report(result, output_dir)
        print(f"JSON report: {path}")
    if "md" in formats:
        path = generate_markdown_report(result, output_dir)
        print(f"Markdown report: {path}")
    if "html" in formats:
        path = generate_html_report(result, output_dir)
        print(f"HTML report: {path}")

    return 0


def _run_compare(args: argparse.Namespace) -> int:
    """Execute the compare subcommand. Returns exit code."""
    project_paths = [p.strip() for p in args.projects.split(",") if p.strip()]
    if len(project_paths) < 2:
        print(
            "Error: --projects requires at least 2 comma-separated project paths.",
            file=sys.stderr,
        )
        return 1

    output_dir = Path(args.output).resolve()
    formats: set[str] = args.format

    results: list[tuple[str, AnalysisResult]] = []
    for raw_path in project_paths:
        project_dir = Path(raw_path).resolve()
        try:
            result = _analyze_project(project_dir, args.after, args.before)
        except FileNotFoundError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        results.append((project_dir.name, result))

    output_dir.mkdir(parents=True, exist_ok=True)

    comparison = compare_projects(results)

    if "json" in formats:
        path = generate_comparison_json(comparison, output_dir)
        print(f"Comparison JSON: {path}")
    if "md" in formats:
        path = generate_comparison_markdown(comparison, output_dir)
        print(f"Comparison Markdown: {path}")
    if "html" in formats:
        path = generate_comparison_html(comparison, output_dir)
        print(f"Comparison HTML: {path}")

    return 0


def _run_watch(_args: argparse.Namespace) -> int:
    """Execute the watch subcommand (stub). Returns exit code."""
    print("watch mode is not yet implemented")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build and return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="cost-analyze",
        description="Analyze AI agent harness execution logs and generate cost reports.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- analyze subcommand ---
    analyze_p = subparsers.add_parser("analyze", help="Analyze a single project")
    analyze_p.add_argument(
        "--project",
        required=True,
        metavar="PATH",
        help="Path to the project directory containing .harness-logs/",
    )
    analyze_p.add_argument(
        "--output",
        default="./report",
        metavar="DIR",
        help="Output directory for reports (default: ./report)",
    )
    analyze_p.add_argument(
        "--after",
        type=_parse_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Include only entries on or after this date (UTC)",
    )
    analyze_p.add_argument(
        "--before",
        type=_parse_date,
        default=None,
        metavar="YYYY-MM-DD",
        help="Exclude entries on or after this date (UTC)",
    )
    analyze_p.add_argument(
        "--format",
        type=_parse_formats,
        default=_ALL_FORMATS,
        metavar="FMT",
        help="Comma-separated output formats: html,json,md (default: all)",
    )

    # --- compare subcommand ---
    compare_p = subparsers.add_parser("compare", help="Compare multiple projects")
    compare_p.add_argument(
        "--projects",
        required=True,
        metavar="PATHS",
        help="Comma-separated list of project directories (≥2)",
    )
    compare_p.add_argument(
        "--output",
        default="./report",
        metavar="DIR",
        help="Output directory for reports (default: ./report)",
    )
    compare_p.add_argument(
        "--after",
        type=_parse_date,
        default=None,
        metavar="YYYY-MM-DD",
    )
    compare_p.add_argument(
        "--before",
        type=_parse_date,
        default=None,
        metavar="YYYY-MM-DD",
    )
    compare_p.add_argument(
        "--format",
        type=_parse_formats,
        default=_ALL_FORMATS,
        metavar="FMT",
        help="Comma-separated output formats: html,json,md (default: all)",
    )

    # --- watch subcommand ---
    watch_p = subparsers.add_parser("watch", help="Watch mode (not yet implemented)")
    watch_p.add_argument(
        "--project",
        required=False,
        metavar="PATH",
        help="Path to the project directory (ignored)",
    )

    return parser


def main() -> None:
    """Entry point for cost-analyze CLI."""
    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None or args.command == "analyze":
        # Default to analyze when no subcommand given — but --project is required.
        if args.command is None:
            # Re-parse treating all positional args as analyze subcommand
            # If --project wasn't given, argparse already would fail.
            # Re-parse with explicit subcommand to trigger required checks.
            args = parser.parse_args(["analyze"] + sys.argv[1:])
        sys.exit(_run_analyze(args))
    elif args.command == "compare":
        sys.exit(_run_compare(args))
    elif args.command == "watch":
        sys.exit(_run_watch(args))
    else:
        parser.print_help()
        sys.exit(1)
