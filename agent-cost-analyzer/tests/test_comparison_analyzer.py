"""Tests for comparison analyzer (Item 10)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from agent_cost_analyzer.analyzer.comparison import compare_projects
from agent_cost_analyzer.models import (
    AnalysisResult,
    CostBreakdown,
    FailurePatterns,
    ProgressData,
    StuckEvent,
    TokenAnalysis,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_UTC = timezone.utc


def _ts(hour: int) -> datetime:
    return datetime(2026, 3, 19, hour, 0, 0, tzinfo=_UTC)


def _make_result(
    project_type: str = "Python",
    total_cost: str = "1.0000",
    total_iterations: int = 10,
    by_phase: dict | None = None,
    by_model: dict | None = None,
    stuck_events: list | None = None,
    timeline_hours: tuple[int, int] | None = (10, 12),  # (start_hour, end_hour)
) -> AnalysisResult:
    """Build a minimal AnalysisResult for testing."""
    by_phase = by_phase or {"build": Decimal(total_cost)}
    by_model = by_model or {"sonnet": Decimal(total_cost)}
    stuck_events = stuck_events or []

    # Build timeline from two timestamps if provided
    timeline: list[tuple[datetime, Decimal]] = []
    if timeline_hours:
        start_h, end_h = timeline_hours
        cumul = Decimal(total_cost)
        timeline = [
            (_ts(start_h), Decimal("0.1000")),
            (_ts(end_h), cumul),
        ]

    cb = CostBreakdown(
        by_phase={k: Decimal(str(v)) for k, v in by_phase.items()},
        by_model={k: Decimal(str(v)) for k, v in by_model.items()},
        by_item={},
        timeline=timeline,
        total_cost=Decimal(total_cost),
        total_iterations=total_iterations,
    )
    fp = FailurePatterns(stuck_events=stuck_events)
    progress = ProgressData(project_type=project_type)

    return AnalysisResult(
        project=progress,
        cost_breakdown=cb,
        token_analysis=TokenAnalysis(),
        failure_patterns=fp,
        timeline=timeline,
    )


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------


def test_compare_requires_at_least_two_projects():
    result = _make_result()
    with pytest.raises(ValueError, match="at least 2"):
        compare_projects([("only_project", result)])


def test_compare_zero_projects_raises():
    with pytest.raises(ValueError, match="at least 2"):
        compare_projects([])


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------


def test_summary_table_has_one_row_per_project():
    r1 = _make_result(total_cost="1.0000", total_iterations=10)
    r2 = _make_result(total_cost="2.0000", total_iterations=20)
    result = compare_projects([("proj_a", r1), ("proj_b", r2)])
    assert len(result.summary_table) == 2


def test_summary_table_project_names():
    r1 = _make_result()
    r2 = _make_result()
    result = compare_projects([("alpha", r1), ("beta", r2)])
    names = [row.project_name for row in result.summary_table]
    assert names == ["alpha", "beta"]


def test_summary_table_total_cost():
    r1 = _make_result(total_cost="1.2345")
    r2 = _make_result(total_cost="3.9999")
    result = compare_projects([("a", r1), ("b", r2)])
    costs = {row.project_name: row.total_cost for row in result.summary_table}
    assert costs["a"] == Decimal("1.2345")
    assert costs["b"] == Decimal("3.9999")


def test_summary_table_total_iterations():
    r1 = _make_result(total_iterations=15)
    r2 = _make_result(total_iterations=25)
    result = compare_projects([("a", r1), ("b", r2)])
    iters = {row.project_name: row.total_iterations for row in result.summary_table}
    assert iters["a"] == 15
    assert iters["b"] == 25


def test_summary_table_duration_minutes():
    # timeline_hours=(10, 12) → 2 hours = 120 minutes
    r1 = _make_result(timeline_hours=(10, 12))
    r2 = _make_result(timeline_hours=(8, 9))  # 1 hour = 60 minutes
    result = compare_projects([("a", r1), ("b", r2)])
    durations = {row.project_name: row.duration_minutes for row in result.summary_table}
    assert durations["a"] == pytest.approx(120.0)
    assert durations["b"] == pytest.approx(60.0)


def test_summary_table_duration_zero_for_empty_timeline():
    r1 = _make_result(timeline_hours=None)
    r2 = _make_result(timeline_hours=None)
    result = compare_projects([("a", r1), ("b", r2)])
    assert result.summary_table[0].duration_minutes == 0.0


def test_summary_table_model_split_percentages():
    # 1 opus (0.4) + 1 sonnet (0.6) = total 1.0
    by_model = {"opus": Decimal("0.4000"), "sonnet": Decimal("0.6000")}
    r1 = _make_result(total_cost="1.0000", by_model=by_model)
    r2 = _make_result()
    result = compare_projects([("a", r1), ("b", r2)])
    split = result.summary_table[0].model_split
    assert split["opus"] == pytest.approx(40.0)
    assert split["sonnet"] == pytest.approx(60.0)


def test_summary_table_model_split_empty_when_no_model_data():
    r1 = _make_result(total_cost="0.0000", by_model={})
    r2 = _make_result()
    result = compare_projects([("a", r1), ("b", r2)])
    assert result.summary_table[0].model_split == {}


def test_summary_table_stuck_count():
    stuck = [StuckEvent(item=3, start_iteration=5, count=3)]
    r1 = _make_result(stuck_events=stuck)
    r2 = _make_result(stuck_events=[])
    result = compare_projects([("a", r1), ("b", r2)])
    counts = {row.project_name: row.stuck_count for row in result.summary_table}
    assert counts["a"] == 1
    assert counts["b"] == 0


# ---------------------------------------------------------------------------
# Efficiency ranking
# ---------------------------------------------------------------------------


def test_efficiency_ranking_sorted_ascending():
    # a: 2.0 / 10 = 0.2 per iter
    # b: 1.0 / 10 = 0.1 per iter → cheaper → ranked first
    r1 = _make_result(total_cost="2.0000", total_iterations=10)
    r2 = _make_result(total_cost="1.0000", total_iterations=10)
    result = compare_projects([("a", r1), ("b", r2)])
    assert result.efficiency_ranking[0].project_name == "b"
    assert result.efficiency_ranking[1].project_name == "a"


def test_efficiency_ranking_cost_per_iteration_values():
    r1 = _make_result(total_cost="3.0000", total_iterations=10)
    r2 = _make_result(total_cost="2.0000", total_iterations=4)
    result = compare_projects([("a", r1), ("b", r2)])
    # a: 0.3 per iter, b: 0.5 per iter → a ranked first
    cpi = {e.project_name: e.cost_per_iteration for e in result.efficiency_ranking}
    assert cpi["a"] == Decimal("0.3")
    assert cpi["b"] == Decimal("0.5")
    assert result.efficiency_ranking[0].project_name == "a"


def test_efficiency_ranking_zero_iterations_handled():
    r1 = _make_result(total_cost="1.0000", total_iterations=0)
    r2 = _make_result(total_cost="0.5000", total_iterations=5)
    result = compare_projects([("a", r1), ("b", r2)])
    # b: 0.1 per iter → ranked first; a falls back to full cost=1.0
    assert result.efficiency_ranking[0].project_name == "b"


# ---------------------------------------------------------------------------
# Stack comparison
# ---------------------------------------------------------------------------


def test_stack_comparison_groups_by_project_type():
    r1 = _make_result(project_type="Python")
    r2 = _make_result(project_type="Python")
    r3 = _make_result(project_type="TypeScript")
    result = compare_projects([("a", r1), ("b", r2), ("c", r3)])
    assert "Python" in result.stack_comparison
    assert "TypeScript" in result.stack_comparison


def test_stack_comparison_project_count():
    r1 = _make_result(project_type="Python")
    r2 = _make_result(project_type="Python")
    r3 = _make_result(project_type="Java")
    result = compare_projects([("a", r1), ("b", r2), ("c", r3)])
    assert result.stack_comparison["Python"]["project_count"] == 2
    assert result.stack_comparison["Java"]["project_count"] == 1


def test_stack_comparison_project_names_listed():
    r1 = _make_result(project_type="Python")
    r2 = _make_result(project_type="Python")
    result = compare_projects([("alpha", r1), ("beta", r2)])
    names = result.stack_comparison["Python"]["project_names"]
    assert set(names) == {"alpha", "beta"}


def test_stack_comparison_averages():
    # Two Python projects: costs 1.0 and 3.0 → avg 2.0
    r1 = _make_result(project_type="Python", total_cost="1.0000", total_iterations=10)
    r2 = _make_result(project_type="Python", total_cost="3.0000", total_iterations=30)
    result = compare_projects([("a", r1), ("b", r2)])
    grp = result.stack_comparison["Python"]
    assert grp["avg_total_cost"] == Decimal("2")
    assert grp["avg_iterations"] == 20.0


def test_stack_comparison_unknown_type_handled():
    r1 = _make_result(project_type="")
    r2 = _make_result(project_type="Python")
    result = compare_projects([("a", r1), ("b", r2)])
    assert "unknown" in result.stack_comparison


# ---------------------------------------------------------------------------
# Cost comparison
# ---------------------------------------------------------------------------


def test_cost_comparison_has_one_entry_per_project():
    r1 = _make_result()
    r2 = _make_result()
    result = compare_projects([("a", r1), ("b", r2)])
    assert len(result.cost_comparison) == 2


def test_cost_comparison_project_names():
    r1 = _make_result()
    r2 = _make_result()
    result = compare_projects([("x", r1), ("y", r2)])
    names = [entry["project_name"] for entry in result.cost_comparison]
    assert names == ["x", "y"]


def test_cost_comparison_total_cost_field():
    r1 = _make_result(total_cost="1.5000")
    r2 = _make_result(total_cost="2.5000")
    result = compare_projects([("a", r1), ("b", r2)])
    totals = {e["project_name"]: e["total_cost"] for e in result.cost_comparison}
    assert totals["a"] == Decimal("1.5000")
    assert totals["b"] == Decimal("2.5000")


def test_cost_comparison_by_phase_field():
    by_phase = {"build": Decimal("0.8000"), "verify": Decimal("0.2000")}
    r1 = _make_result(by_phase=by_phase, total_cost="1.0000")
    r2 = _make_result()
    result = compare_projects([("a", r1), ("b", r2)])
    phase_data = result.cost_comparison[0]["by_phase"]
    assert phase_data["build"] == Decimal("0.8000")
    assert phase_data["verify"] == Decimal("0.2000")


def test_cost_comparison_by_model_field():
    by_model = {"opus": Decimal("0.9000"), "haiku": Decimal("0.1000")}
    r1 = _make_result(by_model=by_model, total_cost="1.0000")
    r2 = _make_result()
    result = compare_projects([("a", r1), ("b", r2)])
    model_data = result.cost_comparison[0]["by_model"]
    assert model_data["opus"] == Decimal("0.9000")
    assert model_data["haiku"] == Decimal("0.1000")


# ---------------------------------------------------------------------------
# Three-project comparison
# ---------------------------------------------------------------------------


def test_three_projects_summary_table_length():
    r1 = _make_result(total_cost="1.0000")
    r2 = _make_result(total_cost="2.0000")
    r3 = _make_result(total_cost="3.0000")
    result = compare_projects([("a", r1), ("b", r2), ("c", r3)])
    assert len(result.summary_table) == 3
    assert len(result.efficiency_ranking) == 3
    assert len(result.cost_comparison) == 3


def test_three_projects_efficiency_order():
    # a: 0.1/iter, b: 0.3/iter, c: 0.2/iter → order: a, c, b
    r1 = _make_result(total_cost="1.0000", total_iterations=10)  # 0.1
    r2 = _make_result(total_cost="3.0000", total_iterations=10)  # 0.3
    r3 = _make_result(total_cost="2.0000", total_iterations=10)  # 0.2
    result = compare_projects([("a", r1), ("b", r2), ("c", r3)])
    order = [e.project_name for e in result.efficiency_ranking]
    assert order == ["a", "c", "b"]
