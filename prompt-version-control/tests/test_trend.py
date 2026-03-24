"""Tests for the trend command."""

import json
from pathlib import Path

import pytest

from prompt_vc.commands.bind import bind
from prompt_vc.commands.trend import NotInitializedError, trend


def _write_result(tmp_path: Path, filename: str, data: dict) -> Path:
    result_file = tmp_path / filename
    result_file.write_text(json.dumps(data))
    return result_file


WORD_COUNTER_V1 = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T10:00:00+09:00",
    "success": True,
    "test_pass_rate": 0.80,
    "latency": 1.5,
    "tokens": 100,
}

WORD_COUNTER_V2 = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T11:00:00+09:00",
    "success": True,
    "test_pass_rate": 0.95,
    "latency": 1.2,
    "tokens": 95,
}

WORD_COUNTER_V3 = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T12:00:00+09:00",
    "success": True,
    "test_pass_rate": 1.0,
    "latency": 1.0,
    "tokens": 90,
}

MATH_SOLVER_V2 = {
    "benchmark": "math-solver",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T11:30:00+09:00",
    "success": False,
    "test_pass_rate": 0.60,
    "accuracy": 0.60,
}

MATH_SOLVER_V3 = {
    "benchmark": "math-solver",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T12:30:00+09:00",
    "success": True,
    "test_pass_rate": 0.90,
    "accuracy": 0.90,
}


def test_trend_not_initialized(tmp_path: Path) -> None:
    with pytest.raises(NotInitializedError):
        trend(tmp_path)


def test_trend_no_versions(initialized_repo: Path) -> None:
    result = trend(initialized_repo)
    assert "No versions yet" in result


def test_trend_no_bindings(snapshot_repo: Path) -> None:
    result = trend(snapshot_repo)
    assert "No binding data found" in result


def test_trend_header(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf = _write_result(tmp_path, "r.json", WORD_COUNTER_V1)
    bind(cwd, "v1", rf)

    result = trend(cwd)
    assert "=== Metric Trend ===" in result


def test_trend_benchmark_name(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf = _write_result(tmp_path, "r.json", WORD_COUNTER_V1)
    bind(cwd, "v1", rf)

    result = trend(cwd)
    assert "Benchmark: word-counter" in result


def test_trend_version_columns(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(cwd, "v1", rf1)
    bind(cwd, "v2", rf2)

    result = trend(cwd)
    assert "v1" in result
    assert "v2" in result


def test_trend_metric_rows(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(cwd, "v1", rf1)
    bind(cwd, "v2", rf2)

    result = trend(cwd)
    assert "latency" in result
    assert "tokens" in result


def test_trend_values_shown(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(cwd, "v1", rf1)
    bind(cwd, "v2", rf2)

    result = trend(cwd)
    # v1 latency
    assert "1.5000" in result
    # v2 latency
    assert "1.2000" in result


def test_trend_missing_binding_shows_dash(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """Versions without bindings for a benchmark show '—'."""
    cwd = two_snapshot_repo
    # Only bind v2, not v1
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(cwd, "v2", rf2)

    result = trend(cwd)
    assert "—" in result


def test_trend_multiple_benchmarks(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf_wc = _write_result(tmp_path, "wc.json", WORD_COUNTER_V1)
    rf_ms = _write_result(tmp_path, "ms.json", MATH_SOLVER_V2)
    bind(cwd, "v1", rf_wc)
    bind(cwd, "v2", rf_ms)

    result = trend(cwd)
    assert "Benchmark: math-solver" in result
    assert "Benchmark: word-counter" in result


def test_trend_benchmarks_sorted_alphabetically(two_snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = two_snapshot_repo
    rf_wc = _write_result(tmp_path, "wc.json", WORD_COUNTER_V1)
    rf_ms = _write_result(tmp_path, "ms.json", MATH_SOLVER_V2)
    bind(cwd, "v1", rf_wc)
    bind(cwd, "v2", rf_ms)

    result = trend(cwd)
    math_pos = result.index("math-solver")
    word_pos = result.index("word-counter")
    assert math_pos < word_pos


def test_trend_uses_latest_run(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """When multiple runs exist, trend shows the latest run's values."""
    cwd = two_snapshot_repo
    rf1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)  # latency 1.5
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)  # latency 1.2
    bind(cwd, "v1", rf1)  # run1 — latency 1.5
    bind(cwd, "v1", rf2)  # run2 — latency 1.2 (latest)

    result = trend(cwd)
    # Latest run has latency 1.2000
    assert "1.2000" in result
    # Older run's latency should not appear
    assert "1.5000" not in result


def test_trend_single_version_single_binding(snapshot_repo: Path, tmp_path: Path) -> None:
    cwd = snapshot_repo
    rf = _write_result(tmp_path, "r.json", WORD_COUNTER_V1)
    bind(cwd, "v1", rf)

    result = trend(cwd)
    assert "Benchmark: word-counter" in result
    assert "v1" in result
    assert "1.5000" in result  # latency value


def test_trend_versions_chronological_order(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """Version columns appear left-to-right in chronological order."""
    cwd = two_snapshot_repo
    rf1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    rf2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(cwd, "v1", rf1)
    bind(cwd, "v2", rf2)

    result = trend(cwd)
    # v1 should appear before v2 in the output
    v1_pos = result.index("v1")
    v2_pos = result.index("v2")
    assert v1_pos < v2_pos
