"""Tests for agent_replay.models dataclasses.

Verifies instantiation, field types, Decimal usage, and default values.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from agent_replay.models import (
    CostEntry,
    GitCommit,
    Iteration,
    MetricsEntry,
    PhaseEntry,
    PlanItem,
    SessionBlock,
    TimelineEvent,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UTC = timezone.utc


def _ts(year: int = 2026, month: int = 3, day: int = 24) -> datetime:
    return datetime(year, month, day, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# CostEntry
# ---------------------------------------------------------------------------


class TestCostEntry:
    def test_instantiation(self) -> None:
        entry = CostEntry(
            timestamp=_ts(),
            phase="build",
            iter=1,
            model="claude-sonnet-4-6",
            tokens_in=1000,
            tokens_out=500,
            cost=Decimal("0.015"),
            cumulative=Decimal("0.030"),
            item="3",
        )
        assert entry.phase == "build"
        assert entry.iter == 1
        assert entry.tokens_in == 1000

    def test_cost_is_decimal(self) -> None:
        entry = CostEntry(
            timestamp=_ts(),
            phase="build",
            iter=1,
            model="claude-sonnet-4-6",
            tokens_in=100,
            tokens_out=50,
            cost=Decimal("0.001500"),
            cumulative=Decimal("0.001500"),
            item="",
        )
        assert isinstance(entry.cost, Decimal)
        assert isinstance(entry.cumulative, Decimal)

    def test_decimal_precision_preserved(self) -> None:
        cost = Decimal("0.012345678901234")
        entry = CostEntry(
            timestamp=_ts(),
            phase="build",
            iter=2,
            model="claude-opus-4-6",
            tokens_in=200,
            tokens_out=100,
            cost=cost,
            cumulative=cost * 2,
            item="",
        )
        assert entry.cost == cost

    def test_item_empty_string(self) -> None:
        entry = CostEntry(
            timestamp=_ts(),
            phase="socratic",
            iter=1,
            model="claude-sonnet-4-6",
            tokens_in=10,
            tokens_out=5,
            cost=Decimal("0"),
            cumulative=Decimal("0"),
            item="",
        )
        assert entry.item == ""

    def test_item_digit_string(self) -> None:
        entry = CostEntry(
            timestamp=_ts(),
            phase="build",
            iter=3,
            model="claude-sonnet-4-6",
            tokens_in=10,
            tokens_out=5,
            cost=Decimal("0"),
            cumulative=Decimal("0"),
            item="7",
        )
        assert entry.item == "7"

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(CostEntry)

    def test_field_types_annotated(self) -> None:
        hints = {f.name: f.type for f in dataclasses.fields(CostEntry)}
        assert "timestamp" in hints
        assert "cost" in hints
        assert "cumulative" in hints


# ---------------------------------------------------------------------------
# PhaseEntry
# ---------------------------------------------------------------------------


class TestPhaseEntry:
    def test_instantiation(self) -> None:
        entry = PhaseEntry(
            timestamp=_ts(),
            event_type="TRANSITION",
            params={"from": "socratic", "to": "plan"},
        )
        assert entry.event_type == "TRANSITION"
        assert entry.params["from"] == "socratic"

    def test_start_event(self) -> None:
        entry = PhaseEntry(
            timestamp=_ts(),
            event_type="START",
            params={"phase": "build", "version": "v2"},
        )
        assert entry.event_type == "START"
        assert entry.params["phase"] == "build"

    def test_circuit_breaker_event(self) -> None:
        entry = PhaseEntry(
            timestamp=_ts(),
            event_type="CIRCUIT_BREAKER",
            params={"message": "Stuck 3 iterations", "phase": "build"},
        )
        assert entry.event_type == "CIRCUIT_BREAKER"

    def test_params_is_dict(self) -> None:
        entry = PhaseEntry(
            timestamp=_ts(),
            event_type="START",
            params={},
        )
        assert isinstance(entry.params, dict)

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PhaseEntry)


# ---------------------------------------------------------------------------
# GitCommit
# ---------------------------------------------------------------------------


class TestGitCommit:
    def test_instantiation(self) -> None:
        commit = GitCommit(
            hash="abc123def456",
            message="feat: add parser",
            timestamp=_ts(),
        )
        assert commit.hash == "abc123def456"
        assert commit.message == "feat: add parser"
        assert commit.timestamp.tzinfo is not None

    def test_timezone_aware(self) -> None:
        commit = GitCommit(hash="aaa", message="msg", timestamp=_ts())
        assert commit.timestamp.tzinfo == UTC

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(GitCommit)


# ---------------------------------------------------------------------------
# SessionBlock
# ---------------------------------------------------------------------------


class TestSessionBlock:
    def test_instantiation(self) -> None:
        block = SessionBlock(
            timestamp=_ts(),
            content="Completed: Item 3 - Parser\nChanges: added parser",
            items_completed=["Item 3 - Parser"],
        )
        assert "Item 3" in block.content
        assert block.items_completed == ["Item 3 - Parser"]

    def test_empty_items_completed(self) -> None:
        block = SessionBlock(
            timestamp=_ts(),
            content="Some freeform text",
            items_completed=[],
        )
        assert block.items_completed == []

    def test_multiple_completed(self) -> None:
        block = SessionBlock(
            timestamp=_ts(),
            content="",
            items_completed=["Item 1 - Models", "Item 2 - Fixtures"],
        )
        assert len(block.items_completed) == 2

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(SessionBlock)


# ---------------------------------------------------------------------------
# PlanItem
# ---------------------------------------------------------------------------


class TestPlanItem:
    def test_instantiation(self) -> None:
        item = PlanItem(number=1, title="Data Models", status="DONE", priority="P0")
        assert item.number == 1
        assert item.status == "DONE"
        assert item.priority == "P0"

    def test_todo_status(self) -> None:
        item = PlanItem(number=5, title="Something", status="TODO", priority="P1")
        assert item.status == "TODO"

    def test_in_progress_status(self) -> None:
        item = PlanItem(number=3, title="Parser", status="IN_PROGRESS", priority="P0")
        assert item.status == "IN_PROGRESS"

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(PlanItem)


# ---------------------------------------------------------------------------
# MetricsEntry
# ---------------------------------------------------------------------------


class TestMetricsEntry:
    def test_instantiation(self) -> None:
        entry = MetricsEntry(
            timestamp=_ts(),
            metric="error_count",
            context="build",
            value="2",
            detail="lint_errors",
        )
        assert entry.metric == "error_count"
        assert entry.value == "2"

    def test_four_fields_required(self) -> None:
        # All four data fields must be present
        fields = {f.name for f in dataclasses.fields(MetricsEntry)}
        assert "metric" in fields
        assert "context" in fields
        assert "value" in fields
        assert "detail" in fields

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(MetricsEntry)


# ---------------------------------------------------------------------------
# TimelineEvent
# ---------------------------------------------------------------------------


class TestTimelineEvent:
    def _make_cost_entry(self) -> CostEntry:
        return CostEntry(
            timestamp=_ts(),
            phase="build",
            iter=1,
            model="claude-sonnet-4-6",
            tokens_in=100,
            tokens_out=50,
            cost=Decimal("0.001"),
            cumulative=Decimal("0.001"),
            item="",
        )

    def test_cost_event(self) -> None:
        cost = self._make_cost_entry()
        event = TimelineEvent(
            timestamp=_ts(),
            event_type="cost",
            phase="build",
            iteration=1,
            data=cost,
        )
        assert event.event_type == "cost"
        assert isinstance(event.data, CostEntry)

    def test_phase_event(self) -> None:
        phase = PhaseEntry(timestamp=_ts(), event_type="START", params={})
        event = TimelineEvent(
            timestamp=_ts(),
            event_type="phase",
            phase="socratic",
            iteration=0,
            data=phase,
        )
        assert isinstance(event.data, PhaseEntry)

    def test_commit_event(self) -> None:
        commit = GitCommit(hash="abc", message="fix", timestamp=_ts())
        event = TimelineEvent(
            timestamp=_ts(),
            event_type="commit",
            phase="build",
            iteration=2,
            data=commit,
        )
        assert isinstance(event.data, GitCommit)

    def test_session_event(self) -> None:
        block = SessionBlock(timestamp=_ts(), content="text", items_completed=[])
        event = TimelineEvent(
            timestamp=_ts(),
            event_type="session",
            phase="build",
            iteration=1,
            data=block,
        )
        assert isinstance(event.data, SessionBlock)

    def test_metrics_event(self) -> None:
        metrics = MetricsEntry(
            timestamp=_ts(),
            metric="error_count",
            context="build",
            value="0",
            detail="",
        )
        event = TimelineEvent(
            timestamp=_ts(),
            event_type="metrics",
            phase="build",
            iteration=1,
            data=metrics,
        )
        assert isinstance(event.data, MetricsEntry)

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(TimelineEvent)


# ---------------------------------------------------------------------------
# Iteration
# ---------------------------------------------------------------------------


class TestIteration:
    def test_minimal_instantiation(self) -> None:
        it = Iteration(number=1, phase="build")
        assert it.number == 1
        assert it.phase == "build"
        assert it.status == "OK"

    def test_default_cost_is_decimal_zero(self) -> None:
        it = Iteration(number=1, phase="build")
        assert isinstance(it.cost_total, Decimal)
        assert it.cost_total == Decimal("0")

    def test_default_tokens_zero(self) -> None:
        it = Iteration(number=1, phase="build")
        assert it.tokens_in == 0
        assert it.tokens_out == 0

    def test_default_empty_lists(self) -> None:
        it = Iteration(number=1, phase="build")
        assert it.events == []
        assert it.items_done == []
        assert it.git_commits == []

    def test_default_duration_zero(self) -> None:
        it = Iteration(number=1, phase="build")
        assert it.duration == timedelta(0)

    def test_status_ok(self) -> None:
        it = Iteration(number=1, phase="build", status="OK")
        assert it.status == "OK"

    def test_status_fail(self) -> None:
        it = Iteration(number=2, phase="build", status="FAIL")
        assert it.status == "FAIL"

    def test_status_stuck(self) -> None:
        it = Iteration(number=3, phase="build", status="STUCK")
        assert it.status == "STUCK"

    def test_cost_is_decimal(self) -> None:
        it = Iteration(number=1, phase="build", cost_total=Decimal("1.234567"))
        assert isinstance(it.cost_total, Decimal)

    def test_duration_is_timedelta(self) -> None:
        delta = timedelta(minutes=5, seconds=30)
        it = Iteration(number=1, phase="build", duration=delta)
        assert it.duration == delta

    def test_mutable_defaults_not_shared(self) -> None:
        # Verify each Iteration gets its own list instances (field(default_factory=list))
        it1 = Iteration(number=1, phase="build")
        it2 = Iteration(number=2, phase="build")
        it1.events.append(
            TimelineEvent(
                timestamp=_ts(),
                event_type="cost",
                phase="build",
                iteration=1,
                data=CostEntry(
                    timestamp=_ts(),
                    phase="build",
                    iter=1,
                    model="m",
                    tokens_in=1,
                    tokens_out=1,
                    cost=Decimal("0"),
                    cumulative=Decimal("0"),
                    item="",
                ),
            )
        )
        assert len(it2.events) == 0

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(Iteration)

    def test_full_instantiation(self) -> None:
        commit = GitCommit(hash="abc", message="feat", timestamp=_ts())
        it = Iteration(
            number=5,
            phase="verify",
            events=[],
            cost_total=Decimal("0.25"),
            tokens_in=5000,
            tokens_out=2000,
            items_done=["Item 3 - Parser"],
            git_commits=[commit],
            status="OK",
            duration=timedelta(minutes=3),
        )
        assert it.number == 5
        assert it.cost_total == Decimal("0.25")
        assert it.tokens_in == 5000
        assert len(it.git_commits) == 1
        assert it.duration == timedelta(minutes=3)
