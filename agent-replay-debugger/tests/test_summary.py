"""Tests for summary.py: print_summary() rich output.

Uses Console(file=StringIO(...)) for precise, deterministic output capture
without relying on capsys or terminal detection.
"""
from __future__ import annotations

import io
from datetime import timedelta
from decimal import Decimal

from rich.console import Console

from agent_replay.models import Iteration, PlanItem
from agent_replay.summary import print_summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _buf_console() -> tuple[Console, io.StringIO]:
    """Return a (Console, buffer) pair for output capture in tests."""
    buf = io.StringIO()
    # width=120, force_terminal=False — consistent plain-text rendering
    con = Console(file=buf, highlight=False, force_terminal=False, width=120)
    return con, buf


def _make_iter(
    number: int,
    phase: str = "build",
    status: str = "OK",
    cost: str = "1.00",
    tokens_in: int = 100,
    tokens_out: int = 500,
    items_done: list[str] | None = None,
    duration: timedelta | None = None,
) -> Iteration:
    return Iteration(
        number=number,
        phase=phase,
        status=status,
        cost_total=Decimal(cost),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        items_done=items_done or [],
        duration=duration or timedelta(seconds=60),
    )


def _make_plan_item(
    number: int,
    title: str,
    status: str = "TODO",
    priority: str = "P0",
) -> PlanItem:
    return PlanItem(number=number, title=title, status=status, priority=priority)


# ---------------------------------------------------------------------------
# Empty session
# ---------------------------------------------------------------------------


class TestEmptySession:
    def test_empty_session_prints_message(self) -> None:
        con, buf = _buf_console()
        print_summary([], None, [], console=con)
        assert "Empty session" in buf.getvalue()

    def test_empty_session_no_totals_printed(self) -> None:
        con, buf = _buf_console()
        print_summary([], None, [], console=con)
        assert "Iterations:" not in buf.getvalue()

    def test_empty_session_with_state_and_plan(self) -> None:
        """State and plan are ignored when there are no iterations."""
        con, buf = _buf_console()
        plan = [_make_plan_item(1, "Something", status="DONE")]
        print_summary([], {"phase": "build"}, plan, console=con)
        assert "Empty session" in buf.getvalue()
        assert "build" not in buf.getvalue()


# ---------------------------------------------------------------------------
# Iteration count, cost, tokens
# ---------------------------------------------------------------------------


class TestTotals:
    def test_shows_iteration_count(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1), _make_iter(2)], None, [], console=con)
        assert "Iterations:  2" in buf.getvalue()

    def test_shows_single_iteration(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1)], None, [], console=con)
        assert "Iterations:  1" in buf.getvalue()

    def test_total_cost_two_decimal_places(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, cost="1.50"), _make_iter(2, cost="2.50")]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "$4.00" in out

    def test_cost_not_four_decimal_places(self) -> None:
        """Spec says $X.XX format, not $X.XXXX."""
        con, buf = _buf_console()
        print_summary([_make_iter(1, cost="3.1416")], None, [], console=con)
        out = buf.getvalue()
        assert "$3.14" in out
        assert "3.1416" not in out

    def test_tokens_in_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, tokens_in=100), _make_iter(2, tokens_in=200)]
        print_summary(iters, None, [], console=con)
        assert "in=300" in buf.getvalue()

    def test_tokens_out_shown_with_comma_formatting(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, tokens_out=500), _make_iter(2, tokens_out=1_000)]
        print_summary(iters, None, [], console=con)
        assert "out=1,500" in buf.getvalue()

    def test_zero_cost_session(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1, cost="0")], None, [], console=con)
        assert "$0.00" in buf.getvalue()


# ---------------------------------------------------------------------------
# Status counts
# ---------------------------------------------------------------------------


class TestStatusCounts:
    def test_ok_count_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, status="OK"), _make_iter(2, status="OK")]
        print_summary(iters, None, [], console=con)
        assert "2 OK" in buf.getvalue()

    def test_fail_count_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, status="FAIL"), _make_iter(2, status="OK")]
        print_summary(iters, None, [], console=con)
        assert "1 FAIL" in buf.getvalue()

    def test_stuck_count_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, status="STUCK"), _make_iter(2, status="OK")]
        print_summary(iters, None, [], console=con)
        assert "1 STUCK" in buf.getvalue()

    def test_all_statuses_on_same_line(self) -> None:
        con, buf = _buf_console()
        iters = [
            _make_iter(1, status="OK"),
            _make_iter(2, status="FAIL"),
            _make_iter(3, status="STUCK"),
            _make_iter(4, status="OK"),
        ]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "2 OK" in out
        assert "1 FAIL" in out
        assert "1 STUCK" in out

    def test_all_ok_no_fail_stuck(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, status="OK"), _make_iter(2, status="OK")]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "0 FAIL" in out
        assert "0 STUCK" in out


# ---------------------------------------------------------------------------
# Per-phase breakdown
# ---------------------------------------------------------------------------


