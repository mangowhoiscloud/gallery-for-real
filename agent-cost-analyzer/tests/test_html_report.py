"""Tests for HTML dashboard report generator (Item 13)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from agent_cost_analyzer.models import (
    AnomalyEntry,
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
from agent_cost_analyzer.report.html import generate_html_report, generate_comparison_html


# ---------------------------------------------------------------------------
# Helpers / fixtures
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
        by_phase={
            "build": PhaseTokenData(input_tokens=8000, output_tokens=4000, count=3),
            "socratic": PhaseTokenData(input_tokens=2000, output_tokens=1000, count=2),
        },
        by_model={
            "opus": ModelTokenData(input_tokens=6000, output_tokens=3000, count=2),
            "sonnet": ModelTokenData(input_tokens=4000, output_tokens=2000, count=3),
        },
        escalations=[EscalationEvent(item=2, iteration=3, from_model="sonnet", to_model="opus")],
        anomalies=[AnomalyEntry(phase="build", iteration=5, actual_tokens=50000, threshold=20000.0)],
    )
    failures = FailurePatterns(
        stuck_events=[StuckEvent(item=2, start_iteration=3, count=2)],
        circuit_breakers=[
            CircuitBreakerEvent(timestamp=_TS, message="Stuck 2 iterations", metadata={"phase": "build"})
        ],
        build_failure_rate=0.25,
        error_categories={"tool_error": 3},
        recovery_times={2: 3},
    )
    progress = ProgressData(
        project_type="Python",
        init_time=_TS,
        sessions=[_TS],
        completed_items=[(1, "first"), (2, "second")],
        is_complete=True,
    )
    return AnalysisResult(
        project=progress,
        summary={
            "total_cost": Decimal("1.73"),
            "total_iterations": 5,
            "avg_iteration_cost": Decimal("0.346"),
        },
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
                total_cost=Decimal("1.00"),
                total_iterations=4,
                duration_minutes=30.0,
                model_split={"opus": 0.5, "sonnet": 0.5},
                stuck_count=0,
            ),
            ProjectSummaryRow(
                project_name="proj-b",
                total_cost=Decimal("2.00"),
                total_iterations=8,
                duration_minutes=60.0,
                model_split={"opus": 0.25, "sonnet": 0.75},
                stuck_count=1,
            ),
        ],
        efficiency_ranking=[
            EfficiencyEntry(project_name="proj-a", cost_per_iteration=Decimal("0.25")),
            EfficiencyEntry(project_name="proj-b", cost_per_iteration=Decimal("0.25")),
        ],
        stack_comparison={"Python": {"avg_cost": 1.5, "count": 2}},
        cost_comparison=[
            {"project": "proj-a", "build": 0.8, "socratic": 0.2},
            {"project": "proj-b", "build": 1.5, "socratic": 0.5},
        ],
    )


# ---------------------------------------------------------------------------
# Tests for generate_html_report
# ---------------------------------------------------------------------------


def test_html_report_creates_file(tmp_path: Path) -> None:
    result = _make_analysis()
    out = generate_html_report(result, tmp_path)
    assert out == tmp_path / "report.html"
    assert out.exists()


def test_html_report_creates_output_dir(tmp_path: Path) -> None:
    result = _make_analysis()
    outdir = tmp_path / "new_dir" / "nested"
    generate_html_report(result, outdir)
    assert (outdir / "report.html").exists()


def test_html_report_returns_path(tmp_path: Path) -> None:
    result = _make_analysis()
    out = generate_html_report(result, tmp_path)
    assert isinstance(out, Path)
    assert out.name == "report.html"


def test_html_report_has_doctype(tmp_path: Path) -> None:
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    assert "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower()


def test_html_report_has_style_tag(tmp_path: Path) -> None:
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    assert "<style>" in html


def test_html_report_single_external_script(tmp_path: Path) -> None:
    """Exactly one external <script src=...> pointing to Chart.js CDN."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    external_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    assert len(external_srcs) == 1
    assert "chart.js" in external_srcs[0].lower() or "cdn.jsdelivr.net" in external_srcs[0]


