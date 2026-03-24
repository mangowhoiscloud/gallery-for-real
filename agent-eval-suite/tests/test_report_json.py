"""Tests for JSON report generation and result discovery."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_eval.models import RunResult
from agent_eval.report import discover_results, generate_report
from agent_eval.report.json_report import generate_json_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    agent: str = "claude",
    benchmark: str = "word-counter",
    success: bool = True,
    test_total: int = 10,
    test_passed: int = 10,
) -> RunResult:
    return RunResult(
        agent=agent,
        benchmark=benchmark,
        success=success,
        build_success=True,
        test_total=test_total,
        test_passed=test_passed,
        test_pass_rate=test_passed / test_total if test_total > 0 else 0.0,
        total_iterations=3,
        total_time_seconds=120.0,
        phase_times={"plan": 10.0, "implement": 100.0, "test": 10.0},
        total_tokens_in=5000,
        total_tokens_out=2000,
        estimated_cost=0.05,
        items_completed=3,
        items_total=3,
        stuck_count=0,
        circuit_breaker_count=0,
        error=None,
    )


# ---------------------------------------------------------------------------
# generate_json_report
# ---------------------------------------------------------------------------


class TestGenerateJsonReport:
    def test_creates_file(self, tmp_path: Path) -> None:
        results = [_make_result()]
        out = tmp_path / "report.json"
        generate_json_report(results, out)
        assert out.exists()

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "deep" / "report.json"
        generate_json_report([_make_result()], out)
        assert out.exists()

    def test_valid_json(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_json_report([_make_result()], out)
        with open(out) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_summary_and_results_keys(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_json_report([_make_result()], out)
        with open(out) as f:
            data = json.load(f)
        assert "summary" in data
        assert "results" in data

    def test_results_count_matches_input(self, tmp_path: Path) -> None:
        results = [_make_result("claude"), _make_result("opus")]
        out = tmp_path / "report.json"
        generate_json_report(results, out)
        with open(out) as f:
            data = json.load(f)
        assert len(data["results"]) == 2

    def test_summary_aggregates_by_benchmark(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="claude", benchmark="bench-a", success=True),
            _make_result(agent="opus", benchmark="bench-a", success=False),
            _make_result(agent="claude", benchmark="bench-b", success=True),
        ]
        out = tmp_path / "report.json"
        generate_json_report(results, out)
        with open(out) as f:
            data = json.load(f)
        summary = data["summary"]
        assert set(summary.keys()) == {"bench-a", "bench-b"}
        assert summary["bench-a"]["total_count"] == 2
        assert summary["bench-a"]["success_count"] == 1
        assert summary["bench-a"]["success_rate"] == pytest.approx(0.5)
        assert summary["bench-b"]["total_count"] == 1
        assert summary["bench-b"]["success_count"] == 1
        assert summary["bench-b"]["success_rate"] == pytest.approx(1.0)

    def test_summary_agents_list(self, tmp_path: Path) -> None:
        results = [
            _make_result(agent="claude", benchmark="bench-a"),
            _make_result(agent="opus", benchmark="bench-a"),
        ]
        out = tmp_path / "report.json"
        generate_json_report(results, out)
        with open(out) as f:
            data = json.load(f)
        agents = data["summary"]["bench-a"]["agents"]
        assert set(agents) == {"claude", "opus"}

    def test_round_trip_run_result(self, tmp_path: Path) -> None:
        original = _make_result()
        out = tmp_path / "report.json"
        generate_json_report([original], out)
        with open(out) as f:
            data = json.load(f)
        restored = RunResult.from_dict(data["results"][0])
        assert restored.agent == original.agent
        assert restored.benchmark == original.benchmark
        assert restored.success == original.success
        assert restored.test_total == original.test_total
        assert restored.test_passed == original.test_passed
        assert restored.test_pass_rate == pytest.approx(original.test_pass_rate)
        assert restored.estimated_cost == pytest.approx(original.estimated_cost)
        assert restored.phase_times == original.phase_times

    def test_empty_results_list(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_json_report([], out)
        with open(out) as f:
            data = json.load(f)
        assert data["results"] == []
        assert data["summary"] == {}

    def test_success_rate_zero_when_all_fail(self, tmp_path: Path) -> None:
        results = [
            _make_result(success=False),
            _make_result(agent="opus", success=False),
        ]
        out = tmp_path / "report.json"
        generate_json_report(results, out)
        with open(out) as f:
            data = json.load(f)
        assert data["summary"]["word-counter"]["success_rate"] == pytest.approx(0.0)

    def test_accepts_str_path(self, tmp_path: Path) -> None:
        out = str(tmp_path / "report.json")
        generate_json_report([_make_result()], out)
        assert Path(out).exists()


# ---------------------------------------------------------------------------
# discover_results
# ---------------------------------------------------------------------------


class TestDiscoverResults:
    def _write_bare_result_json(self, directory: Path, result: RunResult) -> None:
        """Write a bare RunResult dict as result.json."""
        directory.mkdir(parents=True, exist_ok=True)
        with open(directory / "result.json", "w") as f:
            json.dump(result.to_dict(), f)

    def _write_report_result_json(
        self, directory: Path, results: list[RunResult]
    ) -> None:
        """Write a full report JSON (with 'results' key) as result.json."""
        directory.mkdir(parents=True, exist_ok=True)
        generate_json_report(results, directory / "result.json")

    def test_finds_bare_result_json(self, tmp_path: Path) -> None:
        r = _make_result()
        self._write_bare_result_json(tmp_path / "word-counter" / "claude", r)
        found = discover_results(tmp_path)
        assert len(found) == 1
        assert found[0].agent == "claude"

    def test_finds_nested_result_json(self, tmp_path: Path) -> None:
        r1 = _make_result(agent="claude", benchmark="bench-a")
        r2 = _make_result(agent="opus", benchmark="bench-b")
        self._write_bare_result_json(tmp_path / "bench-a" / "claude", r1)
        self._write_bare_result_json(tmp_path / "bench-b" / "opus", r2)
        found = discover_results(tmp_path)
        assert len(found) == 2
        agents = {r.agent for r in found}
        assert agents == {"claude", "opus"}

    def test_empty_directory_returns_empty_list(self, tmp_path: Path) -> None:
        found = discover_results(tmp_path)
        assert found == []

    def test_handles_report_format_result_json(self, tmp_path: Path) -> None:
        """discover_results also handles result.json files in report format."""
        results = [_make_result("claude"), _make_result("opus")]
        self._write_report_result_json(tmp_path / "reports", results)
        found = discover_results(tmp_path)
        assert len(found) == 2

    def test_deserialized_fields_match(self, tmp_path: Path) -> None:
        original = _make_result()
        self._write_bare_result_json(tmp_path / "run", original)
        found = discover_results(tmp_path)
        r = found[0]
        assert r.benchmark == original.benchmark
        assert r.success == original.success
        assert r.test_pass_rate == pytest.approx(original.test_pass_rate)
        assert r.phase_times == original.phase_times

    def test_accepts_str_path(self, tmp_path: Path) -> None:
        r = _make_result()
        self._write_bare_result_json(tmp_path / "run", r)
        found = discover_results(str(tmp_path))
        assert len(found) == 1


# ---------------------------------------------------------------------------
# generate_report dispatcher
# ---------------------------------------------------------------------------


class TestGenerateReport:
    def test_json_format_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_report([_make_result()], out, format="json")
        assert out.exists()

    def test_json_format_valid_json(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_report([_make_result()], out, format="json")
        with open(out) as f:
            data = json.load(f)
        assert "results" in data

    def test_unknown_format_raises_value_error(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unknown format"):
            generate_report([_make_result()], tmp_path / "x.txt", format="csv")

    def test_default_format_is_json(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        generate_report([_make_result()], out)
        assert out.exists()
        with open(out) as f:
            data = json.load(f)
        assert "results" in data
