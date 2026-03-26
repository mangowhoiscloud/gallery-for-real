"""Tests for the TUI app shell (Item 15).

Uses Textual's pilot testing framework to verify:
- App launches and mounts correctly
- Header shows project name and session stats
- Footer shows keybinding labels
- Layout has left-panel and right-panel (non-empty session)
- Empty session shows "Empty session" message
- q keybinding quits the app
- Keybinding actions exist and don't raise
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from agent_replay.models import GitCommit, Iteration, TimelineEvent
from agent_replay.tui.app import ReplayApp, _format_duration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_iteration(
    number: int,
    phase: str = "build",
    cost: str = "0.50",
    tokens_in: int = 20,
    tokens_out: int = 8000,
    status: str = "OK",
    duration_secs: int = 60,
    commits: int = 1,
) -> Iteration:
    """Create a minimal Iteration for testing."""
    ts = datetime(2026, 3, 25, hour=number, tzinfo=timezone.utc)
    git_commits = [
        GitCommit(
            hash=f"abc{number:04d}",
            message=f"feat: item {number}",
            timestamp=ts,
        )
        for _ in range(commits)
    ]
    return Iteration(
        number=number,
        phase=phase,
        events=[
            TimelineEvent(
                timestamp=ts,
                event_type="cost",
                phase=phase,
                iteration=number,
                data=None,  # type: ignore[arg-type]
            ),
        ],
        cost_total=Decimal(cost),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        items_done=[],
        git_commits=git_commits,
        status=status,
        duration=timedelta(seconds=duration_secs),
    )


SAMPLE_ITERATIONS = [
    _make_iteration(1, phase="socratic", cost="0.25", duration_secs=30),
    _make_iteration(2, phase="plan", cost="0.50", duration_secs=120),
    _make_iteration(3, phase="build", cost="1.75", duration_secs=300, status="FAIL", commits=0),
    _make_iteration(4, phase="build", cost="0.80", duration_secs=180),
    _make_iteration(5, phase="build", cost="0.60", duration_secs=90, status="STUCK", commits=0),
]

SAMPLE_PROJECT_DIR = Path("/tmp/test-project")


# ---------------------------------------------------------------------------
# Unit tests for _format_duration
# ---------------------------------------------------------------------------


class TestFormatDuration:
    def test_zero(self) -> None:
        assert _format_duration(timedelta()) == "0s"

    def test_seconds_only(self) -> None:
        assert _format_duration(timedelta(seconds=45)) == "45s"

    def test_minutes_and_seconds(self) -> None:
        assert _format_duration(timedelta(minutes=3, seconds=15)) == "3m 15s"

    def test_hours_minutes_seconds(self) -> None:
        assert _format_duration(timedelta(hours=2, minutes=10, seconds=5)) == "2h 10m 5s"

    def test_hours_only(self) -> None:
        assert _format_duration(timedelta(hours=1)) == "1h"

    def test_hours_and_minutes(self) -> None:
        assert _format_duration(timedelta(hours=1, minutes=30)) == "1h 30m"

    def test_negative_treated_as_zero(self) -> None:
        assert _format_duration(timedelta(seconds=-5)) == "0s"

    def test_large_value(self) -> None:
        result = _format_duration(timedelta(hours=100, minutes=59, seconds=59))
        assert result == "100h 59m 59s"


# ---------------------------------------------------------------------------
# Pilot tests — app lifecycle
# ---------------------------------------------------------------------------


class TestAppLaunch:
    """Verify the app launches, mounts, and displays correctly."""

    @pytest.mark.asyncio
    async def test_app_starts_and_stops(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            assert app.is_running
            await pilot.press("q")

    @pytest.mark.asyncio
    async def test_title_is_project_name(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            assert app.title == "test-project"

    @pytest.mark.asyncio
    async def test_subtitle_shows_stats(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            assert "5 iterations" in app.sub_title
            assert "$3.90" in app.sub_title
            assert "12m" in app.sub_title

    @pytest.mark.asyncio
    async def test_header_widget_exists(self) -> None:
        from textual.widgets import Header

        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            headers = app.query(Header)
            assert len(headers) == 1

    @pytest.mark.asyncio
    async def test_footer_widget_exists(self) -> None:
        from textual.widgets import Footer

        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            footers = app.query(Footer)
            assert len(footers) == 1


# ---------------------------------------------------------------------------
# Pilot tests — layout panels
# ---------------------------------------------------------------------------


class TestLayout:
    """Verify the left/right panel layout for non-empty sessions."""

    @pytest.mark.asyncio
    async def test_left_panel_exists(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            left = app.query_one("#left-panel")
            assert left is not None

    @pytest.mark.asyncio
    async def test_right_panel_exists(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            right = app.query_one("#right-panel")
            assert right is not None

    @pytest.mark.asyncio
    async def test_main_container_exists(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            container = app.query_one("#main-container")
            assert container is not None

    @pytest.mark.asyncio
    async def test_no_empty_message_when_iterations_present(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test():
            results = app.query("#empty-message")
            assert len(results) == 0


# ---------------------------------------------------------------------------
# Pilot tests — empty session
# ---------------------------------------------------------------------------


class TestEmptySession:
    """Verify empty session handling (Round 14)."""

    @pytest.mark.asyncio
    async def test_empty_message_shown(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        async with app.run_test():
            msg = app.query_one("#empty-message")
            assert "Empty session" in msg.render().plain

    @pytest.mark.asyncio
    async def test_no_panels_when_empty(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        async with app.run_test():
            assert len(app.query("#left-panel")) == 0
            assert len(app.query("#right-panel")) == 0

    @pytest.mark.asyncio
    async def test_subtitle_shows_zero_iterations(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        async with app.run_test():
            assert "0 iterations" in app.sub_title
            assert "$0.00" in app.sub_title

    @pytest.mark.asyncio
    async def test_quit_works_on_empty(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        async with app.run_test() as pilot:
            await pilot.press("q")


# ---------------------------------------------------------------------------
# Pilot tests — keybindings
# ---------------------------------------------------------------------------


class TestKeybindings:
    """Verify keybinding actions exist and don't raise."""

    @pytest.mark.asyncio
    async def test_quit_exits_app(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("q")

    @pytest.mark.asyncio
    async def test_j_does_not_crash(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("j")

    @pytest.mark.asyncio
    async def test_k_does_not_crash(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("k")

    @pytest.mark.asyncio
    async def test_number_keys_do_not_crash(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            for key in ("1", "2", "3", "4"):
                await pilot.press(key)

    @pytest.mark.asyncio
    async def test_slash_does_not_crash(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.press("slash")


# ---------------------------------------------------------------------------
# Pilot tests — constructor and properties
# ---------------------------------------------------------------------------


class TestAppProperties:
    """Verify constructor wiring and computed properties."""

    def test_project_dir_stored(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        assert app.project_dir == SAMPLE_PROJECT_DIR

    def test_iterations_stored(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        assert app.iterations is SAMPLE_ITERATIONS

    def test_total_cost(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        expected = Decimal("0.25") + Decimal("0.50") + Decimal("1.75") + Decimal("0.80") + Decimal("0.60")
        assert app._total_cost == expected

    def test_total_cost_empty(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        assert app._total_cost == Decimal("0")

    def test_total_duration(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=SAMPLE_ITERATIONS)
        expected = timedelta(seconds=30 + 120 + 300 + 180 + 90)
        assert app._total_duration == expected

    def test_total_duration_empty(self) -> None:
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=[])
        assert app._total_duration == timedelta()


# ---------------------------------------------------------------------------
# Pilot tests — single iteration session
# ---------------------------------------------------------------------------


class TestSingleIteration:
    """Edge case: session with exactly one iteration."""

    @pytest.mark.asyncio
    async def test_single_iteration_subtitle(self) -> None:
        iters = [_make_iteration(1, cost="0.10", duration_secs=5)]
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=iters)
        async with app.run_test():
            assert "1 iterations" in app.sub_title
            assert "$0.10" in app.sub_title

    @pytest.mark.asyncio
    async def test_single_iteration_has_panels(self) -> None:
        iters = [_make_iteration(1)]
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=iters)
        async with app.run_test():
            assert len(app.query("#left-panel")) == 1
            assert len(app.query("#right-panel")) == 1


# ---------------------------------------------------------------------------
# Pilot tests — varied phases in subtitle
# ---------------------------------------------------------------------------


class TestMultiPhaseStats:
    """Stats computed correctly across multiple phases."""

    @pytest.mark.asyncio
    async def test_large_cost_formatted(self) -> None:
        iters = [_make_iteration(1, cost="123.456", duration_secs=7200)]
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=iters)
        async with app.run_test():
            assert "$123.46" in app.sub_title
            assert "2h" in app.sub_title

    @pytest.mark.asyncio
    async def test_zero_duration_formatted(self) -> None:
        iters = [_make_iteration(1, cost="0.01", duration_secs=0)]
        app = ReplayApp(project_dir=SAMPLE_PROJECT_DIR, iterations=iters)
        async with app.run_test():
            assert "0s" in app.sub_title


# ---------------------------------------------------------------------------
# Integration test — cli._launch_tui wiring
# ---------------------------------------------------------------------------


class TestCliWiring:
    """Verify that cli._launch_tui can import ReplayApp."""

    def test_import_replay_app(self) -> None:
        from agent_replay.tui.app import ReplayApp as Imported

        assert Imported is ReplayApp

    def test_cli_launch_tui_importable(self) -> None:
        """_launch_tui in cli.py references ReplayApp — verify the import path works."""
        from agent_replay.cli import _launch_tui

        assert callable(_launch_tui)
