"""Cost breakdown analyzer for agent cost log entries."""
from __future__ import annotations

from decimal import Decimal

from agent_cost_analyzer.models import CostBreakdown, CostEntry


def analyze_costs(entries: list[CostEntry]) -> CostBreakdown:
    """Compute cost breakdown from a list of CostEntry objects.

    Cumulative values are recalculated by summing individual costs in
    chronological order — the cumulative field in the log is ignored because
    the harness resets it on session restart (Clarity #4).
    """
    by_phase: dict[str, Decimal] = {}
    by_model: dict[str, Decimal] = {}
    by_item: dict[int, Decimal] = {}
    timeline: list[tuple] = []
    running_total = Decimal("0")

    for entry in entries:
        # by_phase
        by_phase[entry.phase] = by_phase.get(entry.phase, Decimal("0")) + entry.cost

        # by_model
        by_model[entry.model] = by_model.get(entry.model, Decimal("0")) + entry.cost

        # by_item — build-phase entries only, where item is not None
        if entry.item is not None:
            by_item[entry.item] = by_item.get(entry.item, Decimal("0")) + entry.cost

        # recalculated cumulative (ignore log cumulative field)
        running_total += entry.cost
        timeline.append((entry.timestamp, running_total))

    return CostBreakdown(
        by_phase=by_phase,
        by_model=by_model,
        by_item=by_item,
        timeline=timeline,
        total_cost=running_total,
        total_iterations=len(entries),
    )
