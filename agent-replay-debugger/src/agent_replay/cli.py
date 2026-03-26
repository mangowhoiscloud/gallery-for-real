"""CLI entrypoint for agent-replay.

Argparse setup, project-directory validation, timeline build, and dispatch.

Clarity resolutions applied:
- Round 14: empty session → "Empty session — no iteration data found"
- Round 15: --iteration N uses global number; exit 1 with message if not found
- Round 16: --failures includes both FAIL and STUCK iterations
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agent_replay.export import export_json
from agent_replay.parsers import parse_harness_state, parse_plan
from agent_replay.summary import print_summary
from agent_replay.timeline import build_timeline


def _validate_project_dir(project_dir_str: str) -> Path:
    """Resolve project-dir path; exit 1 if .harness-logs/ is absent."""
    path = Path(project_dir_str).resolve()
    if not (path / ".harness-logs").is_dir():
        print(f"Not a harness project: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def _handle_summary(iterations: list, project_dir: Path) -> None:
    """Load state and plan, then delegate to print_summary."""
    state = parse_harness_state(project_dir / ".harness-logs" / "harness-state.json")
    plan_items = parse_plan(project_dir / "IMPLEMENTATION_PLAN.md")
    print_summary(iterations, state, plan_items)


def _handle_iteration(
    iterations: list, n: int, *, console: Console | None = None
) -> None:
    """Display rich detail panel for global iteration N; exit 1 if not found (Round 15)."""
    if console is None:
        console = Console()
    it = next((x for x in iterations if x.number == n), None)
    if it is None:
        print(
            f"Iteration {n} not found (session has {len(iterations)} iterations)",
            file=sys.stderr,
        )
        sys.exit(1)
    lines = [
        f"Phase:    {it.phase}",
        f"Status:   {it.status}",
        f"Cost:     ${it.cost_total:.4f}",
        f"Tokens:   in={it.tokens_in:,}  out={it.tokens_out:,}",
        f"Duration: {it.duration}",
    ]
    for commit in it.git_commits:
        lines.append(f"Commit:   {commit.hash[:8]}  {commit.message}")
    for item in it.items_done:
        lines.append(f"Done:     {item}")
    console.print(Panel("\n".join(lines), title=f"Iteration {it.number}", expand=False))


def _handle_failures(
    iterations: list, *, console: Console | None = None
) -> None:
    """Print FAIL and STUCK iterations as a rich table (Round 16: both are failures)."""
    if console is None:
        console = Console()
    failures = [it for it in iterations if it.status in ("FAIL", "STUCK")]
    if not failures:
        console.print("No failures found in session")
        return
    table = Table(title=f"Failures ({len(failures)})")
    table.add_column("No.", justify="right")
    table.add_column("Phase")
    table.add_column("Status")
    table.add_column("Cost", justify="right")
    for it in failures:
        table.add_row(str(it.number), it.phase, it.status, f"${it.cost_total:.4f}")
    console.print(table)


def _handle_export(iterations: list, output_path: Path) -> None:
    """Serialize iterations to JSON via export_json and print confirmation."""
    export_json(iterations, output_path)
    print(f"Exported {len(iterations)} iterations to {output_path}")


def _launch_tui(project_dir: Path, iterations: list) -> None:
    """Launch the Textual TUI (implemented in Item 15)."""
    from agent_replay.tui.app import ReplayApp  # deferred until Item 15 exists

    ReplayApp(project_dir=project_dir, iterations=iterations).run()


def main() -> None:
    """Parse arguments, validate project directory, build timeline, dispatch."""
    parser = argparse.ArgumentParser(
        prog="agent-replay",
        description="TUI debugger for autonomous coding agent session replay",
    )
    parser.add_argument(
        "project_dir",
        metavar="project-dir",
        help="Path to harness project directory (must contain .harness-logs/)",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--summary",
        action="store_true",
        help="Print session summary and exit",
    )
    mode_group.add_argument(
        "--iteration",
        type=int,
        metavar="N",
        help="Show detail for global iteration N and exit",
    )
    mode_group.add_argument(
        "--failures",
        action="store_true",
        help="Show only FAIL and STUCK iterations and exit",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Export full session data to JSON file",
    )

    args = parser.parse_args()
    project_dir = _validate_project_dir(args.project_dir)
    iterations = build_timeline(project_dir)

    if args.summary:
        _handle_summary(iterations, project_dir)
    elif args.iteration is not None:
        _handle_iteration(iterations, args.iteration)
    elif args.failures:
        _handle_failures(iterations)
    elif args.export is None:
        _launch_tui(project_dir, iterations)

    if args.export:
        _handle_export(iterations, Path(args.export))
