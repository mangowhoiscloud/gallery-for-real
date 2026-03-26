"""Tests for TUI Search feature (Item 19).

Uses Textual's pilot testing framework to verify:
- action_search() mounts the search Input and gives it focus
- action_close_search() removes the Input widget
- Enter with a keyword jumps to the first matching iteration
- Repeated Enter with same keyword cycles through multiple matches
- Enter with non-matching keyword triggers warning notification
- Enter with empty input does nothing harmful
- IterationList.jump_to() moves cursor to correct index

Clarity Round 12: search is scoped to progress.txt SessionBlock content only.

Note on pilot key simulation: In Textual 8.1.1 headless tests, pressing printable
characters (including "/" and numeric keys) may be routed to the focused Input widget
rather than triggering App-level bindings. To avoid this, search action tests call
app.action_search() directly. The "slash" binding existence is verified via BINDINGS
inspection. Dynamic mount/unmount of the Input prevents DOM-level focus interference
with tab-switch bindings (1–4).
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
    SessionBlock,
    TimelineEvent,
)
from agent_replay.tui.app import ReplayApp
from agent_replay.tui.iteration_list import IterationList

from textual.widgets import Input, ListView


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROJECT_DIR = Path("/tmp/test-project")


def _make_iteration(
    number: int,
    phase: str = "build",
    cost: str = "0.50",
    status: str = "OK",
    session_content: str | None = None,
) -> Iteration:
    """Create a minimal Iteration, optionally with a SessionBlock event."""
    ts = datetime(2026, 3, 25, hour=number % 24, tzinfo=timezone.utc)
    events: list[TimelineEvent] = []

    cost_entry = CostEntry(
        timestamp=ts,
        phase=phase,
        iter=number,
        model="opus",
        tokens_in=20,
        tokens_out=8000,
        cost=Decimal(cost),
        cumulative=Decimal(cost),
        item="",
    )
    events.append(
        TimelineEvent(
            timestamp=ts,
            event_type="cost",
            phase=phase,
            iteration=number,
            data=cost_entry,
        )
    )

    if session_content is not None:
        block = SessionBlock(
            timestamp=ts,
            content=session_content,
            items_completed=[],
        )
        events.append(
            TimelineEvent(
                timestamp=ts,
                event_type="session",
                phase=phase,
                iteration=number,
                data=block,
            )
        )

    git_commits = [
        GitCommit(
            hash=f"abc{number:04d}00",
            message=f"feat: item {number}",
            timestamp=ts,
        )
    ]

    return Iteration(
        number=number,
        phase=phase,
        events=events,
        cost_total=Decimal(cost),
        tokens_in=20,
        tokens_out=8000,
        items_done=[],
        git_commits=git_commits,
        status=status,
        duration=timedelta(seconds=60),
    )


# Iterations: 1 and 3 have session content matching "alpha", iteration 2 has "beta"
_ITER_1 = _make_iteration(1, phase="socratic", session_content="alpha phase socratic")
_ITER_2 = _make_iteration(2, phase="plan", session_content="beta planning content")
_ITER_3 = _make_iteration(3, phase="build", session_content="alpha build result")
_ITER_4 = _make_iteration(4, phase="build")  # no session block

SAMPLE_ITERATIONS = [_ITER_1, _ITER_2, _ITER_3, _ITER_4]


# ---------------------------------------------------------------------------
# IterationList.jump_to() unit tests
# ---------------------------------------------------------------------------

class TestIterationListJumpTo:
    """Unit tests for IterationList.jump_to() — uses pilot for widget mounting."""

    @pytest.mark.asyncio
    async def test_jump_to_found(self) -> None:
        """jump_to returns True and sets index when iteration exists."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            il = app.query_one(IterationList)
            result = il.jump_to(3)
            await pilot.pause()
            assert result is True
            lv = il.query_one(ListView)
            assert lv.index == 2  # 0-based index for iteration #3

    @pytest.mark.asyncio
    async def test_jump_to_not_found(self) -> None:
        """jump_to returns False for a non-existent iteration number."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            il = app.query_one(IterationList)
            result = il.jump_to(999)
            assert result is False

    @pytest.mark.asyncio
    async def test_jump_to_first(self) -> None:
        """jump_to iteration #1 sets index to 0."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            il = app.query_one(IterationList)
            il.jump_to(3)
            await pilot.pause()
            il.jump_to(1)
            await pilot.pause()
            lv = il.query_one(ListView)
            assert lv.index == 0

    @pytest.mark.asyncio
    async def test_jump_to_last(self) -> None:
        """jump_to last iteration sets index to len-1."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            il = app.query_one(IterationList)
            result = il.jump_to(4)
            await pilot.pause()
            assert result is True
            lv = il.query_one(ListView)
            assert lv.index == 3


# ---------------------------------------------------------------------------
# Search bar visibility via action methods
# ---------------------------------------------------------------------------

class TestSearchBarToggle:
    """Verify search bar show/hide via action_search() and action_close_search().

    The Input is mounted dynamically (not in compose) to avoid intercepting
    numeric keybindings. Tests call action methods directly; binding existence
    is verified via BINDINGS inspection.
    """

    @pytest.mark.asyncio
    async def test_search_bar_absent_initially(self) -> None:
        """Search bar Input is NOT in the DOM on startup."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert len(app.query("#search-bar")) == 0

    @pytest.mark.asyncio
    async def test_action_search_mounts_bar(self) -> None:
        """action_search() mounts the search Input widget."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            assert len(app.query("#search-bar")) == 1

    @pytest.mark.asyncio
    async def test_action_close_search_removes_bar(self) -> None:
        """action_close_search() removes the search Input widget."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            app.action_close_search()
            await pilot.pause()
            assert len(app.query("#search-bar")) == 0

    @pytest.mark.asyncio
    async def test_action_search_focuses_bar(self) -> None:
        """action_search() focuses the mounted search bar Input."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            assert bar.has_focus

    @pytest.mark.asyncio
    async def test_action_search_idempotent(self) -> None:
        """Calling action_search() twice only mounts one Input widget."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            assert len(app.query("#search-bar")) == 1

    def test_slash_binding_exists(self) -> None:
        """'slash' key is bound to 'search' action in BINDINGS."""
        slash_binding = next(
            (b for b in ReplayApp.BINDINGS if b.key == "slash"),
            None,
        )
        assert slash_binding is not None
        assert slash_binding.action == "search"

    def test_escape_binding_exists(self) -> None:
        """'escape' key is bound to 'close_search' action in BINDINGS."""
        esc_binding = next(
            (b for b in ReplayApp.BINDINGS if b.key == "escape"),
            None,
        )
        assert esc_binding is not None
        assert esc_binding.action == "close_search"


