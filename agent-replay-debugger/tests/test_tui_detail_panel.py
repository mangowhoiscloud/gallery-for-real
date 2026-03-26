"""Tests for the TUI detail panel with tabs (Item 17).

Uses Textual's pilot testing framework to verify:
- Initial state shows "Select an iteration"
- Tab switching with show_tab() changes active tab
- Overview tab content (phase, model, tokens, cost, duration, items, metrics)
- Progress tab content (session blocks)
- Git tab content (commits with git show --stat, monkeypatched)
- Cost chart tab placeholder
- Integration with ReplayApp: selection + tab keys
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
    MetricsEntry,
    SessionBlock,
    TimelineEvent,
)
from agent_replay.tui.app import ReplayApp
from agent_replay.tui.detail_panel import DetailPanel, _format_duration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 3, 25, hour=1, tzinfo=timezone.utc)
_PROJECT_DIR = Path("/tmp/test-project")


def _make_iteration(
    number: int = 1,
    phase: str = "build",
    cost: str = "0.50",
    tokens_in: int = 20,
    tokens_out: int = 8000,
    status: str = "OK",
    duration_secs: int = 60,
    model: str = "opus",
    items_done: list[str] | None = None,
    session_content: str | None = None,
    commit_messages: list[str] | None = None,
    metrics: list[tuple[str, str, str, str]] | None = None,
    commits: int | None = None,
) -> Iteration:
    """Create an Iteration with rich event data for detail panel testing."""
    ts = datetime(2026, 3, 25, hour=number % 24, tzinfo=timezone.utc)
    events: list[TimelineEvent] = []

    # Cost event (carries model info)
    cost_entry = CostEntry(
        timestamp=ts,
        phase=phase,
        iter=1,
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost=Decimal(cost),
        cumulative=Decimal(cost),
        item="",
    )
    events.append(
        TimelineEvent(
            timestamp=ts, event_type="cost", phase=phase, iteration=number,
            data=cost_entry,
        )
    )

    # Session block event (for progress tab)
    if session_content is not None:
        block = SessionBlock(
            timestamp=ts,
            content=session_content,
            items_completed=items_done or [],
        )
        events.append(
            TimelineEvent(
                timestamp=ts, event_type="session", phase=phase,
                iteration=number, data=block,
            )
        )

    # Metrics events
    if metrics:
        for metric, context, value, detail in metrics:
            me = MetricsEntry(
                timestamp=ts, metric=metric, context=context,
                value=value, detail=detail,
            )
            events.append(
                TimelineEvent(
                    timestamp=ts, event_type="metrics", phase=phase,
                    iteration=number, data=me,
                )
            )

    # Git commits
    git_commits: list[GitCommit] = []
    if commit_messages:
        for i, msg in enumerate(commit_messages):
            git_commits.append(
                GitCommit(
                    hash=f"abc{number:04d}{i:02d}",
                    message=msg,
                    timestamp=ts,
                )
            )
    elif commits is not None:
        for i in range(commits):
            git_commits.append(
                GitCommit(
                    hash=f"abc{number:04d}{i:02d}",
                    message=f"feat: item {number}",
                    timestamp=ts,
                )
            )
    else:
        git_commits.append(
            GitCommit(
                hash=f"abc{number:04d}00",
                message=f"feat: item {number}",
                timestamp=ts,
            )
        )

    return Iteration(
        number=number,
        phase=phase,
        events=events,
        cost_total=Decimal(cost),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        items_done=items_done or [],
        git_commits=git_commits,
        status=status,
        duration=timedelta(seconds=duration_secs),
    )


SAMPLE_ITERATIONS = [
    _make_iteration(1, phase="socratic", cost="0.25", duration_secs=30),
    _make_iteration(2, phase="plan", cost="0.50", duration_secs=120,
                    session_content="Completed: Item 2 - Plan",
                    items_done=["Item 2 - Plan"]),
    _make_iteration(3, phase="build", cost="1.75", duration_secs=300,
                    status="FAIL", commits=0,
                    metrics=[("test_pass_rate", "build", "85", "tests")]),
    _make_iteration(4, phase="build", cost="0.80", duration_secs=180,
                    commit_messages=["feat: models", "test: models"]),
    _make_iteration(5, phase="build", cost="0.60", duration_secs=90,
                    status="STUCK", commits=0),
]


# ---------------------------------------------------------------------------
# Unit tests for _format_duration (same function, local copy)
# ---------------------------------------------------------------------------


class TestFormatDuration:
    def test_zero(self) -> None:
        assert _format_duration(timedelta()) == "0s"

    def test_seconds(self) -> None:
        assert _format_duration(timedelta(seconds=45)) == "45s"

    def test_minutes_seconds(self) -> None:
        assert _format_duration(timedelta(minutes=2, seconds=30)) == "2m 30s"


# ---------------------------------------------------------------------------
# Unit tests — DetailPanel methods (non-pilot)
# ---------------------------------------------------------------------------


class TestDetailPanelInit:
    def test_stores_project_dir(self) -> None:
        panel = DetailPanel(_PROJECT_DIR, [])
        assert panel._project_dir == _PROJECT_DIR

    def test_stores_iterations(self) -> None:
        panel = DetailPanel(_PROJECT_DIR, SAMPLE_ITERATIONS)
        assert panel._iterations is SAMPLE_ITERATIONS

    def test_initial_active_tab(self) -> None:
        panel = DetailPanel(_PROJECT_DIR, [])
        assert panel._active_tab == 1

    def test_initial_iteration_none(self) -> None:
        panel = DetailPanel(_PROJECT_DIR, [])
        assert panel._iteration is None


# ---------------------------------------------------------------------------
# Pilot tests — initial state
# ---------------------------------------------------------------------------


class TestInitialState:
    @pytest.mark.asyncio
    async def test_auto_selects_first_iteration_on_mount(self) -> None:
        """ListView auto-highlights item 0, so the detail panel shows it."""
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            # First iteration is socratic phase
            assert "socratic" in text

    @pytest.mark.asyncio
    async def test_header_shows_overview(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            header = app.query_one("#detail-tab-header")
            text = header.render().plain
            assert "Overview" in text

    @pytest.mark.asyncio
    async def test_tab_1_has_active_class(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            tab1 = app.query_one("#detail-tab-1")
            assert tab1.has_class("active")

    @pytest.mark.asyncio
    async def test_other_tabs_not_active(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            for i in (2, 3, 4):
                tab = app.query_one(f"#detail-tab-{i}")
                assert not tab.has_class("active")


# ---------------------------------------------------------------------------
# Pilot tests — tab switching via keys
# ---------------------------------------------------------------------------


class TestTabSwitching:
    @pytest.mark.asyncio
    async def test_press_2_activates_progress_tab(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("2")
            tab2 = app.query_one("#detail-tab-2")
            assert tab2.has_class("active")
            tab1 = app.query_one("#detail-tab-1")
            assert not tab1.has_class("active")

    @pytest.mark.asyncio
    async def test_press_3_activates_git_tab(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("3")
            tab3 = app.query_one("#detail-tab-3")
            assert tab3.has_class("active")

    @pytest.mark.asyncio
    async def test_press_4_activates_cost_tab(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("4")
            tab4 = app.query_one("#detail-tab-4")
            assert tab4.has_class("active")

    @pytest.mark.asyncio
    async def test_press_1_returns_to_overview(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("3")
            await pilot.press("1")
            tab1 = app.query_one("#detail-tab-1")
            assert tab1.has_class("active")
            tab3 = app.query_one("#detail-tab-3")
            assert not tab3.has_class("active")

    @pytest.mark.asyncio
    async def test_header_updates_on_tab_switch(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("2")
            header = app.query_one("#detail-tab-header")
            text = header.render().plain
            assert "Progress" in text

    @pytest.mark.asyncio
    async def test_only_one_tab_active_at_a_time(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            for key in ("1", "2", "3", "4"):
                await pilot.press(key)
                active_count = sum(
                    1 for i in range(1, 5)
                    if app.query_one(f"#detail-tab-{i}").has_class("active")
                )
                assert active_count == 1


# ---------------------------------------------------------------------------
# Pilot tests — overview tab content after iteration selection
# ---------------------------------------------------------------------------


class TestOverviewTab:
    @pytest.mark.asyncio
    async def test_overview_shows_phase(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, phase="build")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "build" in text

    @pytest.mark.asyncio
    async def test_overview_shows_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, status="FAIL")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "FAIL" in text

    @pytest.mark.asyncio
    async def test_overview_shows_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, model="opus")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "opus" in text

    @pytest.mark.asyncio
    async def test_overview_shows_tokens(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, tokens_in=20, tokens_out=8000)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "20" in text
            assert "8,000" in text

    @pytest.mark.asyncio
    async def test_overview_shows_cost(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, cost="1.75")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "$1.75" in text

    @pytest.mark.asyncio
    async def test_overview_shows_duration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, duration_secs=300)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "5m" in text

    @pytest.mark.asyncio
    async def test_overview_shows_items_done(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, items_done=["Item 3 - Models"])
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "Items completed" in text
            assert "Item 3 - Models" in text

    @pytest.mark.asyncio
    async def test_overview_shows_metrics(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(
            1, metrics=[("test_pass_rate", "build", "95", "percent")]
        )
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "Metrics" in text
            assert "test_pass_rate" in text
            assert "95" in text

    @pytest.mark.asyncio
    async def test_overview_no_items_section_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, items_done=[])
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "Items completed" not in text

    @pytest.mark.asyncio
    async def test_overview_no_metrics_section_when_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "Metrics" not in text


# ---------------------------------------------------------------------------
# Pilot tests — progress tab
# ---------------------------------------------------------------------------


class TestProgressTab:
    @pytest.mark.asyncio
    async def test_progress_shows_session_content(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(
            1, session_content="Completed: Item 5 - Timeline builder"
        )
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("2")
            tab2 = app.query_one("#detail-tab-2")
            text = tab2.render().plain
            assert "Timeline builder" in text

    @pytest.mark.asyncio
    async def test_progress_no_data_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1)  # no session_content
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("2")
            tab2 = app.query_one("#detail-tab-2")
            text = tab2.render().plain
            assert "No progress data" in text


# ---------------------------------------------------------------------------
# Pilot tests — git tab
# ---------------------------------------------------------------------------


class TestGitTab:
    @pytest.mark.asyncio
    async def test_git_tab_shows_commit_hash_and_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            DetailPanel, "_git_show_stat",
            lambda self, h: " file.py | 10 +++++"
        )
        it = _make_iteration(1, commit_messages=["feat: add models"])
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("3")
            tab3 = app.query_one("#detail-tab-3")
            text = tab3.render().plain
            assert "feat: add models" in text
            assert "abc0001" in text

    @pytest.mark.asyncio
    async def test_git_tab_shows_stat_output(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            DetailPanel, "_git_show_stat",
            lambda self, h: " src/main.py | 42 +++---"
        )
        it = _make_iteration(1, commit_messages=["fix: bug"])
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("3")
            tab3 = app.query_one("#detail-tab-3")
            text = tab3.render().plain
            assert "src/main.py" in text
            assert "42" in text

    @pytest.mark.asyncio
    async def test_git_tab_multiple_commits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            DetailPanel, "_git_show_stat", lambda self, h: "(stat)"
        )
        it = _make_iteration(
            1, commit_messages=["feat: first", "test: second"]
        )
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("3")
            tab3 = app.query_one("#detail-tab-3")
            text = tab3.render().plain
            assert "feat: first" in text
            assert "test: second" in text

    @pytest.mark.asyncio
    async def test_git_tab_no_commits(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            DetailPanel, "_git_show_stat", lambda self, h: "(mocked)"
        )
        it = _make_iteration(1, commits=0)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("3")
            tab3 = app.query_one("#detail-tab-3")
            text = tab3.render().plain
            assert "No git commits" in text


# ---------------------------------------------------------------------------
# Pilot tests — cost chart tab (real implementation, Item 18)
# ---------------------------------------------------------------------------


class TestCostChartTab:
    @pytest.mark.asyncio
    async def test_cost_chart_tab_activates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("4")
            tab4 = app.query_one("#detail-tab-4")
            assert tab4.has_class("active")


# ---------------------------------------------------------------------------
# Pilot tests — header updates with iteration info
# ---------------------------------------------------------------------------


class TestHeaderWithIteration:
    @pytest.mark.asyncio
    async def test_header_shows_iteration_number_after_selection(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            header = app.query_one("#detail-tab-header")
            text = header.render().plain
            assert "#1" in text

    @pytest.mark.asyncio
    async def test_header_includes_tab_name_and_iteration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(3)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("3")
            header = app.query_one("#detail-tab-header")
            text = header.render().plain
            assert "Git" in text
            assert "#3" in text


# ---------------------------------------------------------------------------
# Pilot tests — show_tab edge cases
# ---------------------------------------------------------------------------


class TestShowTabEdgeCases:
    @pytest.mark.asyncio
    async def test_show_tab_invalid_number_ignored(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.show_tab(0)  # out of range
            panel.show_tab(5)  # out of range
            # tab 1 should still be active
            assert app.query_one("#detail-tab-1").has_class("active")

    @pytest.mark.asyncio
    async def test_show_tab_same_tab_is_noop(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.show_tab(1)
            panel.show_tab(1)
            assert app.query_one("#detail-tab-1").has_class("active")


# ---------------------------------------------------------------------------
# Pilot tests — update_iteration changes all tabs
# ---------------------------------------------------------------------------


class TestUpdateIteration:
    @pytest.mark.asyncio
    async def test_update_iteration_changes_overview(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, phase="plan", cost="2.50")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(it)
            tab1 = app.query_one("#detail-tab-1")
            text = tab1.render().plain
            assert "plan" in text
            assert "$2.50" in text

    @pytest.mark.asyncio
    async def test_update_iteration_changes_progress(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1, session_content="Session progress text here")
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(it)
            tab2 = app.query_one("#detail-tab-2")
            text = tab2.render().plain
            assert "Session progress text here" in text

    @pytest.mark.asyncio
    async def test_update_iteration_changes_git(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            DetailPanel, "_git_show_stat", lambda self, h: "(stat output)"
        )
        it = _make_iteration(1, commit_messages=["refactor: cleanup"])
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(it)
            tab3 = app.query_one("#detail-tab-3")
            text = tab3.render().plain
            assert "refactor: cleanup" in text

    @pytest.mark.asyncio
    async def test_update_iteration_stores_reference(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(1)
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test():
            panel = app.query_one(DetailPanel)
            panel.update_iteration(it)
            assert panel._iteration is it


# ---------------------------------------------------------------------------
# Pilot tests — integration with app selection
# ---------------------------------------------------------------------------


class TestAppIntegration:
    @pytest.mark.asyncio
    async def test_selection_updates_detail_panel(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        iters = [
            _make_iteration(1, phase="socratic", cost="0.25"),
            _make_iteration(2, phase="plan", cost="0.50"),
        ]
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=iters)
        async with app.run_test() as pilot:
            # Navigate down to trigger selection
            await pilot.press("j")
            await pilot.pause()
            panel = app.query_one(DetailPanel)
            assert panel._iteration is not None

    @pytest.mark.asyncio
    async def test_navigation_then_tab_switch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(DetailPanel, "_git_show_stat", lambda self, h: "(mocked)")
        it = _make_iteration(
            1, session_content="Build log content"
        )
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[it])
        async with app.run_test() as pilot:
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("2")
            tab2 = app.query_one("#detail-tab-2")
            text = tab2.render().plain
            assert "Build log content" in text

    @pytest.mark.asyncio
    async def test_empty_session_no_detail_panel(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[])
        async with app.run_test():
            panels = app.query(DetailPanel)
            assert len(panels) == 0

    @pytest.mark.asyncio
    async def test_tab_keys_safe_on_empty_session(self) -> None:
        app = ReplayApp(project_dir=_PROJECT_DIR, iterations=[])
        async with app.run_test() as pilot:
            for key in ("1", "2", "3", "4"):
                await pilot.press(key)  # should not crash


# ---------------------------------------------------------------------------
# Unit test — _git_show_stat subprocess
# ---------------------------------------------------------------------------


class TestGitShowStat:
    def test_git_show_stat_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as sp

        def mock_run(*args: object, **kwargs: object) -> sp.CompletedProcess[str]:
            return sp.CompletedProcess(
                args=[], returncode=0, stdout=" file.py | 5 +++++\n"
            )

        monkeypatch.setattr("agent_replay.tui.detail_panel.subprocess.run", mock_run)
        panel = DetailPanel(_PROJECT_DIR, [])
        result = panel._git_show_stat("abc1234")
        assert "file.py" in result

    def test_git_show_stat_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as sp

        def mock_run(*args: object, **kwargs: object) -> sp.CompletedProcess[str]:
            return sp.CompletedProcess(args=[], returncode=128, stdout="")

        monkeypatch.setattr("agent_replay.tui.detail_panel.subprocess.run", mock_run)
        panel = DetailPanel(_PROJECT_DIR, [])
        result = panel._git_show_stat("abc1234")
        assert "no file changes" in result

    def test_git_show_stat_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def mock_run(*args: object, **kwargs: object) -> None:
            raise FileNotFoundError("git not found")

        monkeypatch.setattr("agent_replay.tui.detail_panel.subprocess.run", mock_run)
        panel = DetailPanel(_PROJECT_DIR, [])
        result = panel._git_show_stat("abc1234")
        assert "git not available" in result

    def test_git_show_stat_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import subprocess as sp

        def mock_run(*args: object, **kwargs: object) -> None:
            raise sp.TimeoutExpired(cmd="git", timeout=5)

        monkeypatch.setattr("agent_replay.tui.detail_panel.subprocess.run", mock_run)
        panel = DetailPanel(_PROJECT_DIR, [])
        result = panel._git_show_stat("abc1234")
        assert "git not available" in result
