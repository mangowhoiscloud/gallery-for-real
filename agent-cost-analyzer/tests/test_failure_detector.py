"""Tests for the failure pattern detector."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from agent_cost_analyzer.analyzer.failures import detect_failures
from agent_cost_analyzer.models import (
    CostEntry,
    FailurePatterns,
    PhaseEvent,
    SessionError,
)
from agent_cost_analyzer.parser.cost_log import parse_cost_log
from agent_cost_analyzer.parser.phase_log import parse_phase_log


def _ts(hour: int, tz_offset: int = 9) -> datetime:
    """Build a timezone-aware datetime on 2026-03-19 at the given hour."""
    from datetime import timedelta

    tz = timezone(timedelta(hours=tz_offset))
    return datetime(2026, 3, 19, hour, 0, 0, tzinfo=tz)


def _cost_entry(
    phase: str,
    iteration: int,
    item: int | None,
    ts_hour: int = 10,
) -> CostEntry:
    return CostEntry(
        timestamp=_ts(ts_hour),
        phase=phase,
        iteration=iteration,
        model="claude-sonnet-4-5",
        input_tokens=1000,
        output_tokens=500,
        cost=Decimal("0.10"),
        cumulative=Decimal("0.10"),
        item=item,
    )


def _phase_event(event: str, metadata: dict[str, str], hour: int = 14) -> PhaseEvent:
    return PhaseEvent(timestamp=_ts(hour), event=event, metadata=metadata)


# ---------------------------------------------------------------------------
# Fixture-based integration tests
# ---------------------------------------------------------------------------


class TestFixtureIntegration:
    def test_detect_stuck_on_item5_via_circuit_breaker(
        self, cost_log_path, phase_log_path
    ):
        entries = parse_cost_log(cost_log_path)
        events = parse_phase_log(phase_log_path)
        result = detect_failures(entries, events)

        assert len(result.stuck_events) == 1
        stuck = result.stuck_events[0]
        assert stuck.item == 5
        assert stuck.start_iteration == 5
        assert stuck.count == 3

    def test_circuit_breakers_extracted_from_fixture(
        self, cost_log_path, phase_log_path
    ):
        entries = parse_cost_log(cost_log_path)
        events = parse_phase_log(phase_log_path)
        result = detect_failures(entries, events)

        assert len(result.circuit_breakers) == 1
        cb = result.circuit_breakers[0]
        assert "Stuck 3 iterations" in cb.message
        assert cb.metadata.get("phase") == "build"

    def test_build_failure_rate_from_fixture(self, cost_log_path, phase_log_path):
        entries = parse_cost_log(cost_log_path)
        events = parse_phase_log(phase_log_path)
        result = detect_failures(entries, events)

        # 3 failed out of 8 build iterations
        assert result.build_failure_rate == pytest.approx(3 / 8)

    def test_recovery_time_for_item5(self, cost_log_path, phase_log_path):
        entries = parse_cost_log(cost_log_path)
        events = parse_phase_log(phase_log_path)
        result = detect_failures(entries, events)

        # item 5 appears in iters 5,6,7,8 → recovery = 4
        assert result.recovery_times[5] == 4


# ---------------------------------------------------------------------------
# Unit tests — stuck detection via phase events (primary)
# ---------------------------------------------------------------------------


class TestStuckFromPhaseEvents:
    def _make_cb_event(self, message: str, hour: int = 14) -> PhaseEvent:

        # Build a PhaseEvent manually
        return PhaseEvent(
            timestamp=_ts(hour),
            event="CIRCUIT_BREAKER",
            metadata={"message": message, "phase": "build", "model": "claude-opus-4-5"},
        )

    def test_circuit_breaker_produces_stuck_event(self):
        entries = [
            _cost_entry("build", 1, 1, ts_hour=10),
            _cost_entry("build", 2, 2, ts_hour=11),
            _cost_entry("build", 3, 3, ts_hour=12),
            _cost_entry("build", 4, 4, ts_hour=13),
            _cost_entry("build", 5, 5, ts_hour=14),  # CB at 14:30
        ]
        events = [self._make_cb_event("Stuck 3 iterations, phase=build, model=claude-opus-4-5")]
        result = detect_failures(entries, events)

        assert len(result.stuck_events) == 1
        stuck = result.stuck_events[0]
        assert stuck.item == 5
        assert stuck.start_iteration == 5
        assert stuck.count == 3

    def test_circuit_breaker_no_matching_entries_skipped(self):
        events = [self._make_cb_event("Stuck 2 iterations")]
        result = detect_failures([], events)

        assert result.stuck_events == []
        assert len(result.circuit_breakers) == 1  # CB still recorded

    def test_multiple_circuit_breakers(self):
        entries = [
            _cost_entry("build", 1, 1, ts_hour=10),
            _cost_entry("build", 2, 2, ts_hour=12),
        ]
        events = [
            PhaseEvent(
                timestamp=_ts(11),
                event="CIRCUIT_BREAKER",
                metadata={"message": "Stuck 3 iterations", "phase": "build"},
            ),
            PhaseEvent(
                timestamp=_ts(13),
                event="CIRCUIT_BREAKER",
                metadata={"message": "Stuck 2 iterations", "phase": "build"},
            ),
        ]
        result = detect_failures(entries, events)
        # count=0 ones (the "Stuck 2 iterations" has count=2 ≠ 0, OK) - both should produce stuck events
        assert len(result.circuit_breakers) == 2

    def test_cb_with_zero_count_skipped_in_stuck_events(self):
        entries = [_cost_entry("build", 1, 1, ts_hour=10)]
        events = [
            PhaseEvent(
                timestamp=_ts(11),
                event="CIRCUIT_BREAKER",
                metadata={"message": "No count here"},
            )
        ]
        result = detect_failures(entries, events)
        assert result.stuck_events == []
        assert len(result.circuit_breakers) == 1  # still recorded


# ---------------------------------------------------------------------------
# Unit tests — stuck detection fallback from cost entries
# ---------------------------------------------------------------------------


class TestStuckFromCostEntries:
    def test_no_phase_events_uses_fallback(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
            _cost_entry("build", 3, 3),
            _cost_entry("build", 4, 3),
            _cost_entry("build", 5, 3),
        ]
        result = detect_failures(entries, [])

        assert len(result.stuck_events) == 1
        stuck = result.stuck_events[0]
        assert stuck.item == 3
        assert stuck.start_iteration == 3
        assert stuck.count == 2  # 3 occurrences → 2 failures

    def test_exactly_three_consecutive_triggers_stuck(self):
        entries = [
            _cost_entry("build", 1, 7),
            _cost_entry("build", 2, 7),
            _cost_entry("build", 3, 7),
        ]
        result = detect_failures(entries, [])

        assert len(result.stuck_events) == 1
        assert result.stuck_events[0].count == 2  # 3 total − 1

    def test_two_consecutive_does_not_trigger_stuck(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
            _cost_entry("build", 3, 2),
        ]
        result = detect_failures(entries, [])

        assert result.stuck_events == []

    def test_multiple_stuck_groups_detected(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 1),
            _cost_entry("build", 3, 1),
            _cost_entry("build", 4, 2),
            _cost_entry("build", 5, 3),
            _cost_entry("build", 6, 3),
            _cost_entry("build", 7, 3),
        ]
        result = detect_failures(entries, [])

        assert len(result.stuck_events) == 2
        items = {s.item for s in result.stuck_events}
        assert items == {1, 3}

    def test_non_build_phases_ignored(self):
        entries = [
            _cost_entry("socratic", 1, None),
            _cost_entry("plan", 1, None),
            _cost_entry("build", 1, 5),
            _cost_entry("verify", 1, None),
        ]
        result = detect_failures(entries, [])
        assert result.stuck_events == []

    def test_none_item_entries_excluded_from_fallback(self):
        entries = [
            _cost_entry("build", 1, None),
            _cost_entry("build", 2, None),
            _cost_entry("build", 3, None),
        ]
        result = detect_failures(entries, [])
        assert result.stuck_events == []


# ---------------------------------------------------------------------------
# Unit tests — build failure rate
# ---------------------------------------------------------------------------


class TestBuildFailureRate:
    def test_no_failures(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
            _cost_entry("build", 3, 3),
        ]
        result = detect_failures(entries, [])
        assert result.build_failure_rate == 0.0

    def test_all_failures(self):
        # All consecutive pairs same item
        entries = [
            _cost_entry("build", 1, 9),
            _cost_entry("build", 2, 9),
            _cost_entry("build", 3, 9),
            _cost_entry("build", 4, 9),
        ]
        result = detect_failures(entries, [])
        # 3 failed pairs out of 4 entries
        assert result.build_failure_rate == pytest.approx(3 / 4)

    def test_partial_failure_rate(self):
        # iters 2,3 same item → 1 fail out of 3 entries
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
            _cost_entry("build", 3, 2),
        ]
        result = detect_failures(entries, [])
        assert result.build_failure_rate == pytest.approx(1 / 3)

    def test_empty_build_entries_rate_zero(self):
        entries = [_cost_entry("socratic", 1, None)]
        result = detect_failures(entries, [])
        assert result.build_failure_rate == 0.0

    def test_single_build_entry_rate_zero(self):
        entries = [_cost_entry("build", 1, 1)]
        result = detect_failures(entries, [])
        assert result.build_failure_rate == 0.0


# ---------------------------------------------------------------------------
# Unit tests — recovery times
# ---------------------------------------------------------------------------


class TestRecoveryTimes:
    def test_recovery_time_equals_total_item_occurrences(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
            _cost_entry("build", 3, 2),
            _cost_entry("build", 4, 2),
        ]
        result = detect_failures(entries, [])

        # item 2 is stuck with 3 occurrences
        assert result.recovery_times[2] == 3

    def test_no_stuck_no_recovery(self):
        entries = [
            _cost_entry("build", 1, 1),
            _cost_entry("build", 2, 2),
        ]
        result = detect_failures(entries, [])
        assert result.recovery_times == {}

    def test_fixture_recovery_time(self, cost_log_path, phase_log_path):
        entries = parse_cost_log(cost_log_path)
        events = parse_phase_log(phase_log_path)
        result = detect_failures(entries, events)
        assert result.recovery_times[5] == 4


# ---------------------------------------------------------------------------
# Unit tests — session error categorization
# ---------------------------------------------------------------------------


class TestErrorCategories:
    def test_session_errors_grouped_by_type(self):
        errors = [
            SessionError(file="f1.log", line_num=1, error_type="bash_error", message="oops"),
            SessionError(file="f2.log", line_num=2, error_type="bash_error", message="again"),
            SessionError(file="f3.log", line_num=3, error_type="tool_error", message="fail"),
        ]
        result = detect_failures([], [], session_errors=errors)
        assert result.error_categories == {"bash_error": 2, "tool_error": 1}

    def test_no_session_errors_empty_categories(self):
        result = detect_failures([], [])
        assert result.error_categories == {}

    def test_none_session_errors_empty_categories(self):
        result = detect_failures([], [], session_errors=None)
        assert result.error_categories == {}

    def test_recovery_errors_counted(self):
        errors = [
            SessionError(
                file="recovery_build_iter3.log",
                line_num=1,
                error_type="recovery",
                message="retrying",
                is_recovery=True,
            )
        ]
        result = detect_failures([], [], session_errors=errors)
        assert result.error_categories == {"recovery": 1}


# ---------------------------------------------------------------------------
# Unit tests — empty inputs
# ---------------------------------------------------------------------------


class TestEmptyInputs:
    def test_empty_all_returns_default(self):
        result = detect_failures([], [])
        assert result.stuck_events == []
        assert result.circuit_breakers == []
        assert result.build_failure_rate == 0.0
        assert result.error_categories == {}
        assert result.recovery_times == {}

    def test_returns_failure_patterns_type(self):
        result = detect_failures([], [])
        assert isinstance(result, FailurePatterns)

    def test_non_build_only_entries(self):
        entries = [
            _cost_entry("socratic", 1, None),
            _cost_entry("plan", 1, None),
            _cost_entry("verify", 1, None),
        ]
        result = detect_failures(entries, [])
        assert result.stuck_events == []
        assert result.build_failure_rate == 0.0


# ---------------------------------------------------------------------------
# Unit tests — circuit breakers always extracted from phase events
# ---------------------------------------------------------------------------


class TestCircuitBreakerExtraction:
    def test_non_circuit_breaker_events_not_added(self):
        events = [
            _phase_event("START", {"phase": "build", "version": "v1"}),
            _phase_event("TRANSITION", {"from": "socratic", "to": "plan"}),
            _phase_event("COMPLETE", {"total_iter": "9", "cost": "$3.06"}),
        ]
        result = detect_failures([], events)
        assert result.circuit_breakers == []

    def test_circuit_breakers_always_populated_even_with_no_cost_entries(self):
        events = [
            PhaseEvent(
                timestamp=_ts(14),
                event="CIRCUIT_BREAKER",
                metadata={
                    "message": "Stuck 3 iterations, phase=build",
                    "phase": "build",
                },
            )
        ]
        result = detect_failures([], events)
        assert len(result.circuit_breakers) == 1
        assert "Stuck 3 iterations" in result.circuit_breakers[0].message
        # message key is not in metadata dict of the CircuitBreakerEvent
        assert "message" not in result.circuit_breakers[0].metadata

    def test_circuit_breaker_metadata_excludes_message_key(self):
        events = [
            PhaseEvent(
                timestamp=_ts(14),
                event="CIRCUIT_BREAKER",
                metadata={"message": "Stuck 2 iterations", "phase": "build"},
            )
        ]
        result = detect_failures([], events)
        cb = result.circuit_breakers[0]
        assert cb.message == "Stuck 2 iterations"
        assert cb.metadata == {"phase": "build"}
