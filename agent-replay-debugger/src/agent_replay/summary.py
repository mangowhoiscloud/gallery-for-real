"""Summary mode for agent-replay: rich-formatted session overview.

Clarity resolutions applied:
- Costs formatted as $X.XX (2 decimal places, per spec)
- Per-phase breakdown shown as a rich Table
- Plan progress shows DONE count vs TODO+IN_PROGRESS count
"""
from __future__ import annotations

from decimal import Decimal

from rich.console import Console
from rich.table import Table

from agent_replay.models import Iteration, PlanItem


def print_summary(
    iterations: list[Iteration],
    state: dict | None,
    plan_items: list[PlanItem],
    *,
    console: Console | None = None,
) -> None:
    """Print a rich-formatted session summary to stdout.

    Args:
        iterations: Ordered list of Iteration objects from build_timeline().
        state:      Parsed harness-state.json dict, or None if unavailable.
        plan_items: Parsed IMPLEMENTATION_PLAN.md items, or [] if unavailable.
        console:    Optional rich Console; defaults to Console(highlight=False).
                    Pass a Console backed by a StringIO in tests for precise capture.
    """
    if console is None:
        console = Console(highlight=False)

    if not iterations:
        console.print("Empty session — no iteration data found")
        return

    total_cost: Decimal = sum(
        (it.cost_total for it in iterations), Decimal("0")
    )
    total_in: int = sum(it.tokens_in for it in iterations)
    total_out: int = sum(it.tokens_out for it in iterations)
    ok: int = sum(1 for it in iterations if it.status == "OK")
    fail: int = sum(1 for it in iterations if it.status == "FAIL")
    stuck: int = sum(1 for it in iterations if it.status == "STUCK")

    console.print(f"Iterations:  {len(iterations)}")
    console.print(f"Total cost:  ${total_cost:.2f}")
    console.print(f"Tokens:      in={total_in:,}  out={total_out:,}")
    console.print(f"Status:      {ok} OK  {fail} FAIL  {stuck} STUCK")

    # Per-phase breakdown table
    phases: dict[str, dict] = {}
    for it in iterations:
        if it.phase not in phases:
            phases[it.phase] = {
                "count": 0,
                "cost": Decimal("0"),
                "tokens_in": 0,
                "tokens_out": 0,
            }
        phases[it.phase]["count"] += 1
        phases[it.phase]["cost"] += it.cost_total
        phases[it.phase]["tokens_in"] += it.tokens_in
        phases[it.phase]["tokens_out"] += it.tokens_out

    table = Table(title="Per-Phase Breakdown", highlight=False)
    table.add_column("Phase")
    table.add_column("Iterations", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Tokens In", justify="right")
    table.add_column("Tokens Out", justify="right")
    for phase_name, data in phases.items():
        table.add_row(
            phase_name,
            str(data["count"]),
            f"${data['cost']:.2f}",
            f"{data['tokens_in']:,}",
            f"{data['tokens_out']:,}",
        )
    console.print(table)

    # Current harness state
    if state:
        phase_label = state.get("phase", "unknown")
        console.print(f"Current phase: {phase_label}")

    # Plan progress
    if plan_items:
        done = sum(1 for p in plan_items if p.status == "DONE")
        todo = sum(
            1 for p in plan_items if p.status in ("TODO", "IN_PROGRESS")
        )
        console.print(f"Plan progress: {done} DONE / {todo} TODO")

    # Completed items (deduplicated, insertion-ordered)
    seen: set[str] = set()
    all_items: list[str] = []
    for it in iterations:
        for item in it.items_done:
            if item not in seen:
                seen.add(item)
                all_items.append(item)

    if all_items:
        console.print("Items completed:")
        for item in all_items:
            console.print(f"  {item}")