# ---------------------------------------------------------------------------
# Search execution: finding matches and jumping
# ---------------------------------------------------------------------------

class TestSearchExecution:
    """Verify search finds matching iterations and updates iteration list cursor."""

    @pytest.mark.asyncio
    async def test_search_jumps_to_first_match(self) -> None:
        """Searching 'beta' jumps to iteration #2 (only match)."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "beta"
            await pilot.press("enter")
            await pilot.pause()
            # Cursor should be at iteration #2 (index 1)
            lv = app.query_one(IterationList).query_one(ListView)
            assert lv.index == 1

    @pytest.mark.asyncio
    async def test_search_keyword_stored(self) -> None:
        """After a search, _search_keyword is stored on the app."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "beta"
            await pilot.press("enter")
            await pilot.pause()
            assert app._search_keyword == "beta"

    @pytest.mark.asyncio
    async def test_search_matches_stored(self) -> None:
        """After searching 'alpha', _search_matches contains [1, 3]."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "alpha"
            await pilot.press("enter")
            await pilot.pause()
            assert app._search_matches == [1, 3]

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self) -> None:
        """Search is case-insensitive: 'ALPHA' matches 'alpha phase socratic'."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "ALPHA"
            await pilot.press("enter")
            await pilot.pause()
            assert 1 in app._search_matches
            assert 3 in app._search_matches

    @pytest.mark.asyncio
    async def test_search_no_match_no_jump(self) -> None:
        """Searching a non-matching keyword leaves the cursor unchanged."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            lv = app.query_one(IterationList).query_one(ListView)
            initial_index = lv.index
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "xyzzy_no_match"
            await pilot.press("enter")
            await pilot.pause()
            assert lv.index == initial_index

    @pytest.mark.asyncio
    async def test_search_no_match_clears_matches(self) -> None:
        """Non-matching search stores empty list in _search_matches."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "xyzzy_no_match"
            await pilot.press("enter")
            await pilot.pause()
            assert app._search_matches == []

    @pytest.mark.asyncio
    async def test_search_empty_input_no_change(self) -> None:
        """Submitting empty input does not crash or change state."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = ""
            await pilot.press("enter")
            await pilot.pause()
            assert app._search_keyword == ""
            assert app._search_matches == []

    @pytest.mark.asyncio
    async def test_search_iteration_without_session_block_not_matched(self) -> None:
        """Iteration #4 has no session block; it's never matched by search."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "build"  # iter 3 has "alpha build result"
            await pilot.press("enter")
            await pilot.pause()
            # Only iteration 3 should match (has "build" in session content)
            assert 4 not in app._search_matches


# ---------------------------------------------------------------------------
# Repeated search: cycling through multiple matches
# ---------------------------------------------------------------------------