class TestPerPhaseBreakdown:
    def test_single_phase_shown_in_table(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1, phase="build")], None, [], console=con)
        out = buf.getvalue()
        assert "build" in out

    def test_multiple_phases_both_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, phase="build"), _make_iter(2, phase="test")]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "build" in out
        assert "test" in out

    def test_phase_iteration_count_in_table(self) -> None:
        con, buf = _buf_console()
        iters = [
            _make_iter(1, phase="build"),
            _make_iter(2, phase="build"),
            _make_iter(3, phase="test"),
        ]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        # "2" appears for build count, "1" for test count
        assert "2" in out

    def test_phase_cost_formatted_two_decimal(self) -> None:
        con, buf = _buf_console()
        iters = [
            _make_iter(1, phase="build", cost="1.50"),
            _make_iter(2, phase="build", cost="1.50"),
        ]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "$3.00" in out

    def test_per_phase_breakdown_title(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1)], None, [], console=con)
        assert "Per-Phase Breakdown" in buf.getvalue()


# ---------------------------------------------------------------------------
# Current state
# ---------------------------------------------------------------------------


class TestCurrentState:
    def test_current_phase_shown_when_state_provided(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1)], {"phase": "build"}, [], console=con)
        assert "build" in buf.getvalue()

    def test_current_phase_label(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1)], {"phase": "deploy"}, [], console=con)
        assert "deploy" in buf.getvalue()

    def test_current_phase_not_shown_when_state_none(self) -> None:
        con, buf = _buf_console()
        # No state dict → no "Current phase:" line
        print_summary([_make_iter(1, phase="build")], None, [], console=con)
        assert "Current phase:" not in buf.getvalue()

    def test_state_missing_phase_key_uses_unknown(self) -> None:
        con, buf = _buf_console()
        # Non-empty dict without a "phase" key → fallback to "unknown"
        print_summary([_make_iter(1)], {"status": "running"}, [], console=con)
        assert "unknown" in buf.getvalue()

    def test_state_extra_keys_ignored(self) -> None:
        con, buf = _buf_console()
        state = {"phase": "build", "status": "running", "other": "stuff"}
        print_summary([_make_iter(1)], state, [], console=con)
        assert "build" in buf.getvalue()


# ---------------------------------------------------------------------------
# Plan progress
# ---------------------------------------------------------------------------


class TestPlanProgress:
    def test_plan_progress_shown(self) -> None:
        con, buf = _buf_console()
        plan = [
            _make_plan_item(1, "Item A", status="DONE"),
            _make_plan_item(2, "Item B", status="DONE"),
            _make_plan_item(3, "Item C", status="TODO"),
        ]
        print_summary([_make_iter(1)], None, plan, console=con)
        out = buf.getvalue()
        assert "2 DONE" in out
        assert "1 TODO" in out

    def test_plan_progress_not_shown_when_empty(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1)], None, [], console=con)
        assert "DONE" not in buf.getvalue()

    def test_in_progress_counts_as_todo(self) -> None:
        con, buf = _buf_console()
        plan = [
            _make_plan_item(1, "A", status="DONE"),
            _make_plan_item(2, "B", status="IN_PROGRESS"),
            _make_plan_item(3, "C", status="TODO"),
        ]
        print_summary([_make_iter(1)], None, plan, console=con)
        out = buf.getvalue()
        assert "1 DONE" in out
        assert "2 TODO" in out

    def test_all_done_plan(self) -> None:
        con, buf = _buf_console()
        plan = [_make_plan_item(i, f"Item {i}", status="DONE") for i in range(1, 6)]
        print_summary([_make_iter(1)], None, plan, console=con)
        out = buf.getvalue()
        assert "5 DONE" in out
        assert "0 TODO" in out


# ---------------------------------------------------------------------------
# Items completed
# ---------------------------------------------------------------------------


class TestItemsCompleted:
    def test_items_shown(self) -> None:
        con, buf = _buf_console()
        iters = [_make_iter(1, items_done=["Item 3 - cost.log parser"])]
        print_summary(iters, None, [], console=con)
        assert "Item 3 - cost.log parser" in buf.getvalue()

    def test_items_from_multiple_iterations(self) -> None:
        con, buf = _buf_console()
        iters = [
            _make_iter(1, items_done=["Item 1 - models"]),
            _make_iter(2, items_done=["Item 2 - fixtures"]),
        ]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert "Item 1 - models" in out
        assert "Item 2 - fixtures" in out

    def test_items_deduplicated(self) -> None:
        """Same item appearing in two iterations should appear once."""
        con, buf = _buf_console()
        iters = [
            _make_iter(1, items_done=["Item 3 - parser"]),
            _make_iter(2, items_done=["Item 3 - parser", "Item 4 - other"]),
        ]
        print_summary(iters, None, [], console=con)
        out = buf.getvalue()
        assert out.count("Item 3 - parser") == 1

    def test_no_items_completed_section_absent(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1, items_done=[])], None, [], console=con)
        assert "Items completed:" not in buf.getvalue()

    def test_items_completed_label(self) -> None:
        con, buf = _buf_console()
        print_summary([_make_iter(1, items_done=["Item 1"])], None, [], console=con)
        assert "Items completed:" in buf.getvalue()
