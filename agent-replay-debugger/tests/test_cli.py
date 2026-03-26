"""Tests for CLI entrypoint: argument parsing, validation, and dispatch.

Covers:
- --help output contains all expected flags
- Invalid / missing project-dir → exit 1
- Missing .harness-logs/ → exit 1 with "Not a harness project"
- --summary, --iteration N, --failures, --export dispatch
- --iteration on nonexistent global number → exit 1
- Mutually exclusive mode flags
- Empty session message
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from io import StringIO
from pathlib import Path
from datetime import timedelta

import pytest
from rich.console import Console

import agent_replay.cli as cli_module
from agent_replay.cli import (
    _handle_export,
    _handle_failures,
    _handle_iteration,
    _handle_summary,
    _validate_project_dir,
    main,
)
from agent_replay.models import GitCommit, Iteration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_iteration(
    number: int,
    phase: str = "build",
    status: str = "OK",
    cost: str = "1.0000",
    tokens_in: int = 100,
    tokens_out: int = 500,
    items_done: list[str] | None = None,
    commits: list[GitCommit] | None = None,
    duration: timedelta | None = None,
) -> Iteration:
    it = Iteration(
        number=number,
        phase=phase,
        status=status,
        cost_total=Decimal(cost),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        items_done=items_done or [],
        git_commits=commits or [],
        duration=duration or timedelta(seconds=60),
    )
    return it


# ---------------------------------------------------------------------------
# _validate_project_dir
# ---------------------------------------------------------------------------

class TestValidateProjectDir:
    def test_valid_dir_returns_resolved_path(self, tmp_path: Path) -> None:
        (tmp_path / ".harness-logs").mkdir()
        result = _validate_project_dir(str(tmp_path))
        assert result == tmp_path.resolve()

    def test_missing_harness_logs_exits_1(self, tmp_path: Path, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            _validate_project_dir(str(tmp_path))
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Not a harness project" in captured.err

    def test_nonexistent_path_exits_1(self, tmp_path: Path, capsys) -> None:
        bogus = str(tmp_path / "does_not_exist")
        with pytest.raises(SystemExit) as exc:
            _validate_project_dir(bogus)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Not a harness project" in captured.err

    def test_harness_logs_must_be_directory(self, tmp_path: Path, capsys) -> None:
        (tmp_path / ".harness-logs").write_text("not a dir")
        with pytest.raises(SystemExit) as exc:
            _validate_project_dir(str(tmp_path))
        assert exc.value.code == 1

    def test_relative_path_resolved(self, tmp_path: Path, monkeypatch) -> None:
        (tmp_path / ".harness-logs").mkdir()
        monkeypatch.chdir(tmp_path)
        result = _validate_project_dir(".")
        assert result == tmp_path.resolve()


# ---------------------------------------------------------------------------
# _handle_summary
# ---------------------------------------------------------------------------

class TestHandleSummary:
    def test_empty_iterations_prints_empty_session(self, capsys) -> None:
        _handle_summary([], Path("/fake"))
        captured = capsys.readouterr()
        assert "Empty session" in captured.out

    def test_summary_shows_iteration_count(self, capsys) -> None:
        iterations = [_make_iteration(1), _make_iteration(2)]
        _handle_summary(iterations, Path("/fake"))
        captured = capsys.readouterr()
        assert "2" in captured.out

    def test_summary_shows_total_cost(self, capsys) -> None:
        iterations = [
            _make_iteration(1, cost="1.5000"),
            _make_iteration(2, cost="2.5000"),
        ]
        _handle_summary(iterations, Path("/fake"))
        captured = capsys.readouterr()
        assert "4.00" in captured.out

    def test_summary_shows_token_totals(self, capsys) -> None:
        iterations = [
            _make_iteration(1, tokens_in=100, tokens_out=500),
            _make_iteration(2, tokens_in=200, tokens_out=1000),
        ]
        _handle_summary(iterations, Path("/fake"))
        captured = capsys.readouterr()
        assert "300" in captured.out
        assert "1,500" in captured.out

    def test_summary_shows_status_counts(self, capsys) -> None:
        iterations = [
            _make_iteration(1, status="OK"),
            _make_iteration(2, status="FAIL"),
            _make_iteration(3, status="STUCK"),
            _make_iteration(4, status="OK"),
        ]
        _handle_summary(iterations, Path("/fake"))
        captured = capsys.readouterr()
        assert "2 OK" in captured.out
        assert "1 FAIL" in captured.out
        assert "1 STUCK" in captured.out


# ---------------------------------------------------------------------------
# _handle_iteration
# ---------------------------------------------------------------------------

class TestHandleIteration:
    def test_found_iteration_prints_details(self, capsys) -> None:
        iterations = [_make_iteration(1, phase="build", status="OK")]
        _handle_iteration(iterations, 1)
        captured = capsys.readouterr()
        assert "1" in captured.out
        assert "build" in captured.out
        assert "OK" in captured.out

    def test_not_found_exits_1(self, capsys) -> None:
        iterations = [_make_iteration(1), _make_iteration(2)]
        with pytest.raises(SystemExit) as exc:
            _handle_iteration(iterations, 99)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "99" in captured.err
        assert "not found" in captured.err

    def test_not_found_message_includes_session_size(self, capsys) -> None:
        iterations = [_make_iteration(i) for i in range(1, 6)]
        with pytest.raises(SystemExit):
            _handle_iteration(iterations, 999)
        captured = capsys.readouterr()
        assert "5" in captured.err

    def test_shows_cost(self, capsys) -> None:
        iterations = [_make_iteration(1, cost="3.1400")]
        _handle_iteration(iterations, 1)
        captured = capsys.readouterr()
        assert "3.1400" in captured.out

    def test_shows_git_commits(self, capsys) -> None:
        from datetime import datetime, timezone

        commit = GitCommit(
            hash="abcdef1234567890",
            message="feat: something",
            timestamp=datetime(2026, 3, 24, tzinfo=timezone.utc),
        )
        iterations = [_make_iteration(1, commits=[commit])]
        _handle_iteration(iterations, 1)
        captured = capsys.readouterr()
        assert "abcdef12" in captured.out
        assert "feat: something" in captured.out

    def test_shows_items_done(self, capsys) -> None:
        iterations = [_make_iteration(1, items_done=["Item 3 - cost.log parser"])]
        _handle_iteration(iterations, 1)
        captured = capsys.readouterr()
        assert "Item 3" in captured.out

    def test_shows_duration(self, capsys) -> None:
        iterations = [_make_iteration(1, duration=timedelta(minutes=5))]
        _handle_iteration(iterations, 1)
        captured = capsys.readouterr()
        assert "0:05:00" in captured.out

    def test_empty_session_exits_1(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            _handle_iteration([], 1)
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "0 iterations" in captured.err


# ---------------------------------------------------------------------------
# _handle_failures
# ---------------------------------------------------------------------------

class TestHandleFailures:
    def test_no_failures_prints_no_failures_message(self, capsys) -> None:
        iterations = [_make_iteration(1, status="OK"), _make_iteration(2, status="OK")]
        _handle_failures(iterations)
        captured = capsys.readouterr()
        assert "No failures" in captured.out

    def test_fail_iterations_shown(self, capsys) -> None:
        iterations = [
            _make_iteration(1, status="OK"),
            _make_iteration(2, status="FAIL"),
        ]
        _handle_failures(iterations)
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "#  2" in captured.out or "#2" in captured.out or "2" in captured.out

    def test_stuck_iterations_shown(self, capsys) -> None:
        iterations = [
            _make_iteration(1, status="STUCK"),
            _make_iteration(2, status="OK"),
        ]
        _handle_failures(iterations)
        captured = capsys.readouterr()
        assert "STUCK" in captured.out

    def test_both_fail_and_stuck_shown(self, capsys) -> None:
        iterations = [
            _make_iteration(1, status="FAIL"),
            _make_iteration(2, status="STUCK"),
            _make_iteration(3, status="OK"),
        ]
        _handle_failures(iterations)
        captured = capsys.readouterr()
        assert "Failures (2)" in captured.out

    def test_ok_iterations_excluded(self, capsys) -> None:
        iterations = [
            _make_iteration(1, status="FAIL"),
            _make_iteration(2, status="OK"),
            _make_iteration(3, status="STUCK"),
        ]
        _handle_failures(iterations)
        captured = capsys.readouterr()
        assert "OK" not in captured.out

    def test_empty_session_no_failures(self, capsys) -> None:
        _handle_failures([])
        captured = capsys.readouterr()
        assert "No failures" in captured.out


# ---------------------------------------------------------------------------
# _handle_iteration — rich Panel formatting
# ---------------------------------------------------------------------------

class TestHandleIterationRich:
    def _console(self) -> tuple[Console, StringIO]:
        buf = StringIO()
        return Console(file=buf, highlight=False), buf

    def test_panel_title_contains_iteration_number(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(7, phase="test")]
        _handle_iteration(iterations, 7, console=console)
        assert "Iteration 7" in buf.getvalue()

    def test_panel_shows_phase_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, phase="build")]
        _handle_iteration(iterations, 1, console=console)
        assert "Phase:" in buf.getvalue()
        assert "build" in buf.getvalue()

    def test_panel_shows_status_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, status="STUCK")]
        _handle_iteration(iterations, 1, console=console)
        assert "Status:" in buf.getvalue()
        assert "STUCK" in buf.getvalue()

    def test_panel_shows_tokens_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, tokens_in=42, tokens_out=999)]
        _handle_iteration(iterations, 1, console=console)
        assert "Tokens:" in buf.getvalue()
        assert "42" in buf.getvalue()
        assert "999" in buf.getvalue()

    def test_panel_shows_duration_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, duration=timedelta(minutes=3))]
        _handle_iteration(iterations, 1, console=console)
        assert "Duration:" in buf.getvalue()
        assert "0:03:00" in buf.getvalue()

    def test_panel_shows_cost_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, cost="2.7182")]
        _handle_iteration(iterations, 1, console=console)
        assert "Cost:" in buf.getvalue()
        assert "2.7182" in buf.getvalue()

    def test_panel_shows_commit_hash_and_message(self) -> None:
        from datetime import datetime, timezone

        console, buf = self._console()
        commit = GitCommit(
            hash="deadbeef12345678",
            message="fix: something broken",
            timestamp=datetime(2026, 3, 25, tzinfo=timezone.utc),
        )
        iterations = [_make_iteration(1, commits=[commit])]
        _handle_iteration(iterations, 1, console=console)
        assert "deadbeef" in buf.getvalue()
        assert "fix: something broken" in buf.getvalue()

    def test_panel_shows_items_done_label(self) -> None:
        console, buf = self._console()
        iterations = [_make_iteration(1, items_done=["Item 5 - progress parser"])]
        _handle_iteration(iterations, 1, console=console)
        assert "Done:" in buf.getvalue()
        assert "Item 5" in buf.getvalue()

    def test_console_parameter_used_not_stdout(self, capsys) -> None:
        """Output goes to injected console, not stdout."""
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        iterations = [_make_iteration(3, phase="lint")]
        _handle_iteration(iterations, 3, console=console)
        stdout = capsys.readouterr().out
        # the injected buffer has content; stdout is empty
        assert "lint" in buf.getvalue()
        assert "lint" not in stdout


# ---------------------------------------------------------------------------
# _handle_failures — rich Table formatting
# ---------------------------------------------------------------------------

class TestHandleFailuresRich:
    def _console(self) -> tuple[Console, StringIO]:
        buf = StringIO()
        return Console(file=buf, highlight=False), buf

    def test_table_title_contains_failure_count(self) -> None:
        console, buf = self._console()
        iterations = [
            _make_iteration(1, status="FAIL"),
            _make_iteration(2, status="STUCK"),
        ]
        _handle_failures(iterations, console=console)
        assert "Failures (2)" in buf.getvalue()

    def test_table_has_phase_column(self) -> None:
        console, buf = self._console()
        _handle_failures([_make_iteration(1, status="FAIL")], console=console)
        assert "Phase" in buf.getvalue()

    def test_table_has_status_column(self) -> None:
        console, buf = self._console()
        _handle_failures([_make_iteration(1, status="FAIL")], console=console)
        assert "Status" in buf.getvalue()

    def test_table_has_cost_column(self) -> None:
        console, buf = self._console()
        _handle_failures([_make_iteration(1, status="FAIL")], console=console)
        assert "Cost" in buf.getvalue()

    def test_table_cost_formatted_with_dollar(self) -> None:
        console, buf = self._console()
        _handle_failures(
            [_make_iteration(1, status="FAIL", cost="1.2345")], console=console
        )
        assert "$1.2345" in buf.getvalue()

    def test_table_shows_iteration_numbers(self) -> None:
        console, buf = self._console()
        iterations = [
            _make_iteration(3, status="FAIL"),
            _make_iteration(7, status="STUCK"),
        ]
        _handle_failures(iterations, console=console)
        out = buf.getvalue()
        assert "3" in out
        assert "7" in out

    def test_no_failures_uses_console(self, capsys) -> None:
        """No-failures message goes to injected console, not stdout."""
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        _handle_failures([], console=console)
        stdout = capsys.readouterr().out
        assert "No failures" in buf.getvalue()
        assert "No failures" not in stdout

    def test_console_parameter_used_not_stdout(self, capsys) -> None:
        """Failure table goes to injected console, not stdout."""
        buf = StringIO()
        console = Console(file=buf, highlight=False)
        _handle_failures([_make_iteration(1, status="FAIL")], console=console)
        stdout = capsys.readouterr().out
        assert "FAIL" in buf.getvalue()
        assert "FAIL" not in stdout


# ---------------------------------------------------------------------------
# _handle_export
# ---------------------------------------------------------------------------

class TestHandleExport:
    def test_creates_json_file(self, tmp_path: Path, capsys) -> None:
        iterations = [_make_iteration(1)]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        assert out.exists()

    def test_json_is_valid(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(1)]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        data = json.loads(out.read_text())
        assert isinstance(data, dict)
        assert len(data["iterations"]) == 1

    def test_json_fields_present(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(1, phase="build", status="FAIL", cost="2.5")]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        data = json.loads(out.read_text())
        entry = data["iterations"][0]
        assert entry["number"] == 1
        assert entry["phase"] == "build"
        assert entry["status"] == "FAIL"
        assert entry["cost_total"] == "2.5"

    def test_decimal_serialised_as_string(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(1, cost="3.141592653589793")]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        raw = out.read_text()
        assert "3.141592653589793" in raw

    def test_git_commits_included(self, tmp_path: Path) -> None:
        from datetime import datetime, timezone

        commit = GitCommit(
            hash="abc123def456",
            message="chore: bump",
            timestamp=datetime(2026, 3, 25, tzinfo=timezone.utc),
        )
        iterations = [_make_iteration(1, commits=[commit])]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        data = json.loads(out.read_text())
        assert data["iterations"][0]["git_commits"][0]["hash"] == "abc123def456"

    def test_prints_export_confirmation(self, tmp_path: Path, capsys) -> None:
        iterations = [_make_iteration(1)]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        captured = capsys.readouterr()
        assert "Exported" in captured.out
        assert "1" in captured.out

    def test_multiple_iterations(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(i) for i in range(1, 6)]
        out = tmp_path / "report.json"
        _handle_export(iterations, out)
        data = json.loads(out.read_text())
        assert len(data["iterations"]) == 5


# ---------------------------------------------------------------------------
# main() integration
# ---------------------------------------------------------------------------

class TestMainArgparse:
    def test_help_exits_0(self) -> None:
        sys.argv = ["agent-replay", "--help"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0

    def test_help_mentions_summary(self, capsys) -> None:
        sys.argv = ["agent-replay", "--help"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "--summary" in captured.out

    def test_help_mentions_iteration(self, capsys) -> None:
        sys.argv = ["agent-replay", "--help"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "--iteration" in captured.out

    def test_help_mentions_failures(self, capsys) -> None:
        sys.argv = ["agent-replay", "--help"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "--failures" in captured.out

    def test_help_mentions_export(self, capsys) -> None:
        sys.argv = ["agent-replay", "--help"]
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "--export" in captured.out

    def test_missing_project_dir_exits_nonzero(self) -> None:
        sys.argv = ["agent-replay"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_summary_and_iteration_mutually_exclusive(self, tmp_path: Path, capsys) -> None:
        (tmp_path / ".harness-logs").mkdir()
        sys.argv = ["agent-replay", str(tmp_path), "--summary", "--iteration", "1"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_summary_and_failures_mutually_exclusive(self, tmp_path: Path, capsys) -> None:
        (tmp_path / ".harness-logs").mkdir()
        sys.argv = ["agent-replay", str(tmp_path), "--summary", "--failures"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_iteration_and_failures_mutually_exclusive(self, tmp_path: Path, capsys) -> None:
        (tmp_path / ".harness-logs").mkdir()
        sys.argv = [
            "agent-replay",
            str(tmp_path),
            "--iteration",
            "1",
            "--failures",
        ]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0


class TestMainDispatch:
    def test_invalid_project_dir_exits_1(self, tmp_path: Path, capsys) -> None:
        sys.argv = ["agent-replay", str(tmp_path / "nonexistent")]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Not a harness project" in captured.err

    def test_missing_harness_logs_exits_1(self, tmp_path: Path, capsys) -> None:
        sys.argv = ["agent-replay", str(tmp_path)]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "Not a harness project" in captured.err

    def test_summary_dispatches(self, sample_project: Path, capsys, monkeypatch) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        sys.argv = ["agent-replay", str(sample_project), "--summary"]
        main()
        captured = capsys.readouterr()
        assert "Iterations" in captured.out

    def test_summary_empty_session(self, sample_project: Path, capsys, monkeypatch) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [])
        sys.argv = ["agent-replay", str(sample_project), "--summary"]
        main()
        captured = capsys.readouterr()
        assert "Empty session" in captured.out

    def test_iteration_dispatches(self, sample_project: Path, capsys, monkeypatch) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        sys.argv = ["agent-replay", str(sample_project), "--iteration", "1"]
        main()
        captured = capsys.readouterr()
        assert "Iteration 1" in captured.out

    def test_iteration_not_found(self, sample_project: Path, capsys, monkeypatch) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        sys.argv = ["agent-replay", str(sample_project), "--iteration", "99"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err

    def test_failures_dispatches(self, sample_project: Path, capsys, monkeypatch) -> None:
        iters = [_make_iteration(1, status="FAIL"), _make_iteration(2, status="OK")]
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: iters)
        sys.argv = ["agent-replay", str(sample_project), "--failures"]
        main()
        captured = capsys.readouterr()
        assert "FAIL" in captured.out

    def test_export_creates_file(self, sample_project: Path, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        out_file = tmp_path / "report.json"
        sys.argv = [
            "agent-replay",
            str(sample_project),
            "--summary",
            "--export",
            str(out_file),
        ]
        main()
        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["total_iterations"] == 1

    def test_export_alone_no_tui(self, sample_project: Path, tmp_path: Path, monkeypatch) -> None:
        """--export without mode flag should export without launching TUI."""
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        tui_called = []
        monkeypatch.setattr(cli_module, "_launch_tui", lambda p, i: tui_called.append(True))
        out_file = tmp_path / "export_only.json"
        sys.argv = ["agent-replay", str(sample_project), "--export", str(out_file)]
        main()
        assert out_file.exists()
        assert not tui_called

    def test_default_no_flags_launches_tui(self, sample_project: Path, monkeypatch) -> None:
        """With no display flags and no --export, TUI should be launched."""
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        tui_called = []
        monkeypatch.setattr(cli_module, "_launch_tui", lambda p, i: tui_called.append(True))
        sys.argv = ["agent-replay", str(sample_project)]
        main()
        assert tui_called

    def test_summary_does_not_launch_tui(self, sample_project: Path, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli_module, "build_timeline", lambda p: [_make_iteration(1)])
        tui_called = []
        monkeypatch.setattr(cli_module, "_launch_tui", lambda p, i: tui_called.append(True))
        sys.argv = ["agent-replay", str(sample_project), "--summary"]
        main()
        assert not tui_called
