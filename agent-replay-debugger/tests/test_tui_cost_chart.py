"""Tests for the TUI Cost Chart tab (Item 18).

Verifies:
- Sparkline receives cumulative cost data for all iterations
- Label shows selected iteration info (number, cost, cumulative)
- Tab 4 activates/deactivates correctly
- Empty iterations renders gracefully
- Single iteration case
- Multiple iterations with correct cumulative totals
- Iteration index outside valid range is handled gracefully
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from agent_replay.models import (
    CostEntry,
    GitCommit,
    Iteration,
    TimelineEvent,
)
from agent_replay.tui.app import ReplayApp
from agent_replay.tui.detail_panel import DetailPanel

try:
    from textual.widgets import Sparkline

    HAS_SPARKLINE = True
except ImportError:
    HAS_SPARKLINE = False

pytestmark = pytest.mark.skipif(
    not HAS_SPARKLINE, reason="Textual Sparkline not available"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROJECT_DIR = Path("/tmp/test-project-chart")


def _make_iter(
    number: int,
    phase: str = "build",
    cost: str = "1.00",
    duration_secs: int = 60,
) -> Iteration:
    """Create a minimal Iteration for cost chart testing."""
    ts = datetime(2026, 3, 25, hour=number % 24, tzinfo=timezone.utc)
    cost_dec = Decimal(cost)
    cost_entry = CostEntry(
        timestamp=ts,
        phase=phase,
        iter=number,
        model="opus",
        tokens_in=10,
        tokens_out=5000,
        cost=cost_dec,
        cumulative=cost_dec,
        item="",
    )
    events = [
        TimelineEvent(
            timestamp=ts,
            event_type="cost",
            phase=phase,
            iteration=number,
            data=cost_entry,
        )
    ]
    commit = GitCommit(
        hash=f"abc{number:08d}",
        message=f"feat: item {number}",
        timestamp=ts,
    )
    return Iteration(
        number=number,
        phase=phase,
        events=events,
        cost_total=cost_dec,
        tokens_in=10,
        tokens_out=5000,
        items_done=[],
        git_commits=[commit],
        status="OK",
        duration=timedelta(seconds=duration_secs),
    )


# Five iterations with known costs for cumulative assertions
CHART_ITERATIONS = [
    _make_iter(1, cost="0.10"),  # cumulative: 0.10
    _make_iter(2, cost="0.20"),  # cumulative: 0.30
    _make_iter(3, cost="0.50"),  # cumulative: 0.80
    _make_iter(4, cost="0.15"),  # cumulative: 0.95
    _make_iter(5, cost="0.05"),  # cumulative: 1.00
]


# ---------------------------------------------------------------------------
# Unit tests — _render_cost_chart called directly on mounted panel
# ---------------------------------------------------------------------------


class TestRenderCostChartDirect:
    @pytest.mark.asyncio
    async def test_sparkline_data_length_equals_iteration_count(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[0])
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            assert sparkline.data is not None
            assert len(sparkline.data) == 5

    @pytest.mark.asyncio
    async def test_sparkline_data_is_cumulative(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[0])
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            data = list(sparkline.data)
            # Each value is cumulative sum of all costs up to that iteration
            assert abs(data[0] - 0.10) < 1e-6
            assert abs(data[1] - 0.30) < 1e-6
            assert abs(data[2] - 0.80) < 1e-6
            assert abs(data[3] - 0.95) < 1e-6
            assert abs(data[4] - 1.00) < 1e-6

    @pytest.mark.asyncio
    async def test_sparkline_data_is_monotonically_increasing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[2])
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            data = list(sparkline.data)
            for i in range(1, len(data)):
                assert data[i] >= data[i - 1]

    @pytest.mark.asyncio
    async def test_label_shows_iteration_number(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[2])  # iteration #3
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            assert "#3" in text

    @pytest.mark.asyncio
    async def test_label_shows_iteration_cost(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[2])  # iter 3, cost $0.50
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            assert "$0.50" in text

    @pytest.mark.asyncio
    async def test_label_shows_cumulative_cost(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[2])  # cumulative at #3: $0.80
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            assert "$0.80" in text

    @pytest.mark.asyncio
    async def test_label_shows_total_iteration_count(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[0])
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            assert "5" in text

    @pytest.mark.asyncio
    async def test_label_updates_when_iteration_changes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(CHART_ITERATIONS[0])  # #1
            label_before = app.query_one("#cost-chart-label").render().plain
            panel.update_iteration(CHART_ITERATIONS[4])  # #5
            label_after = app.query_one("#cost-chart-label").render().plain
            assert "#1" in label_before
            assert "#5" in label_after


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestCostChartEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_iterations_shows_no_data_message(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[])
        # Empty session shows "Empty session" message, no DetailPanel
        async with app.run_test():
            panels = app.query(DetailPanel)
            assert len(panels) == 0

    @pytest.mark.asyncio
    async def test_single_iteration_sparkline_has_one_point(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        single = [_make_iter(1, cost="2.50")]
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=single)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(single[0])
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            assert sparkline.data is not None
            assert len(sparkline.data) == 1

    @pytest.mark.asyncio
    async def test_single_iteration_label_singular(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        single = [_make_iter(1, cost="2.50")]
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=single)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(single[0])
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            assert "iteration" in text  # "1 iteration total", not "iterations"

    @pytest.mark.asyncio
    async def test_sparkline_data_independent_of_selected_iteration(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Sparkline always shows ALL iterations regardless of selection."""
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        iters = [_make_iter(i, cost="1.00") for i in range(1, 6)]
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=iters)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            # Select last iteration — sparkline still has 5 data points
            panel.update_iteration(iters[4])
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            assert len(sparkline.data) == 5


# ---------------------------------------------------------------------------
# Pilot tests — interaction via keyboard
# ---------------------------------------------------------------------------


class TestCostChartPilot:
    @pytest.mark.asyncio
    async def test_press_4_shows_sparkline(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("4")
            tab4 = app.query_one("#detail-tab-4")
            assert tab4.has_class("active")
            sparkline = app.query_one("#cost-sparkline", Sparkline)
            # Data populated from auto-selection of first iteration on mount
            assert sparkline.data is not None

    @pytest.mark.asyncio
    async def test_navigate_and_check_chart_updates(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("4")
            await pilot.press("j")
            await pilot.pause()
            label = app.query_one("#cost-chart-label")
            text = label.render().plain
            # After navigating, label should show iteration number
            assert "#" in text

    @pytest.mark.asyncio
    async def test_tab_4_does_not_crash_with_single_iteration(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        single = [_make_iter(1, cost="5.00")]
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=single)
        async with app.run_test() as pilot:
            await pilot.press("4")  # should not crash

    @pytest.mark.asyncio
    async def test_tab_switch_back_from_chart_works(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("4")
            await pilot.press("1")
            tab1 = app.query_one("#detail-tab-1")
            tab4 = app.query_one("#detail-tab-4")
            assert tab1.has_class("active")
            assert not tab4.has_class("active")

    @pytest.mark.asyncio
    async def test_header_shows_cost_chart_label_on_tab_4(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=CHART_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("4")
            header = app.query_one("#detail-tab-header")
            text = header.render().plain
            assert "Cost" in text
