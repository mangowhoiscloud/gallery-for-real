"""Tests for the HTML report generator (Items 13 & 14 — table + SVG charts)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from agent_eval.models import RunResult
from agent_eval.report.html import generate_html_report


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_result(
    agent: str = "agent-a",
    benchmark: str = "bench-1",
    success: bool = True,
    test_total: int = 10,
    test_passed: int = 10,
    test_pass_rate: float = 1.0,
    total_time_seconds: float = 60.0,
    estimated_cost: float = 0.05,
    items_completed: int = 3,
    items_total: int = 5,
    **kwargs,
) -> RunResult:
    return RunResult(
        agent=agent,
        benchmark=benchmark,
        success=success,
        build_success=True,
        test_total=test_total,
        test_passed=test_passed,
        test_pass_rate=test_pass_rate,
        total_iterations=5,
        total_time_seconds=total_time_seconds,
        estimated_cost=estimated_cost,
        items_completed=items_completed,
        items_total=items_total,
        **kwargs,
    )


# ── Tests: HTML generation ────────────────────────────────────────────────────


class TestHtmlGeneration:
    def test_generates_html_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        assert out.exists()

    def test_output_is_not_empty(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        assert out.stat().st_size > 0

    def test_valid_html_doctype(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert content.strip().startswith("<!DOCTYPE html>")

    def test_html_charset_utf8(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "charset" in content.lower()
        assert "utf-8" in content.lower()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "deep" / "report.html"
        generate_html_report([_make_result()], out)
        assert out.exists()

    def test_empty_results_no_crash(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([], out)
        assert out.exists()

    def test_empty_results_no_data_rows(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([], out)
        content = out.read_text(encoding="utf-8")
        assert "No results" in content


# ── Tests: self-contained (no external links) ─────────────────────────────────


class TestSelfContained:
    def test_no_external_css_links(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        # No <link rel="stylesheet" href="http...">
        assert not re.search(r'<link[^>]+href=["\']https?://', content, re.IGNORECASE)

    def test_no_external_js_scripts(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert not re.search(r'<script[^>]+src=["\']https?://', content, re.IGNORECASE)

    def test_no_external_font_imports(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "fonts.googleapis" not in content
        assert "fonts.gstatic" not in content

    def test_inline_css_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "<style>" in content


# ── Tests: comparison table ───────────────────────────────────────────────────


class TestComparisonTable:
    def test_table_element_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "<table" in content
        assert "<thead" in content
        assert "<tbody" in content

    def test_table_headers_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "Agent" in content
        assert "Benchmark" in content
        assert "Pass Rate" in content
        assert "Time" in content
        assert "Cost" in content

    def test_table_row_count_matches_results(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="a", benchmark="b1"),
            _make_result(agent="b", benchmark="b1"),
            _make_result(agent="a", benchmark="b2"),
        ]
        out = tmp_path / "report.html"
        generate_html_report(results, out)
        content = out.read_text(encoding="utf-8")
        # Each result produces one <tr> in <tbody>; count td rows by agent names
        assert content.count(">a<") >= 2  # agent "a" appears in 2 rows
        assert content.count(">b<") >= 1  # agent "b" appears in 1 row

    def test_agent_name_in_table(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(agent="my-agent")], out)
        content = out.read_text(encoding="utf-8")
        assert "my-agent" in content

    def test_benchmark_name_in_table(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(benchmark="my-bench")], out)
        content = out.read_text(encoding="utf-8")
        assert "my-bench" in content

    def test_success_checkmark_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(success=True)], out)
        content = out.read_text(encoding="utf-8")
        assert "✓" in content

    def test_failure_x_mark_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(success=False)], out)
        content = out.read_text(encoding="utf-8")
        assert "✗" in content

    def test_items_fraction_in_table(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(items_completed=4, items_total=7)], out)
        content = out.read_text(encoding="utf-8")
        assert "4" in content and "7" in content

    def test_all_metric_columns_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        for col in ("Tokens In", "Tokens Out", "Iterations", "Items Done", "Stuck", "Circuit"):
            assert col in content, f"Missing column: {col}"


# ── Tests: chart placeholder blocks ──────────────────────────────────────────


class TestChartPlaceholders:
    def test_chart_section_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "chart" in content.lower()

    def test_radar_chart_id_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert 'id="radar-chart"' in content

    def test_bar_chart_id_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert 'id="bar-chart"' in content

    def test_heatmap_id_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert 'id="heatmap"' in content

    def test_placeholder_text_when_no_svg(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "placeholder" in content

    def test_svg_kwargs_render_in_output(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report(
            [_make_result()],
            out,
            radar_svg="<svg id='test-radar'></svg>",
            bar_chart_svg="<svg id='test-bar'></svg>",
            heatmap_svg="<svg id='test-heat'></svg>",
        )
        content = out.read_text(encoding="utf-8")
        assert "test-radar" in content
        assert "test-bar" in content
        assert "test-heat" in content

    def test_svg_not_escaped(self, tmp_path: Path) -> None:
        """SVG passed via kwargs must be rendered as raw HTML, not escaped."""
        out = tmp_path / "report.html"
        generate_html_report(
            [_make_result()],
            out,
            radar_svg="<svg><polygon points='0,0 10,0 10,10'/></svg>",
        )
        content = out.read_text(encoding="utf-8")
        # If escaped, would appear as &lt;svg&gt;
        assert "<svg>" in content or "<svg " in content
        assert "&lt;svg" not in content


# ── Tests: dispatcher ─────────────────────────────────────────────────────────


class TestDispatcher:
    def test_generate_report_dispatches_html(self, tmp_path: Path) -> None:
        from agent_eval.report import generate_report

        out = tmp_path / "report.html"
        generate_report([_make_result()], out, format="html")
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_generate_report_unknown_format_raises(self, tmp_path: Path) -> None:
        from agent_eval.report import generate_report

        with pytest.raises(ValueError, match="html"):
            generate_report([_make_result()], tmp_path / "out", format="csv")

    def test_detailed_metrics_section_present(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(agent="solo", benchmark="bmark")], out)
        content = out.read_text(encoding="utf-8")
        assert "Detailed Metrics" in content
        assert "solo" in content
        assert "bmark" in content

    def test_error_field_shown_in_details(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(error="build collapsed")], out)
        content = out.read_text(encoding="utf-8")
        assert "build collapsed" in content

    def test_phase_times_shown_in_details(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(phase_times={"plan": 10.0, "build": 45.0})], out)
        content = out.read_text(encoding="utf-8")
        assert "plan" in content
        assert "build" in content


# ── Tests: SVG chart helpers (Item 14) ───────────────────────────────────────


class TestSvgCharts:
    # ── _radar_chart_svg ──────────────────────────────────────────────────────

    def test_radar_svg_returns_svg_element(self) -> None:
        from agent_eval.report.html import _radar_chart_svg

        scores = {"agent-a": {"correctness": 1.0, "speed": 0.5, "cost": 0.8, "reliability": 0.9}}
        svg = _radar_chart_svg(scores)
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_radar_svg_empty_scores_returns_empty(self) -> None:
        from agent_eval.report.html import _radar_chart_svg

        assert _radar_chart_svg({}) == ""

    def test_radar_svg_has_polygon_per_agent(self) -> None:
        from agent_eval.report.html import _radar_chart_svg

        scores = {
            "agent-a": {"correctness": 1.0, "speed": 0.5, "cost": 0.8, "reliability": 0.9},
            "agent-b": {"correctness": 0.5, "speed": 1.0, "cost": 0.6, "reliability": 0.7},
        }
        svg = _radar_chart_svg(scores)
        # Grid uses 4 polygons; 2 more for the agents → at least 6 total
        assert svg.count("<polygon") >= 6

    def test_radar_data_polygon_has_4_points(self) -> None:
        """Each agent's data polygon must have exactly 4 coordinate pairs."""
        import re

        from agent_eval.report.html import _radar_chart_svg

        scores = {
            "solo": {"correctness": 0.8, "speed": 0.6, "cost": 0.7, "reliability": 0.9}
        }
        svg = _radar_chart_svg(scores)
        # Data polygons have fill-opacity="0.2"
        data_pts = re.findall(r'<polygon[^>]*fill-opacity="0\.2"[^>]*points="([^"]+)"', svg)
        assert len(data_pts) == 1
        assert len(data_pts[0].strip().split()) == 4

    def test_radar_two_agents_produce_two_data_polygons(self) -> None:
        import re

        from agent_eval.report.html import _radar_chart_svg

        scores = {
            "a": {"correctness": 1.0, "speed": 0.5, "cost": 0.8, "reliability": 0.9},
            "b": {"correctness": 0.5, "speed": 1.0, "cost": 0.6, "reliability": 0.7},
        }
        svg = _radar_chart_svg(scores)
        data_pts = re.findall(r'<polygon[^>]*fill-opacity="0\.2"[^>]*points="([^"]+)"', svg)
        assert len(data_pts) == 2

    def test_radar_auto_generated_in_report(self, tmp_path: Path) -> None:
        """generate_html_report auto-generates the radar SVG when results present."""
        out = tmp_path / "report.html"
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        # Radar is always generated (even for single-agent results)
        assert "<svg" in content

    # ── _stacked_bar_chart_svg ────────────────────────────────────────────────

    def test_bar_svg_returns_svg_with_phase_times(self) -> None:
        from agent_eval.report.html import _stacked_bar_chart_svg

        results = [_make_result(phase_times={"plan": 10.0, "build": 30.0})]
        svg = _stacked_bar_chart_svg(results)
        assert "<svg" in svg
        assert "<rect" in svg

    def test_bar_svg_empty_phase_times_returns_empty(self) -> None:
        from agent_eval.report.html import _stacked_bar_chart_svg

        assert _stacked_bar_chart_svg([_make_result()]) == ""

    def test_bar_svg_empty_results_returns_empty(self) -> None:
        from agent_eval.report.html import _stacked_bar_chart_svg

        assert _stacked_bar_chart_svg([]) == ""

    def test_bar_rect_count_matches_phase_segments(self) -> None:
        """Each non-zero phase-time segment produces one <rect>."""
        import re

        from agent_eval.report.html import _stacked_bar_chart_svg

        results = [
            _make_result(
                agent="a", benchmark="b1",
                phase_times={"plan": 10.0, "build": 20.0, "test": 5.0},
            ),
            _make_result(
                agent="b", benchmark="b1",
                phase_times={"plan": 8.0, "build": 25.0},
            ),
        ]
        svg = _stacked_bar_chart_svg(results)
        # result[0]: 3 phases → 3 rects; result[1]: 2 phases → 2 rects; total 5
        rects = re.findall(r"<rect\b", svg)
        assert len(rects) == 5

    def test_bar_svg_title_elements_have_phase_names(self) -> None:
        from agent_eval.report.html import _stacked_bar_chart_svg

        results = [_make_result(phase_times={"plan": 10.0, "build": 30.0})]
        svg = _stacked_bar_chart_svg(results)
        assert "<title>plan:" in svg
        assert "<title>build:" in svg

    def test_bar_placeholder_shown_when_no_phase_times(self, tmp_path: Path) -> None:
        """Auto-generated bar chart is empty → template renders placeholder."""
        out = tmp_path / "report.html"
        # _make_result() has no phase_times → bar_chart_svg="" → placeholder shown
        generate_html_report([_make_result()], out)
        content = out.read_text(encoding="utf-8")
        assert "placeholder" in content

    # ── _heatmap_svg ──────────────────────────────────────────────────────────

    def test_heatmap_svg_returns_svg_element(self) -> None:
        from agent_eval.report.html import _heatmap_svg

        svg = _heatmap_svg([_make_result(agent="a", benchmark="b1")])
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_heatmap_svg_empty_returns_empty(self) -> None:
        from agent_eval.report.html import _heatmap_svg

        assert _heatmap_svg([]) == ""

    def test_heatmap_cell_count_matches_grid(self) -> None:
        """2 benchmarks × 2 agents = 4 cells (rects)."""
        import re

        from agent_eval.report.html import _heatmap_svg

        results = [
            _make_result(agent="a", benchmark="b1", test_pass_rate=1.0),
            _make_result(agent="b", benchmark="b1", test_pass_rate=0.5),
            _make_result(agent="a", benchmark="b2", test_pass_rate=0.0),
            _make_result(agent="b", benchmark="b2", test_pass_rate=0.8),
        ]
        svg = _heatmap_svg(results)
        rects = re.findall(r"<rect\b", svg)
        assert len(rects) == 4

    def test_heatmap_green_cell_for_full_pass(self) -> None:
        from agent_eval.report.html import _heatmap_svg

        svg = _heatmap_svg([_make_result(test_pass_rate=1.0)])
        assert "#28a745" in svg.lower() or "28a745" in svg

    def test_heatmap_red_cell_for_zero_pass(self) -> None:
        from agent_eval.report.html import _heatmap_svg

        svg = _heatmap_svg([_make_result(test_pass_rate=0.0, success=False)])
        assert "#dc3545" in svg.lower() or "dc3545" in svg

    def test_heatmap_auto_generated_in_report(self, tmp_path: Path) -> None:
        out = tmp_path / "report.html"
        generate_html_report([_make_result(agent="a", benchmark="b1")], out)
        content = out.read_text(encoding="utf-8")
        # heatmap generates at least one <rect>
        assert "<rect" in content
