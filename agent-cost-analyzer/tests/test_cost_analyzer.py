"""Tests for cost breakdown analyzer (Item 7)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from agent_cost_analyzer.analyzer.cost import analyze_costs
from agent_cost_analyzer.models import CostBreakdown, CostEntry
from agent_cost_analyzer.parser.cost_log import parse_cost_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_entry(
    phase: str,
    iteration: int,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cost: str,
    item: int | None = None,
    ts_offset_hours: int = 0,
) -> CostEntry:
    ts = datetime(2026, 3, 19, 10 + ts_offset_hours, 0, 0, tzinfo=timezone.utc)
    return CostEntry(
        timestamp=ts,
        phase=phase,
        iteration=iteration,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=Decimal(cost),
        cumulative=Decimal("0"),  # ignored by analyzer
        item=item,
    )


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------

def test_empty_input_returns_zero_breakdown() -> None:
    result = analyze_costs([])
    assert result.total_cost == Decimal("0")
    assert result.total_iterations == 0
    assert result.by_phase == {}
    assert result.by_model == {}
    assert result.by_item == {}
    assert result.timeline == []


# ---------------------------------------------------------------------------
# Single entry
# ---------------------------------------------------------------------------

def test_single_entry() -> None:
    entry = make_entry("build", 1, "sonnet", 1000, 500, "0.10", item=1)
    result = analyze_costs([entry])

    assert result.total_cost == Decimal("0.10")
    assert result.total_iterations == 1
    assert result.by_phase == {"build": Decimal("0.10")}
    assert result.by_model == {"sonnet": Decimal("0.10")}
    assert result.by_item == {1: Decimal("0.10")}
    assert len(result.timeline) == 1
    assert result.timeline[0][1] == Decimal("0.10")


# ---------------------------------------------------------------------------
# by_phase aggregation
# ---------------------------------------------------------------------------

def test_by_phase_aggregation() -> None:
    entries = [
        make_entry("socratic", 1, "sonnet", 100, 50, "0.10", ts_offset_hours=0),
        make_entry("plan", 1, "opus", 200, 100, "0.20", ts_offset_hours=1),
        make_entry("build", 1, "sonnet", 150, 75, "0.15", item=1, ts_offset_hours=2),
        make_entry("build", 2, "sonnet", 150, 75, "0.25", item=2, ts_offset_hours=3),
        make_entry("verify", 1, "sonnet", 300, 150, "0.30", ts_offset_hours=4),
    ]
    result = analyze_costs(entries)

    assert result.by_phase["socratic"] == Decimal("0.10")
    assert result.by_phase["plan"] == Decimal("0.20")
    assert result.by_phase["build"] == Decimal("0.40")
    assert result.by_phase["verify"] == Decimal("0.30")
    assert result.total_cost == Decimal("1.00")


# ---------------------------------------------------------------------------
# by_model aggregation
# ---------------------------------------------------------------------------

def test_by_model_aggregation() -> None:
    entries = [
        make_entry("socratic", 1, "sonnet", 100, 50, "0.10", ts_offset_hours=0),
        make_entry("plan", 1, "opus", 200, 100, "0.20", ts_offset_hours=1),
        make_entry("build", 1, "sonnet", 150, 75, "0.15", item=1, ts_offset_hours=2),
        make_entry("build", 2, "opus", 150, 75, "0.25", item=2, ts_offset_hours=3),
    ]
    result = analyze_costs(entries)

    assert result.by_model["sonnet"] == Decimal("0.25")
    assert result.by_model["opus"] == Decimal("0.45")


# ---------------------------------------------------------------------------
# by_item — build-phase entries only, item=None excluded
# ---------------------------------------------------------------------------

def test_by_item_excludes_none_items() -> None:
    entries = [
        make_entry("socratic", 1, "sonnet", 100, 50, "0.10", item=None, ts_offset_hours=0),
        make_entry("plan", 1, "opus", 200, 100, "0.20", item=None, ts_offset_hours=1),
        make_entry("build", 1, "sonnet", 150, 75, "0.15", item=1, ts_offset_hours=2),
        make_entry("verify", 1, "sonnet", 300, 150, "0.30", item=None, ts_offset_hours=3),
    ]
    result = analyze_costs(entries)

    assert result.by_item == {1: Decimal("0.15")}


def test_by_item_groups_same_item() -> None:
    entries = [
        make_entry("build", 5, "opus", 100, 50, "0.18", item=5, ts_offset_hours=0),
        make_entry("build", 6, "opus", 100, 50, "0.19", item=5, ts_offset_hours=1),
        make_entry("build", 7, "opus", 100, 50, "0.12", item=5, ts_offset_hours=2),
    ]
    result = analyze_costs(entries)

    assert result.by_item == {5: Decimal("0.49")}


def test_by_item_non_sequential_items_included() -> None:
    """Items that skip numbers (e.g., 1, 3, 7) are grouped by actual value — no gaps filled."""
    entries = [
        make_entry("build", 1, "sonnet", 100, 50, "0.10", item=1, ts_offset_hours=0),
        make_entry("build", 2, "sonnet", 100, 50, "0.20", item=3, ts_offset_hours=1),
        make_entry("build", 3, "sonnet", 100, 50, "0.30", item=7, ts_offset_hours=2),
    ]
    result = analyze_costs(entries)

    assert set(result.by_item.keys()) == {1, 3, 7}
    assert result.by_item[1] == Decimal("0.10")
    assert result.by_item[3] == Decimal("0.20")
    assert result.by_item[7] == Decimal("0.30")


# ---------------------------------------------------------------------------
# Timeline — recalculated cumulative (ignores log cumulative field)
# ---------------------------------------------------------------------------

def test_timeline_recalculates_cumulative() -> None:
    """Timeline must recalculate running total, not use log cumulative field."""
    # Simulate session reset: log cumulative resets mid-run
    entries = [
        make_entry("build", 1, "sonnet", 100, 50, "0.10", item=1, ts_offset_hours=0),
        make_entry("build", 2, "sonnet", 100, 50, "0.20", item=2, ts_offset_hours=1),
        make_entry("build", 3, "sonnet", 100, 50, "0.30", item=3, ts_offset_hours=2),
    ]
    # Manually set log cumulative to simulate a reset at entry 3
    entries[2].cumulative = Decimal("0.30")  # log shows only 0.30, not 0.60

    result = analyze_costs(entries)

    # timeline should show monotonically increasing recalculated values
    cumuls = [t[1] for t in result.timeline]
    assert cumuls == [Decimal("0.10"), Decimal("0.30"), Decimal("0.60")]
    # final cumulative == total_cost
    assert result.timeline[-1][1] == result.total_cost


def test_timeline_length_matches_entries() -> None:
    entries = [
        make_entry("build", i, "sonnet", 100, 50, "0.10", item=i, ts_offset_hours=i)
        for i in range(1, 6)
    ]
    result = analyze_costs(entries)
    assert len(result.timeline) == 5


def test_timeline_monotonically_increasing() -> None:
    entries = [
        make_entry("socratic", 1, "sonnet", 100, 50, "0.10", ts_offset_hours=0),
        make_entry("plan", 1, "opus", 200, 100, "0.20", ts_offset_hours=1),
        make_entry("build", 1, "sonnet", 150, 75, "0.15", item=1, ts_offset_hours=2),
    ]
    result = analyze_costs(entries)
    cumuls = [t[1] for t in result.timeline]
    for i in range(1, len(cumuls)):
        assert cumuls[i] > cumuls[i - 1]


# ---------------------------------------------------------------------------
# Type checks
# ---------------------------------------------------------------------------

def test_all_monetary_values_are_decimal() -> None:
    entries = [
        make_entry("socratic", 1, "sonnet", 100, 50, "0.10", ts_offset_hours=0),
        make_entry("build", 1, "sonnet", 150, 75, "0.15", item=1, ts_offset_hours=1),
    ]
    result = analyze_costs(entries)

    assert isinstance(result.total_cost, Decimal)
    for v in result.by_phase.values():
        assert isinstance(v, Decimal)
    for v in result.by_model.values():
        assert isinstance(v, Decimal)
    for v in result.by_item.values():
        assert isinstance(v, Decimal)
    for _, cumul in result.timeline:
        assert isinstance(cumul, Decimal)


def test_returns_costbreakdown_instance() -> None:
    result = analyze_costs([])
    assert isinstance(result, CostBreakdown)


# ---------------------------------------------------------------------------
# Integration with real fixture
# ---------------------------------------------------------------------------

def test_fixture_total_cost(cost_log_path) -> None:
    """Total cost from fixture must equal sum of individual costs = $3.0590."""
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    assert result.total_cost == Decimal("3.0590")
    assert result.total_iterations == 11


def test_fixture_by_phase(cost_log_path) -> None:
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    assert result.by_phase["socratic"] == Decimal("0.6257")
    assert result.by_phase["plan"] == Decimal("0.5914")
    assert result.by_phase["verify"] == Decimal("0.5186")
    # build = 0.1897 + 0.0769 + 0.3099 + 0.1550 + 0.1800 + 0.1900 + 0.1200 + 0.1018 = 1.3233
    assert result.by_phase["build"] == Decimal("1.3233")


def test_fixture_by_model(cost_log_path) -> None:
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    # sonnet: socratic(0.6257) + build1(0.1897) + build2(0.0769) + build4(0.1550) + verify(0.5186)
    assert result.by_model["claude-sonnet-4-5"] == Decimal("1.5659")
    # opus: plan(0.5914) + build3(0.3099) + build5(0.1800) + build6(0.1900) + build7(0.1200) + build8(0.1018)
    assert result.by_model["claude-opus-4-5"] == Decimal("1.4931")


def test_fixture_by_item(cost_log_path) -> None:
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    assert result.by_item[1] == Decimal("0.1897")
    assert result.by_item[2] == Decimal("0.0769")
    assert result.by_item[3] == Decimal("0.3099")
    assert result.by_item[4] == Decimal("0.1550")
    # item 5 appears 4 times: 0.1800 + 0.1900 + 0.1200 + 0.1018
    assert result.by_item[5] == Decimal("0.5918")
    # no other items
    assert set(result.by_item.keys()) == {1, 2, 3, 4, 5}


def test_fixture_timeline_recalculated(cost_log_path) -> None:
    """Recalculated cumulative differs from log cumulative at session reset (iter 6)."""
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    assert len(result.timeline) == 11
    # Final recalculated cumulative == total_cost
    assert result.timeline[-1][1] == Decimal("3.0590")

    # iter=6 (index 7) log cumulative = 0.1900 (session reset).
    # Recalculated must be > 2.1286 (the value after iter=5).
    iter6_cumul = result.timeline[7][1]  # 0-indexed: entry index 7 is build iter=6
    assert iter6_cumul > Decimal("2.1286")


def test_fixture_timeline_monotonically_increasing(cost_log_path) -> None:
    entries = parse_cost_log(cost_log_path)
    result = analyze_costs(entries)

    cumuls = [t[1] for t in result.timeline]
    for i in range(1, len(cumuls)):
        assert cumuls[i] > cumuls[i - 1], f"Not monotonic at index {i}: {cumuls[i-1]} → {cumuls[i]}"
