"""Tests for Markdown report generator (Item 12)."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from agent_cost_analyzer.models import (
    AnalysisResult,
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
from agent_cost_analyzer.report.markdown import (
    generate_comparison_markdown,
    generate_markdown_report,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_TS = datetime(2026, 3, 24, 10, 0, 0, tzinfo=timezone.utc)
_TS2 = datetime(2026, 3, 24, 11, 0, 0, tzinfo=timezone.utc)


def _make_analysis(
    *,
    with_failures: bool = True,
    with_tokens: bool = True,
) -> AnalysisResult:
    cost = CostBreakdown(
        by_phase={"build": Decimal("1.2300"), "socratic": Decimal("0.5000")},
        by_model={"opus": Decimal("1.0000"), "sonnet": Decimal("0.7300")},
        by_item={1: Decimal("0.5000"), 2: Decimal("0.7300")},
        timeline=[(_TS, Decimal("0.50")), (_TS2, Decimal("1.73"))],
        total_cost=Decimal("1.7300"),
        total_iterations=5,
    )
    tokens = TokenAnalysis(
        total_input=10000,
        total_output=5000,
        io_ratio=0.5,
        by_phase={"build": PhaseTokenData(input_tokens=8000, output_tokens=4000, count=3)},
        by_model={"opus": ModelTokenData(input_tokens=6000, output_tokens=3000, count=2)},
        escalations=(
            [EscalationEvent(item=2, iteration=3, from_model="sonnet", to_model="opus")]
            if with_tokens
            else []
        ),
        anomalies=[],
    )
    failures = FailurePatterns(
        stuck_events=(
            [StuckEvent(item=3, start_iteration=5, count=3)] if with_failures else []
        ),
        circuit_breakers=(
            [CircuitBreakerEvent(timestamp=_TS, message="Stuck 3 iterations")]
            if with_failures
            else []
        ),
        build_failure_rate=0.375 if with_failures else 0.0,
        error_categories={},
        recovery_times={},
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
        cost_comparison=[],
    )


# ---------------------------------------------------------------------------
# generate_markdown_report tests
# ---------------------------------------------------------------------------


def test_generates_report_md_file(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path / "report")
    assert out.name == "report.md"
    assert out.exists()


def test_creates_output_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "new" / "nested"
    assert not out_dir.exists()
    generate_markdown_report(_make_analysis(), out_dir)
    assert out_dir.exists()


def test_contains_all_five_sections(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "## Project Summary" in text
    assert "## Cost by Phase" in text
    assert "## Cost by Item" in text
    assert "## Failure Patterns" in text
    assert "## Key Metrics" in text


def test_contains_gfm_table(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    # GFM tables use pipe delimiters and separator rows
    assert "|" in text
    assert "---" in text


def test_monetary_format(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    # Monetary values must use $X.XXXX format
    assert "$1.7300" in text


def test_phase_costs_present(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "build" in text
    assert "socratic" in text
    assert "$1.2300" in text


def test_item_costs_present(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "$0.7300" in text  # item 2 appears in top items


def test_failure_patterns_stuck_event(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(with_failures=True), tmp_path)
    text = out.read_text()
    assert "Stuck" in text
    assert "Item 3" in text


def test_no_failures_message(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(with_failures=False), tmp_path)
    text = out.read_text()
    assert "No failures detected" in text


def test_key_metrics_token_counts(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "10,000" in text  # formatted input tokens
    assert "5,000" in text   # formatted output tokens


def test_key_metrics_io_ratio(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "0.50" in text


def test_key_metrics_escalation_count(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(with_tokens=True), tmp_path)
    text = out.read_text()
    assert "1" in text  # 1 escalation


def test_character_limit_for_typical_data(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert len(text) < 5000


def test_project_type_displayed(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "Python" in text


def test_model_split_in_summary(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "opus" in text or "sonnet" in text


def test_duration_displayed(tmp_path: Path) -> None:
    out = generate_markdown_report(_make_analysis(), tmp_path)
    text = out.read_text()
    assert "min" in text  # duration shown with min unit


def test_empty_analysis_no_crash(tmp_path: Path) -> None:
    empty = AnalysisResult()
    out = generate_markdown_report(empty, tmp_path)
    assert out.exists()
    text = out.read_text()
    assert "## Project Summary" in text


# ---------------------------------------------------------------------------
# generate_comparison_markdown tests
# ---------------------------------------------------------------------------


def test_generates_comparison_md_file(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path / "cmp")
    assert out.name == "comparison.md"
    assert out.exists()


def test_comparison_creates_output_directory(tmp_path: Path) -> None:
    out_dir = tmp_path / "cmp_out"
    assert not out_dir.exists()
    generate_comparison_markdown(_make_comparison(), out_dir)
    assert out_dir.exists()


def test_comparison_contains_summary_section(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path)
    text = out.read_text()
    assert "## Summary" in text
    assert "proj-a" in text
    assert "proj-b" in text


def test_comparison_contains_efficiency_ranking(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path)
    text = out.read_text()
    assert "Efficiency Ranking" in text


def test_comparison_contains_stack_comparison(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path)
    text = out.read_text()
    assert "Stack Comparison" in text
    assert "Python" in text


def test_comparison_monetary_format(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path)
    text = out.read_text()
    assert "$1.7300" in text


def test_comparison_has_gfm_table(tmp_path: Path) -> None:
    out = generate_comparison_markdown(_make_comparison(), tmp_path)
    text = out.read_text()
    assert "|" in text
    assert "---" in text
