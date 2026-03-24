"""Tests for the CLI entry point (Item 14)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from agent_cost_analyzer.cli import (
    _ALL_FORMATS,
    _build_parser,
    _parse_date,
    _parse_formats,
    _run_analyze,
    _run_compare,
    _run_watch,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_project(tmp_path: Path, fixtures_dir: Path) -> Path:
    """Create a minimal project directory with .harness-logs/ populated from fixtures."""
    project_dir = tmp_path / "my_project"
    logs_dir = project_dir / ".harness-logs"
    logs_dir.mkdir(parents=True)
    # Required
    (logs_dir / "cost.log").write_bytes((fixtures_dir / "cost.log").read_bytes())
    # Optional — include them for complete coverage
    (logs_dir / "phase.log").write_bytes((fixtures_dir / "phase.log").read_bytes())
    (logs_dir / "metrics.log").write_bytes((fixtures_dir / "metrics.log").read_bytes())
    (project_dir / "progress.txt").write_bytes(
        (fixtures_dir / "progress.txt").read_bytes()
    )
    return project_dir


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------


def test_parse_date_valid() -> None:
    from datetime import date

    assert _parse_date("2026-03-19") == date(2026, 3, 19)


def test_parse_date_invalid() -> None:
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _parse_date("19-03-2026")


def test_parse_date_invalid_text() -> None:
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        _parse_date("yesterday")


# ---------------------------------------------------------------------------
# _parse_formats
# ---------------------------------------------------------------------------


def test_parse_formats_all() -> None:
    result = _parse_formats("html,json,md")
    assert result == {"html", "json", "md"}


def test_parse_formats_single() -> None:
    assert _parse_formats("json") == {"json"}


def test_parse_formats_unknown() -> None:
    import argparse

    with pytest.raises(argparse.ArgumentTypeError, match="Unknown format"):
        _parse_formats("xml")


def test_parse_formats_mixed_case() -> None:
    assert _parse_formats("HTML,Json,MD") == {"html", "json", "md"}


def test_parse_formats_spaces() -> None:
    assert _parse_formats("html, json") == {"html", "json"}


# ---------------------------------------------------------------------------
# Parser construction
# ---------------------------------------------------------------------------


def test_parser_analyze_requires_project() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["analyze"])
    assert exc_info.value.code != 0


def test_parser_analyze_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args(["analyze", "--project", "/some/path"])
    assert args.output == "./report"
    assert args.after is None
    assert args.before is None
    assert args.format == _ALL_FORMATS


def test_parser_analyze_with_dates() -> None:
    from datetime import date

    parser = _build_parser()
    args = parser.parse_args(
        ["analyze", "--project", "/p", "--after", "2026-03-19", "--before", "2026-03-21"]
    )
    assert args.after == date(2026, 3, 19)
    assert args.before == date(2026, 3, 21)


def test_parser_analyze_format_single() -> None:
    parser = _build_parser()
    args = parser.parse_args(["analyze", "--project", "/p", "--format", "json"])
    assert args.format == {"json"}


def test_parser_compare_requires_projects() -> None:
    parser = _build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["compare"])
    assert exc_info.value.code != 0


def test_parser_compare_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args(["compare", "--projects", "/a,/b"])
    assert args.output == "./report"
    assert args.format == _ALL_FORMATS


def test_parser_watch_no_required_args() -> None:
    """watch should parse with no arguments."""
    parser = _build_parser()
    args = parser.parse_args(["watch"])
    assert args.command == "watch"


def test_parser_watch_with_project() -> None:
    parser = _build_parser()
    args = parser.parse_args(["watch", "--project", "/some/path"])
    assert args.command == "watch"


# ---------------------------------------------------------------------------
# _run_watch
# ---------------------------------------------------------------------------


def test_run_watch_prints_message(capsys: pytest.CaptureFixture) -> None:
    parser = _build_parser()
    args = parser.parse_args(["watch"])
    code = _run_watch(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "not yet implemented" in captured.out


# ---------------------------------------------------------------------------
# _run_analyze
# ---------------------------------------------------------------------------


def test_run_analyze_success_all_formats(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        ["analyze", "--project", str(project_dir), "--output", str(output_dir)]
    )
    code = _run_analyze(args)

    assert code == 0
    assert (output_dir / "report.json").exists()
    assert (output_dir / "report.md").exists()
    assert (output_dir / "report.html").exists()


def test_run_analyze_creates_output_dir(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "nested" / "output"
    assert not output_dir.exists()

    parser = _build_parser()
    args = parser.parse_args(
        ["analyze", "--project", str(project_dir), "--output", str(output_dir)]
    )
    code = _run_analyze(args)

    assert code == 0
    assert output_dir.exists()


def test_run_analyze_missing_cost_log(tmp_path: Path) -> None:
    """Missing cost.log should return exit code 1."""
    project_dir = tmp_path / "empty_project"
    (project_dir / ".harness-logs").mkdir(parents=True)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        ["analyze", "--project", str(project_dir), "--output", str(output_dir)]
    )
    code = _run_analyze(args)

    assert code == 1


def test_run_analyze_format_json_only(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
        ]
    )
    code = _run_analyze(args)

    assert code == 0
    assert (output_dir / "report.json").exists()
    assert not (output_dir / "report.md").exists()
    assert not (output_dir / "report.html").exists()


def test_run_analyze_format_md_only(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "md",
        ]
    )
    code = _run_analyze(args)

    assert code == 0
    assert (output_dir / "report.md").exists()
    assert not (output_dir / "report.json").exists()
    assert not (output_dir / "report.html").exists()


def test_run_analyze_json_content_valid(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    """Generated JSON report should be valid and have expected top-level keys."""
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
        ]
    )
    _run_analyze(args)

    data = json.loads((output_dir / "report.json").read_text())
    assert "project" in data
    assert "summary" in data
    assert "cost_breakdown" in data
    assert "token_analysis" in data
    assert "failure_patterns" in data
    assert "timeline" in data


def test_run_analyze_date_filter(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    """--after/--before should pass through to parse_cost_log."""
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    # Fixture entries span 2026-03-18 UTC through 2026-03-19 UTC.
    # Setting after=2026-03-20 means no entries → total_iterations=0
    args = parser.parse_args(
        [
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
            "--after",
            "2026-03-20",
        ]
    )
    code = _run_analyze(args)
    assert code == 0

    data = json.loads((output_dir / "report.json").read_text())
    assert data["summary"]["total_iterations"] == 0


def test_run_analyze_summary_fields(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    """Summary should have total_cost, total_iterations, duration_minutes, stuck_count."""
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
        ]
    )
    _run_analyze(args)

    data = json.loads((output_dir / "report.json").read_text())
    summary = data["summary"]
    assert "total_cost" in summary
    assert "total_iterations" in summary
    assert "duration_minutes" in summary
    assert "stuck_count" in summary
    assert summary["total_iterations"] == 11  # fixture has 11 lines


# ---------------------------------------------------------------------------
# _run_compare
# ---------------------------------------------------------------------------


def test_run_compare_two_projects(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_a = _make_project(tmp_path / "a", fixtures_dir)
    project_b = _make_project(tmp_path / "b", fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "compare",
            "--projects",
            f"{project_a},{project_b}",
            "--output",
            str(output_dir),
        ]
    )
    code = _run_compare(args)

    assert code == 0
    assert (output_dir / "comparison.json").exists()
    assert (output_dir / "comparison.md").exists()
    assert (output_dir / "comparison.html").exists()


def test_run_compare_one_project_error(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """compare with only 1 project path should return exit code 1."""
    project_a = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "compare",
            "--projects",
            str(project_a),
            "--output",
            str(output_dir),
        ]
    )
    code = _run_compare(args)

    assert code == 1
    captured = capsys.readouterr()
    assert "at least 2" in captured.err


def test_run_compare_missing_project(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    """compare when one project has no cost.log → exit 1."""
    project_a = _make_project(tmp_path / "a", fixtures_dir)
    project_b = tmp_path / "b" / "my_project"
    (project_b / ".harness-logs").mkdir(parents=True)  # no cost.log
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "compare",
            "--projects",
            f"{project_a},{project_b}",
            "--output",
            str(output_dir),
        ]
    )
    code = _run_compare(args)
    assert code == 1


def test_run_compare_json_content(
    tmp_path: Path, fixtures_dir: Path
) -> None:
    project_a = _make_project(tmp_path / "a", fixtures_dir)
    project_b = _make_project(tmp_path / "b", fixtures_dir)
    output_dir = tmp_path / "out"

    parser = _build_parser()
    args = parser.parse_args(
        [
            "compare",
            "--projects",
            f"{project_a},{project_b}",
            "--output",
            str(output_dir),
            "--format",
            "json",
        ]
    )
    _run_compare(args)

    data = json.loads((output_dir / "comparison.json").read_text())
    assert "summary_table" in data
    assert "efficiency_ranking" in data
    assert len(data["summary_table"]) == 2


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------


def test_main_watch(capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["cost-analyze", "watch"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "not yet implemented" in captured.out


def test_main_analyze_missing_cost_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = tmp_path / "proj"
    (project_dir / ".harness-logs").mkdir(parents=True)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cost-analyze",
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(tmp_path / "out"),
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1


def test_main_analyze_success(
    tmp_path: Path, fixtures_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_dir = _make_project(tmp_path, fixtures_dir)
    output_dir = tmp_path / "report"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "cost-analyze",
            "analyze",
            "--project",
            str(project_dir),
            "--output",
            str(output_dir),
            "--format",
            "json",
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert (output_dir / "report.json").exists()
