"""Tests for the compare command."""

import json
from pathlib import Path

import pytest

from prompt_vc.commands.bind import bind
from prompt_vc.commands.compare import (
    NoBenchmarksError,
    NotInitializedError,
    VersionNotFoundError,
    compare,
)


def _write_result(tmp_path: Path, filename: str, data: dict) -> Path:
    result_file = tmp_path / filename
    result_file.write_text(json.dumps(data))
    return result_file


WORD_COUNTER_V1 = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T10:00:00+09:00",
    "success": True,
    "test_pass_rate": 0.95,
    "total_tests": 144,
}

WORD_COUNTER_V2 = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T11:00:00+09:00",
    "success": True,
    "test_pass_rate": 1.0,
    "total_tests": 144,
}

MATH_SOLVER_V1 = {
    "benchmark": "math-solver",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T10:30:00+09:00",
    "success": False,
    "test_pass_rate": 0.80,
    "total_tests": 50,
}

MATH_SOLVER_V2 = {
    "benchmark": "math-solver",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T11:30:00+09:00",
    "success": True,
    "test_pass_rate": 0.88,
    "total_tests": 50,
}


def test_compare_shows_version_header(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() output includes the version comparison header."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    assert "v1 vs v2" in output


def test_compare_shows_benchmark_name(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() output includes the benchmark name."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    assert "word-counter" in output


def test_compare_shows_metric_names(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() output includes metric names from the bindings."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    assert "test_pass_rate" in output
    assert "total_tests" in output


def test_compare_shows_numeric_delta(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() shows a positive delta for improved numeric metrics."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    # test_pass_rate improved from 0.95 to 1.00: delta should be positive
    assert "+" in output


def test_compare_shows_zero_delta_for_unchanged(
    two_snapshot_repo: Path, tmp_path: Path
) -> None:
    """compare() shows 0 delta when a metric is identical between versions."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    # total_tests is the same (144) → delta = 0
    assert "+0" in output


def test_compare_shows_winner_line(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() output includes a Winner line when numeric metrics exist."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    assert "Winner:" in output
    assert "v2" in output


def test_compare_key_change_includes_v2_message(
    two_snapshot_repo: Path, tmp_path: Path
) -> None:
    """compare() includes the v2 snapshot message as Key Change."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    # two_snapshot_repo fixture uses "second snapshot" as v2 message
    assert "Key Change:" in output
    assert "second snapshot" in output


def test_compare_benchmark_filter(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() with benchmark filter shows only the requested benchmark."""
    r1a = _write_result(tmp_path, "r1a.json", WORD_COUNTER_V1)
    r1b = _write_result(tmp_path, "r1b.json", MATH_SOLVER_V1)
    r2a = _write_result(tmp_path, "r2a.json", WORD_COUNTER_V2)
    r2b = _write_result(tmp_path, "r2b.json", MATH_SOLVER_V2)
    bind(two_snapshot_repo, "v1", r1a)
    bind(two_snapshot_repo, "v1", r1b)
    bind(two_snapshot_repo, "v2", r2a)
    bind(two_snapshot_repo, "v2", r2b)

    output = compare(two_snapshot_repo, "v1", "v2", benchmark="word-counter")
    assert "word-counter" in output
    assert "math-solver" not in output


def test_compare_benchmark_filter_not_common_raises(
    two_snapshot_repo: Path, tmp_path: Path
) -> None:
    """compare() raises NoBenchmarksError if filtered benchmark is not in both versions."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", MATH_SOLVER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    with pytest.raises(NoBenchmarksError):
        compare(two_snapshot_repo, "v1", "v2", benchmark="word-counter")


def test_compare_no_common_benchmarks_raises(
    two_snapshot_repo: Path, tmp_path: Path
) -> None:
    """compare() raises NoBenchmarksError when versions share no benchmarks."""
    r1 = _write_result(tmp_path, "r1.json", WORD_COUNTER_V1)
    r2 = _write_result(tmp_path, "r2.json", MATH_SOLVER_V2)
    bind(two_snapshot_repo, "v1", r1)
    bind(two_snapshot_repo, "v2", r2)

    with pytest.raises(NoBenchmarksError):
        compare(two_snapshot_repo, "v1", "v2")


def test_compare_no_bindings_raises(two_snapshot_repo: Path) -> None:
    """compare() raises NoBenchmarksError when neither version has any bindings."""
    with pytest.raises(NoBenchmarksError):
        compare(two_snapshot_repo, "v1", "v2")


def test_compare_uses_latest_run(two_snapshot_repo: Path, tmp_path: Path) -> None:
    """compare() uses the latest run number when multiple runs exist for a version."""
    # v1 run1: test_pass_rate = 0.50 (stale)
    # v1 run2: test_pass_rate = 0.95 (latest — should be used)
    r1_old = _write_result(tmp_path, "r1_old.json", {**WORD_COUNTER_V1, "test_pass_rate": 0.50})
    r1_new = _write_result(tmp_path, "r1_new.json", {**WORD_COUNTER_V1, "test_pass_rate": 0.95})
    r2 = _write_result(tmp_path, "r2.json", WORD_COUNTER_V2)

    bind(two_snapshot_repo, "v1", r1_old)  # run1
    bind(two_snapshot_repo, "v1", r1_new)  # run2
    bind(two_snapshot_repo, "v2", r2)

    output = compare(two_snapshot_repo, "v1", "v2")
    # Latest v1 run has 0.95; v2 has 1.00 → delta = +0.05
    # Stale run (0.50) would give delta +0.50 — verify the smaller delta is used
    assert "0.9500" in output  # latest v1 value shown
    assert "0.5000" not in output  # stale v1 value NOT shown


def test_compare_multiple_benchmarks_shown(
    two_snapshot_repo: Path, tmp_path: Path
) -> None:
    """compare() shows all common benchmarks when no filter is applied."""
    r1a = _write_result(tmp_path, "r1a.json", WORD_COUNTER_V1)
    r1b = _write_result(tmp_path, "r1b.json", MATH_SOLVER_V1)
    r2a = _write_result(tmp_path, "r2a.json", WORD_COUNTER_V2)
    r2b = _write_result(tmp_path, "r2b.json", MATH_SOLVER_V2)
    bind(two_snapshot_repo, "v1", r1a)
    bind(two_snapshot_repo, "v1", r1b)
    bind(two_snapshot_repo, "v2", r2a)
    bind(two_snapshot_repo, "v2", r2b)

    output = compare(two_snapshot_repo, "v1", "v2")
    assert "word-counter" in output
    assert "math-solver" in output


def test_compare_version_not_found_v1(two_snapshot_repo: Path) -> None:
    """compare() raises VersionNotFoundError for a nonexistent first version."""
    with pytest.raises(VersionNotFoundError):
        compare(two_snapshot_repo, "v99", "v2")


def test_compare_version_not_found_v2(two_snapshot_repo: Path) -> None:
    """compare() raises VersionNotFoundError for a nonexistent second version."""
    with pytest.raises(VersionNotFoundError):
        compare(two_snapshot_repo, "v1", "v99")


def test_compare_not_initialized(tmp_path: Path) -> None:
    """compare() raises NotInitializedError when .prompt-vc/ does not exist."""
    with pytest.raises(NotInitializedError):
        compare(tmp_path, "v1", "v2")
