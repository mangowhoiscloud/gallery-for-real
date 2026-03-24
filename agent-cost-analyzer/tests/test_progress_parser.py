"""Tests for progress.txt parser (Item 5)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from agent_cost_analyzer.parser.progress import parse_progress
from agent_cost_analyzer.models import ProgressData


# ---------------------------------------------------------------------------
# Fixture parsing
# ---------------------------------------------------------------------------


def test_parse_fixture_returns_progress_data(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    assert isinstance(result, ProgressData)


def test_fixture_init_time(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    assert result.init_time is not None
    assert result.init_time == datetime.fromisoformat("2026-03-19T07:55:00+09:00")


def test_fixture_project_type_normalized(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    # python-uv → "Python"
    assert result.project_type == "Python"


def test_fixture_sessions(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    assert len(result.sessions) == 3
    assert result.sessions[0] == datetime.fromisoformat("2026-03-19T08:00:00+09:00")
    assert result.sessions[1] == datetime.fromisoformat("2026-03-19T12:00:00+09:00")
    assert result.sessions[2] == datetime.fromisoformat("2026-03-19T15:00:00+09:00")


def test_fixture_completed_items(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    assert len(result.completed_items) == 6
    assert result.completed_items[0] == (1, "Project scaffolding and data models")
    assert result.completed_items[1] == (2, "Test fixtures and conftest")
    assert result.completed_items[2] == (3, "Cost log parser")
    assert result.completed_items[3] == (4, "Phase log and metrics log parser")
    assert result.completed_items[4] == (5, "Progress text parser")
    assert result.completed_items[5] == (6, "Session log parser")


def test_fixture_is_complete(progress_path: Path) -> None:
    result = parse_progress(progress_path)
    assert result.is_complete is True


# ---------------------------------------------------------------------------
# Missing file → default ProgressData (no exception)
# ---------------------------------------------------------------------------


def test_missing_file_returns_default(tmp_path: Path) -> None:
    result = parse_progress(tmp_path / "nonexistent.txt")
    assert isinstance(result, ProgressData)
    assert result.project_type == ""
    assert result.init_time is None
    assert result.sessions == []
    assert result.completed_items == []
    assert result.is_complete is False


# ---------------------------------------------------------------------------
# HARNESS_COMPLETE flag
# ---------------------------------------------------------------------------


def test_no_harness_complete_is_false(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("=== Harness initialized: 2026-01-01T00:00:00+00:00 ===\nProject type: python-uv\n")
    result = parse_progress(f)
    assert result.is_complete is False


def test_harness_complete_sets_flag(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("HARNESS_COMPLETE\n")
    result = parse_progress(f)
    assert result.is_complete is True


# ---------------------------------------------------------------------------
# Project type normalization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("python-uv", "Python"),
        ("java-maven", "Java"),
        ("java-gradle", "Java"),
        ("typescript-npm", "TypeScript"),
        ("node-npm", "TypeScript"),
        ("rust-cargo", "rust-cargo"),  # unknown → pass-through
        ("go-modules", "go-modules"),  # unknown → pass-through
    ],
)
def test_project_type_normalization(tmp_path: Path, raw: str, expected: str) -> None:
    f = tmp_path / "progress.txt"
    f.write_text(f"Project type: {raw}\n")
    result = parse_progress(f)
    assert result.project_type == expected


# ---------------------------------------------------------------------------
# Unrecognised lines are silently ignored
# ---------------------------------------------------------------------------


def test_unrecognised_lines_ignored(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text(
        "=== Harness initialized: 2026-01-01T00:00:00+00:00 ===\n"
        "Project type: python-uv\n"
        "\n"
        "Some random log output that should be ignored.\n"
        "Another unrecognised line.\n"
        "HARNESS_COMPLETE\n"
    )
    result = parse_progress(f)
    assert result.project_type == "Python"
    assert result.is_complete is True
    assert result.sessions == []
    assert result.completed_items == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_file(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("")
    result = parse_progress(f)
    assert result == ProgressData()


def test_multiple_completed_items_same_session(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text(
        "=== Harness initialized: 2026-01-01T00:00:00+00:00 ===\n"
        "Project type: node-npm\n"
        "=== Session 2026-01-01T01:00:00+00:00 ===\n"
        "Completed: Item 1 - First task\n"
        "Completed: Item 2 - Second task\n"
        "Completed: Item 10 - Tenth task\n"
    )
    result = parse_progress(f)
    assert result.project_type == "TypeScript"
    assert len(result.completed_items) == 3
    assert result.completed_items[2] == (10, "Tenth task")


def test_completed_items_are_int_not_str(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("Completed: Item 42 - Some task\n")
    result = parse_progress(f)
    assert len(result.completed_items) == 1
    item_num, title = result.completed_items[0]
    assert isinstance(item_num, int)
    assert item_num == 42
    assert title == "Some task"