class TestSearchCycling:
    """Verify that repeated Enter with same keyword cycles through matches."""

    @pytest.mark.asyncio
    async def test_first_enter_jumps_to_first_match(self) -> None:
        """First Enter for 'alpha' jumps to iteration #1 (first match)."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "alpha"
            await pilot.press("enter")
            await pilot.pause()
            lv = app.query_one(IterationList).query_one(ListView)
            assert lv.index == 0
            assert app._search_idx == 0

    @pytest.mark.asyncio
    async def test_second_enter_same_keyword_advances(self) -> None:
        """Second Enter with same 'alpha' keyword advances to iteration #3."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "alpha"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            lv = app.query_one(IterationList).query_one(ListView)
            assert lv.index == 2  # iteration #3 is index 2
            assert app._search_idx == 1

    @pytest.mark.asyncio
    async def test_third_enter_wraps_to_first_match(self) -> None:
        """Third Enter wraps back to iteration #1 (modulo cycle)."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "alpha"
            await pilot.press("enter")  # → iter #1
            await pilot.pause()
            await pilot.press("enter")  # → iter #3
            await pilot.pause()
            await pilot.press("enter")  # → wraps to iter #1
            await pilot.pause()
            lv = app.query_one(IterationList).query_one(ListView)
            assert lv.index == 0
            assert app._search_idx == 0

    @pytest.mark.asyncio
    async def test_new_keyword_resets_cycle(self) -> None:
        """Changing the keyword resets _search_idx to 0."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "alpha"
            await pilot.press("enter")
            await pilot.pause()
            await pilot.press("enter")  # advance to idx 1
            await pilot.pause()
            assert app._search_idx == 1
            bar.value = "beta"
            await pilot.press("enter")
            await pilot.pause()
            assert app._search_idx == 0
            assert app._search_keyword == "beta"

    @pytest.mark.asyncio
    async def test_single_match_cycling_stays_on_same(self) -> None:
        """Single-match keyword: cycling always returns to the same iteration."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            await app.action_search()
            await pilot.pause()
            bar = app.query_one("#search-bar", Input)
            bar.value = "beta"
            await pilot.press("enter")
            await pilot.pause()
            assert len(app._search_matches) == 1
            idx_before = app.query_one(IterationList).query_one(ListView).index
            await pilot.press("enter")  # cycle (only 1 match → stays)
            await pilot.pause()
            idx_after = app.query_one(IterationList).query_one(ListView).index
            assert idx_before == idx_after


# ---------------------------------------------------------------------------
# _find_matches unit-style tests via app API
# ---------------------------------------------------------------------------

class TestFindMatches:
    """Tests for ReplayApp._find_matches() logic."""

    @pytest.mark.asyncio
    async def test_find_matches_returns_correct_numbers(self) -> None:
        """_find_matches('alpha') returns [1, 3]."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            matches = app._find_matches("alpha")
            assert matches == [1, 3]

    @pytest.mark.asyncio
    async def test_find_matches_empty_on_no_match(self) -> None:
        """_find_matches with non-matching keyword returns []."""
        app = ReplayApp(_PROJECT_DIR, SAMPLE_ITERATIONS)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app._find_matches("zzzno") == []

    @pytest.mark.asyncio
    async def test_find_matches_each_iteration_once(self) -> None:
        """Each iteration appears at most once even if it has multiple blocks."""
        ts = datetime(2026, 3, 25, hour=5, tzinfo=timezone.utc)
        block1 = SessionBlock(timestamp=ts, content="dupe content", items_completed=[])
        block2 = SessionBlock(timestamp=ts, content="dupe content again", items_completed=[])
        cost_entry = CostEntry(
            timestamp=ts, phase="build", iter=1, model="opus",
            tokens_in=10, tokens_out=100, cost=Decimal("0.10"),
            cumulative=Decimal("0.10"), item="",
        )
        it = Iteration(
            number=5, phase="build",
            events=[
                TimelineEvent(timestamp=ts, event_type="cost", phase="build", iteration=5, data=cost_entry),
                TimelineEvent(timestamp=ts, event_type="session", phase="build", iteration=5, data=block1),
                TimelineEvent(timestamp=ts, event_type="session", phase="build", iteration=5, data=block2),
            ],
            cost_total=Decimal("0.10"),
            tokens_in=10, tokens_out=100,
            items_done=[], git_commits=[],
            status="OK", duration=timedelta(seconds=30),
        )
        iters = [it]
        app = ReplayApp(_PROJECT_DIR, iters)
        async with app.run_test() as pilot:
            await pilot.pause()
            matches = app._find_matches("dupe")
            assert matches == [5]

    @pytest.mark.asyncio
    async def test_find_matches_no_session_events(self) -> None:
        """Iterations with no session events are never matched."""
        app = ReplayApp(_PROJECT_DIR, [_ITER_4])  # _ITER_4 has no session block
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app._find_matches("build") == []
