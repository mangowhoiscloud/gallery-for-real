"""Comparison analyzer: compare multiple projects side-by-side."""
from __future__ import annotations

from decimal import Decimal

from agent_cost_analyzer.models import (
    AnalysisResult,
    ComparisonResult,
    EfficiencyEntry,
    ProjectSummaryRow,
)


def compare_projects(
    results: list[tuple[str, AnalysisResult]],
) -> ComparisonResult:
    """Compare two or more project analysis results.

    Args:
        results: List of (project_name, analysis_result) pairs. Must contain ≥2 items.

    Returns:
        ComparisonResult with summary_table, efficiency_ranking, stack_comparison,
        and cost_comparison.

    Raises:
        ValueError: If fewer than 2 projects are provided.
    """
    if len(results) < 2:
        raise ValueError(
            f"compare_projects requires at least 2 projects, got {len(results)}"
        )

    summary_table = _build_summary_table(results)
    efficiency_ranking = _build_efficiency_ranking(summary_table)
    stack_comparison = _build_stack_comparison(results, summary_table)
    cost_comparison = _build_cost_comparison(results)

    return ComparisonResult(
        summary_table=summary_table,
        efficiency_ranking=efficiency_ranking,
        stack_comparison=stack_comparison,
        cost_comparison=cost_comparison,
    )


def _duration_minutes(result: AnalysisResult) -> float:
    """Compute project duration in minutes from the cost timeline."""
    timeline = result.timeline or result.cost_breakdown.timeline
    if len(timeline) < 2:
        return 0.0
    first_ts = timeline[0][0]
    last_ts = timeline[-1][0]
    delta = last_ts - first_ts
    return delta.total_seconds() / 60.0


def _model_split(result: AnalysisResult) -> dict[str, float]:
    """Compute each model's share of total cost as a percentage (0–100)."""
    by_model = result.cost_breakdown.by_model
    total = result.cost_breakdown.total_cost
    if not by_model or total == Decimal("0"):
        return {}
    return {
        model: float(cost / total * 100)
        for model, cost in by_model.items()
    }


def _build_summary_table(
    results: list[tuple[str, AnalysisResult]],
) -> list[ProjectSummaryRow]:
    rows = []
    for project_name, result in results:
        rows.append(
            ProjectSummaryRow(
                project_name=project_name,
                total_cost=result.cost_breakdown.total_cost,
                total_iterations=result.cost_breakdown.total_iterations,
                duration_minutes=_duration_minutes(result),
                model_split=_model_split(result),
                stuck_count=len(result.failure_patterns.stuck_events),
            )
        )
    return rows


def _build_efficiency_ranking(
    summary_table: list[ProjectSummaryRow],
) -> list[EfficiencyEntry]:
    """Rank projects by cost-per-iteration (ascending — cheaper is better)."""
    entries = []
    for row in summary_table:
        if row.total_iterations > 0:
            cpi = row.total_cost / Decimal(row.total_iterations)
        else:
            cpi = row.total_cost  # treat 0 iterations as full cost
        entries.append(
            EfficiencyEntry(
                project_name=row.project_name,
                cost_per_iteration=cpi,
            )
        )
    entries.sort(key=lambda e: e.cost_per_iteration)
    return entries


def _build_stack_comparison(
    results: list[tuple[str, AnalysisResult]],
    summary_table: list[ProjectSummaryRow],
) -> dict[str, dict]:
    """Group projects by project_type and compute per-group averages."""
    groups: dict[str, list[ProjectSummaryRow]] = {}
    for (_, result), row in zip(results, summary_table):
        stack = result.project.project_type or "unknown"
        groups.setdefault(stack, []).append(row)

    comparison: dict[str, dict] = {}
    for stack, rows in groups.items():
        n = len(rows)
        avg_cost = sum((r.total_cost for r in rows), Decimal("0")) / Decimal(n)
        avg_iterations = sum(r.total_iterations for r in rows) / n
        avg_duration = sum(r.duration_minutes for r in rows) / n
        avg_stuck = sum(r.stuck_count for r in rows) / n
        comparison[stack] = {
            "project_count": n,
            "project_names": [r.project_name for r in rows],
            "avg_total_cost": avg_cost,
            "avg_iterations": avg_iterations,
            "avg_duration_minutes": avg_duration,
            "avg_stuck_count": avg_stuck,
        }
    return comparison


def _build_cost_comparison(
    results: list[tuple[str, AnalysisResult]],
) -> list[dict]:
    """Side-by-side cost breakdown per project."""
    comparison = []
    for project_name, result in results:
        cb = result.cost_breakdown
        comparison.append(
            {
                "project_name": project_name,
                "total_cost": cb.total_cost,
                "by_phase": dict(cb.by_phase),
                "by_model": dict(cb.by_model),
            }
        )
    return comparison