def test_html_report_no_external_css(tmp_path: Path) -> None:
    """No <link rel='stylesheet' href='...'> pointing to external files."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    links = re.findall(r'<link[^>]+rel=["\']stylesheet["\'][^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
    # Allow empty list or only CDN links, but no local file references
    for href in links:
        assert href.startswith("http"), f"Local CSS reference found: {href}"


def test_html_report_has_canvas_elements(tmp_path: Path) -> None:
    """Must have at least 3 chart canvas elements."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    canvases = re.findall(r"<canvas\b", html, re.IGNORECASE)
    assert len(canvases) >= 3


def test_html_report_embeds_json_data(tmp_path: Path) -> None:
    """Analysis data is embedded as JSON in a <script> tag."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    # Should contain a script block with JSON data
    assert "const analysisData" in html or "analysisData" in html
    # Verify the embedded JSON is parseable by extracting it
    match = re.search(r"const analysisData\s*=\s*(\{.*?\});", html, re.DOTALL)
    assert match is not None, "analysisData JSON not found in HTML"
    data = json.loads(match.group(1))
    assert isinstance(data, dict)


def test_html_report_has_summary_cards(tmp_path: Path) -> None:
    """Total cost and iteration count appear in the HTML."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    assert "1.73" in html  # total cost
    assert "5" in html     # total iterations


def test_html_report_has_phase_labels(tmp_path: Path) -> None:
    """Phase names from cost breakdown appear in HTML."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    assert "build" in html
    assert "socratic" in html


def test_html_report_decimal_serialized_as_float(tmp_path: Path) -> None:
    """Decimal values in embedded JSON must be numbers, not strings."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    match = re.search(r"const analysisData\s*=\s*(\{.*?\});", html, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))
    # total_cost should be a float/int in JSON, not a string
    total = data.get("total_cost") or data.get("summary", {}).get("total_cost")
    assert total is not None
    assert isinstance(total, (int, float))


def test_html_report_failure_patterns_present(tmp_path: Path) -> None:
    """Failure patterns section or data appears in HTML."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    # Either a heading or data about stuck events should appear
    assert "stuck" in html.lower() or "failure" in html.lower() or "circuit" in html.lower()


def test_html_report_no_local_file_references(tmp_path: Path) -> None:
    """No references to local .css or .js files."""
    result = _make_analysis()
    html = generate_html_report(result, tmp_path).read_text()
    # Look for script src that does NOT start with http
    script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    for src in script_srcs:
        assert src.startswith("http"), f"Local script reference found: {src}"


def test_html_report_empty_analysis(tmp_path: Path) -> None:
    """Empty AnalysisResult generates valid HTML without crashing."""
    result = AnalysisResult()
    out = generate_html_report(result, tmp_path)
    html = out.read_text()
    assert "<html" in html.lower()


# ---------------------------------------------------------------------------
# Tests for generate_comparison_html
# ---------------------------------------------------------------------------


def test_comparison_html_creates_file(tmp_path: Path) -> None:
    comp = _make_comparison()
    out = generate_comparison_html(comp, tmp_path)
    assert out == tmp_path / "comparison.html"
    assert out.exists()


def test_comparison_html_creates_output_dir(tmp_path: Path) -> None:
    comp = _make_comparison()
    outdir = tmp_path / "compare_out"
    generate_comparison_html(comp, outdir)
    assert (outdir / "comparison.html").exists()


def test_comparison_html_has_project_names(tmp_path: Path) -> None:
    comp = _make_comparison()
    html = generate_comparison_html(comp, tmp_path).read_text()
    assert "proj-a" in html
    assert "proj-b" in html


def test_comparison_html_single_cdn_reference(tmp_path: Path) -> None:
    comp = _make_comparison()
    html = generate_comparison_html(comp, tmp_path).read_text()
    external_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    assert len(external_srcs) == 1
    assert "chart.js" in external_srcs[0].lower() or "cdn.jsdelivr.net" in external_srcs[0]


def test_comparison_html_has_canvas(tmp_path: Path) -> None:
    comp = _make_comparison()
    html = generate_comparison_html(comp, tmp_path).read_text()
    canvases = re.findall(r"<canvas\b", html, re.IGNORECASE)
    assert len(canvases) >= 1


def test_comparison_html_embeds_data(tmp_path: Path) -> None:
    comp = _make_comparison()
    html = generate_comparison_html(comp, tmp_path).read_text()
    assert "comparisonData" in html or "comparison" in html.lower()
