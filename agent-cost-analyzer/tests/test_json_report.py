"""Tests for JSON report generator (Item 11)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from agent_cost_analyzer.models import (
    AnalysisResult,
    AnomalyEntry,
    CircuitBreakerEvent,
    ComparisonResult,
    CostBreakdown,
    EfficiencyEntry,
    EscalationEvent,
    FailurePatterns,
    ModelTokenData,
    PhaseTokenData,
    ProgressData,
    ProjectSummaryRow,
    StuckEvent,
    TokenAnalysis,
)
from agent_cost_analyzer.report.json_report import (
    generate_comparison_json,
    generate_json_report,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 3, 24, 10, 0, 0, tzinfo=timezone.utc)
_TS2 = datetime(2026, 3, 24, 11, 0, 0, tzinfo=timezone.utc)


def _make_analysis() -> AnalysisResult:
    cost = CostBreakdown(
        by_phase={"build": Decimal("1.23"), "socratic": Decimal("0.50")},
        by_model={"opus": Decimal("1.00"), "sonnet": Decimal("0.73")},
        by_item={1: Decimal("0.50"), 2: Decimal("0.73")},
        timeline=[(_TS, Decimal("0.50")), (_TS2, Decimal("1.73"))],
        total_cost=Decimal("1.73"),
        total_iterations=5,
    )
    tokens = TokenAnalysis(
        total_input=10000,
        total_output=5000,
        io_ratio=0.5,
        by_phase={"build": PhaseTokenData(input_tokens=8000, output_tokens=4000, count=3)},
        by_model={"opus": ModelTokenData(input_tokens=6000, output_tokens=3000, count=2)},
        escalations=[EscalationEvent(item=2, iteration=3, from_model="sonnet", to_model="opus")],
        anomalies=[AnomalyEntry(phase="build", iteration=5, actual_tokens=50000, threshold=20000.0)],
    )
    failures = FailurePatterns(
        stuck_events=[StuckEvent(item=3, start_iteration=5, count=3)],
        circuit_breakers=[
            CircuitBreakerEvent(timestamp=_TS, message="Stuck 3 iterations", metadata={"phase": "build"})
        ],
        build_failure_rate=0.375,
        error_categories={"AssertionError": 2},
        recovery_times={3: 4},
    )
    progress = ProgressData(
        project_type="Python",
        init_time=_TS,
        sessions=[_TS, _TS2],
        completed_items=[(1, "scaffolding"), (2, "parser")],
        is_complete=True,
    )
    return AnalysisResult(
        project=progress,
        summary={"total_cost": Decimal("1.73"), "total_iterations": 5},
        cost_breakdown=cost,
        token_analysis=tokens,
        failure_patterns=failures,
        timeline=[(_TS, Decimal("0.50")), (_TS2, Decimal("1.73"))],
    )


def _make_comparison() -> ComparisonResult:
    return ComparisonResult(
        summary_table=[
            ProjectSummaryRow(
                project_name="proj-a",
                total_cost=Decimal("1.73"),
                total_iterations=5,
                duration_minutes=60.0,
                model_split={"opus": 57.8, "sonnet": 42.2},
                stuck_count=1,
            ),
            ProjectSummaryRow(
                project_name="proj-b",
                total_cost=Decimal("2.50"),
                total_iterations=8,
                duration_minutes=90.0,
                model_split={"opus": 40.0, "sonnet": 60.0},
                stuck_count=0,
            ),
        ],
        efficiency_ranking=[
            EfficiencyEntry(project_name="proj-a", cost_per_iteration=Decimal("0.346")),
            EfficiencyEntry(project_name="proj-b", cost_per_iteration=Decimal("0.3125")),
        ],
        stack_comparison={"Python": {"avg_total_cost": Decimal("2.115"), "project_count": 2, "project_names": ["proj-a", "proj-b"], "avg_iterations": 7, "avg_duration_minutes": 75.0, "avg_stuck_count": 0.5}},
        cost_comparison=[{"project": "proj-a", "build": 1.23}, {"project": "proj-b", "build": 2.10}],
    )


# ---------------------------------------------------------------------------
# generate_json_report tests
# ---------------------------------------------------------------------------


def test_generates_report_json_file(tmp_path: Path) -> None:
    result = _make_analysis()
    out = generate_json_report(result, tmp_path / "report")
    assert out.name == "report.json"
    assert out.exists()


def test_creates_output_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "new" / "nested" / "dir"
    assert not out_dir.exists()
    generate_json_report(_make_analysis(), out_dir)
    assert out_dir.exists()


def test_output_is_valid_json(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_top_level_keys_present(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    for key in ("project", "summary", "cost_breakdown", "token_analysis", "failure_patterns", "timeline"):
        assert key in data, f"Missing top-level key: {key}"


def test_decimal_serialized_as_float(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    # total_cost in cost_breakdown should be float
    assert isinstance(data["cost_breakdown"]["total_cost"], float)
    assert abs(data["cost_breakdown"]["total_cost"] - 1.73) < 1e-6


def test_datetime_serialized_as_iso_string(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    # project.init_time should be an ISO string
    assert isinstance(data["project"]["init_time"], str)
    assert "2026" in data["project"]["init_time"]


def test_cost_breakdown_by_phase(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    by_phase = data["cost_breakdown"]["by_phase"]
    assert "build" in by_phase
    assert abs(by_phase["build"] - 1.23) < 1e-6


def test_cost_breakdown_by_model(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    by_model = data["cost_breakdown"]["by_model"]
    assert "opus" in by_model
    assert abs(by_model["opus"] - 1.00) < 1e-6


def test_cost_breakdown_by_item(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    # item keys are integers from dict (JSON keys are always strings)
    by_item = data["cost_breakdown"]["by_item"]
    # Keys may be int or string depending on serialization
    keys = {int(k) for k in by_item.keys()}
    assert 1 in keys
    assert 2 in keys


def test_token_analysis_totals(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    ta = data["token_analysis"]
    assert ta["total_input"] == 10000
    assert ta["total_output"] == 5000
    assert abs(ta["io_ratio"] - 0.5) < 1e-9


def test_token_analysis_by_phase(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    by_phase = data["token_analysis"]["by_phase"]
    assert "build" in by_phase
    assert by_phase["build"]["input_tokens"] == 8000


def test_token_analysis_escalations(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    escalations = data["token_analysis"]["escalations"]
    assert len(escalations) == 1
    assert escalations[0]["from_model"] == "sonnet"
    assert escalations[0]["to_model"] == "opus"


def test_token_analysis_anomalies(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    anomalies = data["token_analysis"]["anomalies"]
    assert len(anomalies) == 1
    assert anomalies[0]["phase"] == "build"
    assert anomalies[0]["actual_tokens"] == 50000


def test_failure_patterns_stuck_events(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    stuck = data["failure_patterns"]["stuck_events"]
    assert len(stuck) == 1
    assert stuck[0]["item"] == 3
    assert stuck[0]["count"] == 3


def test_failure_patterns_build_failure_rate(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    assert abs(data["failure_patterns"]["build_failure_rate"] - 0.375) < 1e-9


def test_failure_patterns_error_categories(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    cats = data["failure_patterns"]["error_categories"]
    assert cats["AssertionError"] == 2


def test_timeline_entries(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    timeline = data["timeline"]
    assert len(timeline) == 2
    assert "timestamp" in timeline[0]
    assert "cumulative" in timeline[0]
    assert isinstance(timeline[0]["cumulative"], float)


def test_circuit_breakers_in_failure_patterns(tmp_path: Path) -> None:
    out = generate_json_report(_make_analysis(), tmp_path)
    data = json.loads(out.read_text())
    cbs = data["failure_patterns"]["circuit_breakers"]
    assert len(cbs) == 1
    assert cbs[0]["message"] == "Stuck 3 iterations"


# ---------------------------------------------------------------------------
# generate_comparison_json tests
# ---------------------------------------------------------------------------


def test_generates_comparison_json_file(tmp_path: Path) -> None:
    result = _make_comparison()
    out = generate_comparison_json(result, tmp_path / "cmp")
    assert out.name == "comparison.json"
    assert out.exists()


def test_comparison_creates_output_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "cmp_out"
    assert not out_dir.exists()
    generate_comparison_json(_make_comparison(), out_dir)
    assert out_dir.exists()


def test_comparison_output_is_valid_json(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    assert isinstance(data, dict)


def test_comparison_top_level_keys(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    for key in ("summary_table", "efficiency_ranking", "stack_comparison", "cost_comparison"):
        assert key in data, f"Missing key: {key}"


def test_comparison_summary_table_length(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    assert len(data["summary_table"]) == 2


def test_comparison_decimal_as_float(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    row = data["summary_table"][0]
    assert isinstance(row["total_cost"], float)
    assert abs(row["total_cost"] - 1.73) < 1e-6


def test_comparison_efficiency_ranking(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    ranking = data["efficiency_ranking"]
    assert len(ranking) == 2
    assert ranking[0]["project_name"] == "proj-a"


def test_comparison_stack_comparison(tmp_path: Path) -> None:
    out = generate_comparison_json(_make_comparison(), tmp_path)
    data = json.loads(out.read_text())
    assert "Python" in data["stack_comparison"]
