"""Tests for the bind command."""

import json
from pathlib import Path

import pytest
import yaml

from prompt_vc.commands.bind import (
    InvalidResultError,
    NotInitializedError,
    VersionNotFoundError,
    bind,
)
from prompt_vc.models import BindingMeta


def _write_result(path: Path, data: dict) -> Path:
    result_file = path / "result.json"
    result_file.write_text(json.dumps(data))
    return result_file


VALID_DATA = {
    "benchmark": "word-counter",
    "agent": "claude-sonnet-4-6",
    "timestamp": "2026-03-24T10:00:00+09:00",
    "success": True,
    "test_pass_rate": 0.95,
    "total_tests": 144,
    "extra_metric": 42.0,
}


def test_bind_returns_binding_meta(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """bind() returns a BindingMeta with fields from the result JSON."""
    meta = bind(snapshot_repo, "v1", fixtures_dir / "valid_result.json")

    assert isinstance(meta, BindingMeta)
    assert meta.version == "v1"
    assert meta.benchmark == "word-counter"
    assert meta.agent == "claude-sonnet-4-6"
    assert meta.timestamp == "2026-03-24T10:00:00+09:00"


def test_bind_metrics_contain_success_and_rate(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """Required metric fields (success, test_pass_rate) appear in metrics dict."""
    meta = bind(snapshot_repo, "v1", fixtures_dir / "valid_result.json")

    assert meta.metrics["success"] is True
    assert meta.metrics["test_pass_rate"] == pytest.approx(0.95)


def test_bind_creates_binding_file(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """bind() writes binding YAML to bindings/v1_run1.yaml."""
    bind(snapshot_repo, "v1", fixtures_dir / "valid_result.json")

    assert (snapshot_repo / ".prompt-vc" / "bindings" / "v1_run1.yaml").exists()


def test_bind_file_content_correct(snapshot_repo: Path, tmp_path: Path) -> None:
    """Binding YAML has correct top-level fields and metrics dict."""
    result_file = _write_result(tmp_path, VALID_DATA)
    bind(snapshot_repo, "v1", result_file)

    raw = yaml.safe_load(
        (snapshot_repo / ".prompt-vc" / "bindings" / "v1_run1.yaml").read_text()
    )
    assert raw["version"] == "v1"
    assert raw["benchmark"] == "word-counter"
    assert raw["agent"] == "claude-sonnet-4-6"
    assert raw["metrics"]["success"] is True
    assert raw["metrics"]["test_pass_rate"] == pytest.approx(0.95)
    assert raw["metrics"]["total_tests"] == 144
    assert raw["metrics"]["extra_metric"] == pytest.approx(42.0)


def test_bind_benchmark_not_in_metrics(snapshot_repo: Path, tmp_path: Path) -> None:
    """benchmark, agent, timestamp are top-level, not duplicated in metrics."""
    result_file = _write_result(tmp_path, VALID_DATA)
    meta = bind(snapshot_repo, "v1", result_file)

    assert "benchmark" not in meta.metrics
    assert "agent" not in meta.metrics
    assert "timestamp" not in meta.metrics


def test_bind_auto_increments_run_id(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """Second bind to same version creates v1_run2.yaml."""
    rf = fixtures_dir / "valid_result.json"
    bind(snapshot_repo, "v1", rf)
    bind(snapshot_repo, "v1", rf)

    bindings_dir = snapshot_repo / ".prompt-vc" / "bindings"
    assert (bindings_dir / "v1_run1.yaml").exists()
    assert (bindings_dir / "v1_run2.yaml").exists()


def test_bind_three_runs_increment_correctly(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """Third bind to same version creates v1_run3.yaml."""
    rf = fixtures_dir / "valid_result.json"
    bind(snapshot_repo, "v1", rf)
    bind(snapshot_repo, "v1", rf)
    bind(snapshot_repo, "v1", rf)

    assert (snapshot_repo / ".prompt-vc" / "bindings" / "v1_run3.yaml").exists()


def test_bind_different_versions_independent(two_snapshot_repo: Path, fixtures_dir: Path) -> None:
    """Binding v1 and v2 each start at run1 independently."""
    rf = fixtures_dir / "valid_result.json"
    bind(two_snapshot_repo, "v1", rf)
    bind(two_snapshot_repo, "v2", rf)

    bindings_dir = two_snapshot_repo / ".prompt-vc" / "bindings"
    assert (bindings_dir / "v1_run1.yaml").exists()
    assert (bindings_dir / "v2_run1.yaml").exists()


def test_bind_optional_metrics_preserved(snapshot_repo: Path, tmp_path: Path) -> None:
    """Optional metrics fields beyond success/test_pass_rate are stored."""
    data = {
        "benchmark": "eval-bench",
        "agent": "claude-opus-4-6",
        "success": False,
        "test_pass_rate": 0.5,
        "total_tests": 20,
        "cost_usd": 1.23,
    }
    meta = bind(snapshot_repo, "v1", _write_result(tmp_path, data))

    assert meta.metrics["total_tests"] == 20
    assert meta.metrics["cost_usd"] == pytest.approx(1.23)


def test_bind_generates_timestamp_when_absent(snapshot_repo: Path, tmp_path: Path) -> None:
    """bind() generates ISO timestamp when result JSON has no timestamp."""
    data = {"benchmark": "bench", "agent": "agent", "success": True, "test_pass_rate": 1.0}
    meta = bind(snapshot_repo, "v1", _write_result(tmp_path, data))

    assert meta.timestamp


def test_bind_missing_benchmark_raises(snapshot_repo: Path, tmp_path: Path) -> None:
    """Missing 'benchmark' raises InvalidResultError."""
    data = {"agent": "a", "success": True, "test_pass_rate": 1.0}
    with pytest.raises(InvalidResultError, match="missing required fields"):
        bind(snapshot_repo, "v1", _write_result(tmp_path, data))


def test_bind_missing_success_raises(snapshot_repo: Path, tmp_path: Path) -> None:
    """Missing 'success' raises InvalidResultError."""
    data = {"benchmark": "b", "agent": "a", "test_pass_rate": 1.0}
    with pytest.raises(InvalidResultError, match="missing required fields"):
        bind(snapshot_repo, "v1", _write_result(tmp_path, data))


def test_bind_missing_test_pass_rate_raises(snapshot_repo: Path, tmp_path: Path) -> None:
    """Missing 'test_pass_rate' raises InvalidResultError."""
    data = {"benchmark": "b", "agent": "a", "success": True}
    with pytest.raises(InvalidResultError, match="missing required fields"):
        bind(snapshot_repo, "v1", _write_result(tmp_path, data))


def test_bind_invalid_json_file_raises(snapshot_repo: Path, tmp_path: Path) -> None:
    """Non-JSON file raises InvalidResultError with 'Invalid JSON' message."""
    bad = tmp_path / "bad.json"
    bad.write_text("not json {{{")
    with pytest.raises(InvalidResultError, match="Invalid JSON"):
        bind(snapshot_repo, "v1", bad)


def test_bind_nonexistent_version_raises(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """bind() raises VersionNotFoundError for a version that doesn't exist."""
    with pytest.raises(VersionNotFoundError, match="v99"):
        bind(snapshot_repo, "v99", fixtures_dir / "valid_result.json")


def test_bind_not_initialized_raises(tmp_path: Path, fixtures_dir: Path) -> None:
    """bind() raises NotInitializedError when .prompt-vc/ does not exist."""
    with pytest.raises(NotInitializedError):
        bind(tmp_path, "v1", fixtures_dir / "valid_result.json")


def test_bind_invalid_result_fixture(snapshot_repo: Path, fixtures_dir: Path) -> None:
    """invalid_result.json fixture correctly triggers missing-required-fields error."""
    with pytest.raises(InvalidResultError, match="missing required fields"):
        bind(snapshot_repo, "v1", fixtures_dir / "invalid_result.json")
