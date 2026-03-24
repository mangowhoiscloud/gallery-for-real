"""CLI entry point — agent-eval command with run/compare/suite/report subcommands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from agent_eval.backends.base import AgentBackend
from agent_eval.config import load_suite_config
from agent_eval.report import discover_results, generate_report
from agent_eval.runner import run_compare, run_single, run_suite


def _make_backend(agent_name: str) -> AgentBackend:
    """Instantiate an AgentBackend from an agent name string.

    Supported names:
    - "mock"           — MockBackend (test/demo; uses current directory as fixture_dir)
    - "claude"         — ClaudeBackend with default model "sonnet"
    - "claude:<model>" — ClaudeBackend with explicit model

    Raises ValueError for unrecognised agents.
    Raises ImportError if the backend module is not yet available.
    """
    parts = agent_name.split(":", 1)
    name = parts[0].lower()

    if name == "mock":
        from agent_eval.backends.mock import MockBackend  # noqa: PLC0415

        return MockBackend(Path("."))

    if name == "claude":
        model = parts[1] if len(parts) > 1 else "sonnet"
        from agent_eval.backends.claude import ClaudeBackend  # noqa: PLC0415

        return ClaudeBackend(model)

    raise ValueError(f"Unknown agent backend: {agent_name!r}")


def _cmd_run(args: argparse.Namespace) -> int:
    """Handle 'agent-eval run' subcommand. Returns exit code."""
    benchmark_dir = Path(args.benchmark)
    if not benchmark_dir.is_dir():
        print(f"error: benchmark directory not found: {benchmark_dir}", file=sys.stderr)
        return 2

    try:
        backend = _make_backend(args.agent)
    except (ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output)
    result = run_single(benchmark_dir, backend, output_dir)
    return 0 if result.success else 1


def _cmd_compare(args: argparse.Namespace) -> int:
    """Handle 'agent-eval compare' subcommand. Returns exit code."""
    benchmark_dir = Path(args.benchmark)
    if not benchmark_dir.is_dir():
        print(f"error: benchmark directory not found: {benchmark_dir}", file=sys.stderr)
        return 2

    agent_names = [a.strip() for a in args.agents.split(",")]
    try:
        backends = [_make_backend(name) for name in agent_names]
    except (ValueError, ImportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    output_dir = Path(args.output)
    results = run_compare(benchmark_dir, backends, output_dir)
    failed = sum(1 for r in results if not r.success)
    return 1 if failed else 0


def _cmd_suite(args: argparse.Namespace) -> int:
    """Handle 'agent-eval suite' subcommand. Returns exit code."""
    config_path = Path(args.config)
    if not config_path.is_file():
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 2

    try:
        suite_config = load_suite_config(config_path)
    except (ValueError, Exception) as exc:
        print(f"error: invalid config: {exc}", file=sys.stderr)
        return 2

    if args.output is not None:
        suite_config.output = args.output

    def backend_factory(agent_name: str) -> AgentBackend:
        try:
            return _make_backend(agent_name)
        except (ValueError, ImportError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(2)

    results = run_suite(suite_config, backend_factory)
    failed = sum(1 for r in results if not r.success)
    return 1 if failed else 0


def _cmd_report(args: argparse.Namespace) -> int:
    """Handle 'agent-eval report' subcommand. Returns exit code."""
    results_dir = Path(args.results)
    if not results_dir.is_dir():
        print(f"error: results directory not found: {results_dir}", file=sys.stderr)
        return 2

    results = discover_results(results_dir)
    if not results:
        print(f"error: no results found in {results_dir}", file=sys.stderr)
        return 1

    output_path = (
        Path(args.output)
        if args.output
        else results_dir / f"report.{args.format}"
    )

    try:
        generate_report(results, output_path, format=args.format)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Report written to {output_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-eval",
        description="AI coding agent benchmark and comparison tool",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ── run ──────────────────────────────────────────────────────────────────
    run_p = sub.add_parser("run", help="Run one agent against one benchmark")
    run_p.add_argument("--benchmark", required=True, help="Path to benchmark directory")
    run_p.add_argument(
        "--agent", required=True, help="Agent name (e.g. claude, claude:opus, mock)"
    )
    run_p.add_argument("--output", required=True, help="Output directory for results")

    # ── compare ──────────────────────────────────────────────────────────────
    cmp_p = sub.add_parser("compare", help="Compare multiple agents on one benchmark")
    cmp_p.add_argument("--benchmark", required=True, help="Path to benchmark directory")
    cmp_p.add_argument("--agents", required=True, help="Comma-separated agent names")
    cmp_p.add_argument("--output", required=True, help="Output directory for results")

    # ── suite ─────────────────────────────────────────────────────────────────
    suite_p = sub.add_parser("suite", help="Run full suite from config file")
    suite_p.add_argument("--config", required=True, help="Path to eval-config.yaml")
    suite_p.add_argument(
        "--output", default=None, help="Override output directory from config"
    )

    # ── report ────────────────────────────────────────────────────────────────
    rpt_p = sub.add_parser("report", help="Generate a report from results")
    rpt_p.add_argument("--results", required=True, help="Path to results directory")
    rpt_p.add_argument(
        "--format",
        choices=["json", "markdown", "html"],
        default="json",
        help="Report format (default: json)",
    )
    rpt_p.add_argument(
        "--output", default=None, help="Output file path (auto-detected if omitted)"
    )

    return parser


_HANDLERS = {
    "run": _cmd_run,
    "compare": _cmd_compare,
    "suite": _cmd_suite,
    "report": _cmd_report,
}


def main(argv: list[str] | None = None) -> None:
    """Entry point for the agent-eval CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    code = _HANDLERS[args.command](args)
    sys.exit(code)
