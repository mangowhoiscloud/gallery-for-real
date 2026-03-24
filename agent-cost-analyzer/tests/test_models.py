"""Unit tests for data models."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from agent_cost_analyzer.models import (
    AnalysisResult,
    AnomalyEntry,
    CircuitBreakerEvent,
    CostBreakdown,
    CostEntry,
    EfficiencyEntry,
    EscalationEvent,
    FailurePatterns,
    MetricEntry,
    ModelTokenData,
    PhaseEvent,
    PhaseTokenData,
    ProgressData,
    ProjectSummaryRow,
    SessionError,
    StuckEvent,
    TokenAnalysis,
)


def ts() -> datetime:
    return datetime(2026, 3, 19, 12, 0, 0, tzinfo=timezone.utc)


class TestCostEntry:
    def test_construction_with_all_fields(self) -> None:
        entry = CostEntry(
            timestamp=ts(),
            phase="build",
            iteration=3,
            model="claude-opus-4-6",
            input_tokens=1000,
            output_tokens=500,
            cost=Decimal("0.1234"),
            cumulative=Decimal("1.5678"),
            item=2,
        )
        assert entry.phase == "build"
        assert entry.iteration == 3
        assert entry.model == "claude-opus-4-6"
        assert entry.input_tokens == 1000
        assert entry.output_tokens == 500

    def test_cost_is_decimal(self) -> None:
        entry = CostEntry(ts(), "plan", 1, "sonnet", 100, 200, Decimal("0.05"), Decimal("0.10"), None)
        assert isinstance(entry.cost, Decimal)
        assert isinstance(entry.cumulative, Decimal)

    def test_item_is_none_for_non_build(self) -> None:
        for phase in ("socratic", "plan", "verify"):
            entry = CostEntry(ts(), phase, 1, "sonnet", 100, 200, Decimal("0.05"), Decimal("0.05"), None)
            assert entry.item is None, f"Expected item=None for phase={phase}"

    def test_item_is_int_for_build(self) -> None:
        entry = CostEntry(ts(), "build", 1, "sonnet", 100, 200, Decimal("0.05"), Decimal("0.05"), 1)
        assert isinstance(entry.item, int)
        assert entry.item == 1

    def test_item_none_is_distinct_from_zero(self) -> None:
        entry = CostEntry(ts(), "socratic", 1, "sonnet", 0, 0, Decimal("0"), Decimal("0"), None)
        assert entry.item is None
        assert entry.item != 0


class TestPhaseEvent:
    def test_construction(self) -> None:
        event = PhaseEvent(timestamp=ts(), event="START", metadata={"phase": "build", "version": "1.0"})
        assert event.event == "START"
        assert event.metadata["phase"] == "build"
        assert event.metadata["version"] == "1.0"

    def test_default_metadata_is_empty_dict(self) -> None:
        event = PhaseEvent(timestamp=ts(), event="COMPLETE")
        assert event.metadata == {}

    def test_metadata_is_mutable_per_instance(self) -> None:
        e1 = PhaseEvent(timestamp=ts(), event="A")
        e2 = PhaseEvent(timestamp=ts(), event="B")
        e1.metadata["key"] = "val"
        assert "key" not in e2.metadata


class TestMetricEntry:
    def test_construction(self) -> None:
        entry = MetricEntry(timestamp=ts(), metric="error_count", context="build_iter_3", value=2, detail=1)
        assert entry.metric == "error_count"
        assert entry.context == "build_iter_3"
        assert isinstance(entry.value, int)
        assert isinstance(entry.detail, int)


class TestProgressData:
    def test_defaults(self) -> None:
        data = ProgressData()
        assert data.project_type == ""
        assert data.init_time is None
        assert data.sessions == []
        assert data.completed_items == []
        assert data.is_complete is False

    def test_construction(self) -> None:
        t = ts()
        data = ProgressData(
            project_type="Python",
            init_time=t,
            sessions=[t],
            completed_items=[(1, "Item 1 - scaffold")],
            is_complete=True,
        )
        assert data.project_type == "Python"
        assert data.init_time == t
        assert len(data.sessions) == 1
        assert data.completed_items[0] == (1, "Item 1 - scaffold")
        assert data.is_complete is True

    def test_lists_are_mutable_per_instance(self) -> None:
        d1 = ProgressData()
        d2 = ProgressData()
        d1.sessions.append(ts())
        assert len(d2.sessions) == 0


class TestSessionError:
    def test_construction(self) -> None:
        err = SessionError(
            file="build_iter_1.log",
            line_num=42,
            error_type="ToolError",
            message="Command failed with exit code 1",
        )
        assert err.file == "build_iter_1.log"
        assert err.line_num == 42
        assert err.error_type == "ToolError"
        assert err.is_recovery is False

    def test_recovery_flag(self) -> None:
        err = SessionError(file="recovery_1.log", line_num=1, error_type="ToolError", message="err", is_recovery=True)
        assert err.is_recovery is True


class TestCostBreakdown:
    def test_defaults(self) -> None:
        bd = CostBreakdown()
        assert bd.total_cost == Decimal("0")
        assert bd.total_iterations == 0
        assert bd.by_phase == {}
        assert bd.by_model == {}
        assert bd.by_item == {}
        assert bd.timeline == []

    def test_decimal_values(self) -> None:
        bd = CostBreakdown(
            by_phase={"build": Decimal("1.5"), "plan": Decimal("0.5")},
            total_cost=Decimal("2.0"),
            total_iterations=5,
        )
        assert isinstance(bd.by_phase["build"], Decimal)
        assert isinstance(bd.total_cost, Decimal)
        assert bd.total_iterations == 5

    def test_by_item_uses_int_keys(self) -> None:
        bd = CostBreakdown(by_item={1: Decimal("0.1"), 2: Decimal("0.2")})
        assert isinstance(list(bd.by_item.keys())[0], int)


class TestTokenAnalysis:
    def test_defaults(self) -> None:
        ta = TokenAnalysis()
        assert ta.total_input == 0
        assert ta.total_output == 0
        assert ta.io_ratio == 0.0
        assert ta.by_phase == {}
        assert ta.by_model == {}
        assert ta.escalations == []
        assert ta.anomalies == []

    def test_construction(self) -> None:
        ta = TokenAnalysis(
            total_input=10000,
            total_output=5000,
            io_ratio=0.5,
            by_phase={"build": PhaseTokenData(input_tokens=8000, output_tokens=4000, count=5)},
        )
        assert ta.total_input == 10000
        assert ta.io_ratio == 0.5
        assert ta.by_phase["build"].count == 5


class TestFailurePatterns:
    def test_defaults(self) -> None:
        fp = FailurePatterns()
        assert fp.stuck_events == []
        assert fp.circuit_breakers == []
        assert fp.build_failure_rate == 0.0
        assert fp.error_categories == {}
        assert fp.recovery_times == {}

    def test_construction(self) -> None:
        fp = FailurePatterns(
            stuck_events=[StuckEvent(item=5, start_iteration=5, count=3)],
            build_failure_rate=0.375,
            recovery_times={5: 4},
        )
        assert len(fp.stuck_events) == 1
        assert fp.stuck_events[0].item == 5
        assert fp.build_failure_rate == pytest.approx(0.375)
        assert fp.recovery_times[5] == 4


class TestAnalysisResult:
    def test_defaults(self) -> None:
        ar = AnalysisResult()
        assert isinstance(ar.project, ProgressData)
        assert isinstance(ar.cost_breakdown, CostBreakdown)
        assert isinstance(ar.token_analysis, TokenAnalysis)
        assert isinstance(ar.failure_patterns, FailurePatterns)
        assert ar.timeline == []
        assert ar.summary == {}

    def test_nested_defaults_are_independent(self) -> None:
        ar1 = AnalysisResult()
        ar2 = AnalysisResult()
        ar1.cost_breakdown.by_phase["build"] = Decimal("1.0")
        assert "build" not in ar2.cost_breakdown.by_phase


class TestHelperDataclasses:
    def test_phase_token_data(self) -> None:
        ptd = PhaseTokenData(input_tokens=100, output_tokens=200, count=3)
        assert ptd.input_tokens == 100
        assert ptd.count == 3

    def test_model_token_data(self) -> None:
        mtd = ModelTokenData(input_tokens=500, output_tokens=300, count=2)
        assert mtd.output_tokens == 300

    def test_escalation_event(self) -> None:
        ev = EscalationEvent(item=3, iteration=5, from_model="sonnet", to_model="opus")
        assert ev.from_model == "sonnet"
        assert ev.to_model == "opus"

    def test_anomaly_entry(self) -> None:
        a = AnomalyEntry(phase="build", iteration=5, actual_tokens=35897, threshold=15000.0)
        assert a.actual_tokens > a.threshold

    def test_stuck_event(self) -> None:
        s = StuckEvent(item=5, start_iteration=5, count=3)
        assert s.item == 5
        assert s.count == 3

    def test_circuit_breaker_event(self) -> None:
        cbe = CircuitBreakerEvent(timestamp=ts(), message="Stuck 3 iterations, phase=build", metadata={"phase": "build"})
        assert "Stuck" in cbe.message
        assert cbe.metadata["phase"] == "build"

    def test_project_summary_row(self) -> None:
        row = ProjectSummaryRow(
            project_name="word-counter",
            total_cost=Decimal("3.059"),
            total_iterations=11,
            duration_minutes=45.0,
            model_split={"opus": 0.6, "sonnet": 0.4},
            stuck_count=1,
        )
        assert isinstance(row.total_cost, Decimal)
        assert row.stuck_count == 1

    def test_efficiency_entry(self) -> None:
        ee = EfficiencyEntry(project_name="word-counter", cost_per_iteration=Decimal("0.278"))
        assert isinstance(ee.cost_per_iteration, Decimal)
