"""Tests for the Markdown report generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_eval.models import RunResult
from agent_eval.report.markdown import generate_markdown_report, _winner


# ── Fixtures ─────────────────────────────────────────────────────────────────


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


# ── Tests: table generation ───────────────────────────────────────────────────


class TestTableGeneration:
    def test_generates_markdown_file(self, tmp_path: Path) -> None:
        results = [_make_result()]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert out.exists()

    def test_table_header_present(self, tmp_path: Path) -> None:
        results = [_make_result()]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "| Agent |" in content
        assert "| Benchmark |" in content
        assert "| Pass Rate |" in content

    def test_table_has_correct_column_count(self, tmp_path: Path) -> None:
        results = [_make_result()]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        # Find a data row (starts with "| agent-a")
        for line in content.splitlines():
            if line.startswith("| agent-a"):
                # Count pipe characters (N+1 pipes for N columns, but leading/trailing)
                col_count = line.count("|") - 1
                assert col_count == 7  # 7 columns
                break
        else:
            pytest.fail("No data row found in table")

    def test_success_checkmark(self, tmp_path: Path) -> None:
        results = [_make_result(success=True)]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert "✓" in out.read_text()

    def test_failure_x_mark(self, tmp_path: Path) -> None:
        results = [_make_result(success=False)]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert "✗" in out.read_text()

    def test_items_fraction_format(self, tmp_path: Path) -> None:
        results = [_make_result(items_completed=3, items_total=5)]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert "3/5" in out.read_text()

    def test_row_count_matches_results(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="a", benchmark="b1"),
            _make_result(agent="b", benchmark="b1"),
            _make_result(agent="a", benchmark="b2"),
        ]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        # Count data rows: lines starting with "| " that are not header/sep
        data_rows = [
            line for line in content.splitlines()
            if line.startswith("|") and "---" not in line and "Agent" not in line
        ]
        assert len(data_rows) == 3

    def test_empty_results_no_crash(self, tmp_path: Path) -> None:
        out = tmp_path / "report.md"
        generate_markdown_report([], out)
        assert out.exists()

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "deep" / "report.md"
        generate_markdown_report([_make_result()], out)
        assert out.exists()


# ── Tests: winner logic ────────────────────────────────────────────────────────


class TestWinnerLogic:
    def test_winner_highest_pass_rate(self) -> None:
        a = _make_result(agent="a", test_pass_rate=0.5, estimated_cost=0.01)
        b = _make_result(agent="b", test_pass_rate=1.0, estimated_cost=0.10)
        assert _winner([a, b]).agent == "b"

    def test_winner_tiebreak_by_cost(self) -> None:
        a = _make_result(agent="a", test_pass_rate=1.0, estimated_cost=0.20)
        b = _make_result(agent="b", test_pass_rate=1.0, estimated_cost=0.05)
        assert _winner([a, b]).agent == "b"

    def test_winner_single_entry(self) -> None:
        r = _make_result(agent="only")
        assert _winner([r]).agent == "only"

    def test_winner_section_in_output(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="a", benchmark="bench", test_pass_rate=0.5, estimated_cost=0.01),
            _make_result(agent="b", benchmark="bench", test_pass_rate=1.0, estimated_cost=0.10),
        ]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "Winners by Benchmark" in content
        assert "**b**" in content  # winner is bold

    def test_winner_per_benchmark(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="a", benchmark="bench-1", test_pass_rate=1.0, estimated_cost=0.05),
            _make_result(agent="b", benchmark="bench-1", test_pass_rate=0.5, estimated_cost=0.01),
            _make_result(agent="a", benchmark="bench-2", test_pass_rate=0.3, estimated_cost=0.05),
            _make_result(agent="b", benchmark="bench-2", test_pass_rate=0.8, estimated_cost=0.10),
        ]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        # bench-1 winner: a (higher pass rate)
        # bench-2 winner: b (higher pass rate)
        lines = content.splitlines()
        bench1_line = next(ln for ln in lines if "bench-1" in ln and "sole" not in ln and ln.startswith("- "))
        bench2_line = next(ln for ln in lines if "bench-2" in ln and "sole" not in ln and ln.startswith("- "))
        assert "**a**" in bench1_line
        assert "**b**" in bench2_line

    def test_sole_entry_label(self, tmp_path: Path) -> None:
        results = [_make_result(agent="only", benchmark="bench")]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert "sole entry" in out.read_text()


# ── Tests: single result ───────────────────────────────────────────────────────


class TestSingleResult:
    def test_single_result_table(self, tmp_path: Path) -> None:
        results = [_make_result(agent="solo", benchmark="bmark")]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "solo" in content
        assert "bmark" in content

    def test_single_result_detailed_section(self, tmp_path: Path) -> None:
        results = [_make_result(agent="solo", benchmark="bmark")]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "Detailed Metrics" in content
        assert "solo on bmark" in content

    def test_error_field_shown(self, tmp_path: Path) -> None:
        results = [_make_result(error="build failed")]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        assert "build failed" in out.read_text()

    def test_phase_times_shown(self, tmp_path: Path) -> None:
        results = [_make_result(phase_times={"plan": 10.0, "build": 30.0})]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "plan" in content
        assert "build" in content


# ── Tests: multi-benchmark results ────────────────────────────────────────────


class TestMultiBenchmarkResults:
    def test_multiple_benchmarks_all_in_table(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="a", benchmark="bench-1"),
            _make_result(agent="a", benchmark="bench-2"),
            _make_result(agent="b", benchmark="bench-1"),
        ]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "bench-1" in content
        assert "bench-2" in content

    def test_multiple_agents_in_table(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="claude-opus", benchmark="bench"),
            _make_result(agent="claude-sonnet", benchmark="bench"),
        ]
        out = tmp_path / "report.md"
        generate_markdown_report(results, out)
        content = out.read_text()
        assert "claude-opus" in content
        assert "claude-sonnet" in content

    def test_generate_report_dispatches_markdown(self, tmp_path: Path) -> None:
        from agent_eval.report import generate_report
        results = [_make_result()]
        out = tmp_path / "report.md"
        generate_report(results, out, format="markdown")
        assert out.exists()
        assert "# Agent Evaluation Report" in out.read_text()
