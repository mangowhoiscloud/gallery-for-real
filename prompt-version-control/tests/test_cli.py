"""Tests for CLI argument parsing, dispatch, and exit codes."""

from unittest.mock import MagicMock, patch

import pytest

from prompt_vc.cli import build_parser, main, _HANDLERS


# ---------------------------------------------------------------------------
# Parser tests — argument parsing correctness
# ---------------------------------------------------------------------------


class TestParser:
    def test_no_subcommand_sets_command_none(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None

    def test_init_default_dir(self):
        parser = build_parser()
        args = parser.parse_args(["init"])
        assert args.command == "init"
        assert args.dir == "."

    def test_init_custom_dir(self):
        parser = build_parser()
        args = parser.parse_args(["init", "--dir", "./prompts"])
        assert args.dir == "./prompts"

    def test_snapshot_message_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["snapshot", "-m", "my message"])
        assert args.command == "snapshot"
        assert args.message == "my message"

    def test_snapshot_message_long_flag(self):
        parser = build_parser()
        args = parser.parse_args(["snapshot", "--message", "my message"])
        assert args.message == "my message"

    def test_snapshot_message_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["snapshot"])

    def test_log_no_args(self):
        parser = build_parser()
        args = parser.parse_args(["log"])
        assert args.command == "log"

    def test_diff_positional_args(self):
        parser = build_parser()
        args = parser.parse_args(["diff", "v1", "v2"])
        assert args.command == "diff"
        assert args.v1 == "v1"
        assert args.v2 == "v2"

    def test_checkout_positional_version(self):
        parser = build_parser()
        args = parser.parse_args(["checkout", "v2"])
        assert args.command == "checkout"
        assert args.version == "v2"
        assert args.force is False

    def test_checkout_force_short(self):
        parser = build_parser()
        args = parser.parse_args(["checkout", "v2", "-f"])
        assert args.force is True

    def test_checkout_force_long(self):
        parser = build_parser()
        args = parser.parse_args(["checkout", "v2", "--force"])
        assert args.force is True

    def test_bind_version_and_result(self):
        parser = build_parser()
        args = parser.parse_args(["bind", "v3", "--result", "results/run.json"])
        assert args.command == "bind"
        assert args.version == "v3"
        assert args.result == "results/run.json"

    def test_bind_result_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["bind", "v1", "-r", "run.json"])
        assert args.result == "run.json"

    def test_bind_result_required(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["bind", "v1"])

    def test_compare_positional_versions(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2"])
        assert args.command == "compare"
        assert args.v1 == "v1"
        assert args.v2 == "v2"
        assert args.benchmark is None

    def test_compare_benchmark_flag(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2", "--benchmark", "word-counter"])
        assert args.benchmark == "word-counter"

    def test_compare_benchmark_short_flag(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2", "-b", "word-counter"])
        assert args.benchmark == "word-counter"

    def test_compare_default_format_is_terminal(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2"])
        assert args.format == "terminal"

    def test_compare_format_html(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2", "--format", "html"])
        assert args.format == "html"

    def test_compare_format_markdown(self):
        parser = build_parser()
        args = parser.parse_args(["compare", "v1", "v2", "--format", "markdown"])
        assert args.format == "markdown"

    def test_compare_invalid_format_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["compare", "v1", "v2", "--format", "pdf"])

    def test_trend_no_args(self):
        parser = build_parser()
        args = parser.parse_args(["trend"])
        assert args.command == "trend"

    def test_trend_default_format_is_terminal(self):
        parser = build_parser()
        args = parser.parse_args(["trend"])
        assert args.format == "terminal"

    def test_trend_format_html(self):
        parser = build_parser()
        args = parser.parse_args(["trend", "--format", "html"])
        assert args.format == "html"

    def test_trend_format_markdown(self):
        parser = build_parser()
        args = parser.parse_args(["trend", "--format", "markdown"])
        assert args.format == "markdown"

    def test_trend_invalid_format_exits(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["trend", "--format", "pdf"])


# ---------------------------------------------------------------------------
# Dispatch tests — all subcommands registered
# ---------------------------------------------------------------------------


def test_all_handlers_registered():
    expected = {"init", "snapshot", "log", "diff", "checkout", "bind", "compare", "trend"}
    assert set(_HANDLERS.keys()) == expected


# ---------------------------------------------------------------------------
# main() exit code tests
# ---------------------------------------------------------------------------


def _run_main(argv: list[str]) -> int:
    """Invoke main() with patched sys.argv and capture exit code."""
    with patch("sys.argv", ["prompt-vc"] + argv):
        with pytest.raises(SystemExit) as exc_info:
            main()
    return exc_info.value.code


class TestMainExitCodes:
    def test_no_subcommand_exits_1(self):
        assert _run_main([]) == 1

    def test_init_success_exits_0(self):
        with patch("prompt_vc.commands.init.init") as mock_init:
            mock_init.return_value = None
            code = _run_main(["init", "--dir", "."])
        assert code == 0

    def test_init_already_initialized_exits_1(self):
        from prompt_vc.commands.init import AlreadyInitializedError

        with patch("prompt_vc.commands.init.init", side_effect=AlreadyInitializedError("already")):
            code = _run_main(["init"])
        assert code == 1

    def test_snapshot_success_exits_0(self):
        mock_meta = MagicMock()
        mock_meta.version = "v1"
        mock_meta.message = "test"
        with patch("prompt_vc.commands.snapshot.snapshot", return_value=mock_meta):
            code = _run_main(["snapshot", "-m", "test"])
        assert code == 0

    def test_snapshot_not_initialized_exits_1(self):
        from prompt_vc.commands.snapshot import NotInitializedError

        with patch(
            "prompt_vc.commands.snapshot.snapshot",
            side_effect=NotInitializedError("not init"),
        ):
            code = _run_main(["snapshot", "-m", "test"])
        assert code == 1

    def test_snapshot_no_changes_exits_1(self):
        from prompt_vc.commands.snapshot import NoChangesError

        with patch(
            "prompt_vc.commands.snapshot.snapshot",
            side_effect=NoChangesError("no changes"),
        ):
            code = _run_main(["snapshot", "-m", "test"])
        assert code == 1

    def test_log_success_exits_0(self):
        with patch("prompt_vc.commands.log.log", return_value="v1  2026-03-24  msg"):
            code = _run_main(["log"])
        assert code == 0

    def test_log_not_initialized_exits_1(self):
        from prompt_vc.commands.log import NotInitializedError

        with patch(
            "prompt_vc.commands.log.log",
            side_effect=NotInitializedError("not init"),
        ):
            code = _run_main(["log"])
        assert code == 1

    def test_diff_success_exits_0(self):
        with patch("prompt_vc.commands.diff.diff", return_value="--- a\n+++ b\n"):
            code = _run_main(["diff", "v1", "v2"])
        assert code == 0

    def test_diff_version_not_found_exits_1(self):
        from prompt_vc.commands.diff import VersionNotFoundError

        with patch(
            "prompt_vc.commands.diff.diff",
            side_effect=VersionNotFoundError("not found"),
        ):
            code = _run_main(["diff", "v1", "v99"])
        assert code == 1

    def test_checkout_success_exits_0(self):
        with patch("prompt_vc.commands.checkout.checkout", return_value=None):
            code = _run_main(["checkout", "v1"])
        assert code == 0

    def test_checkout_unsaved_changes_exits_1(self):
        from prompt_vc.commands.checkout import UnsavedChangesError

        with patch(
            "prompt_vc.commands.checkout.checkout",
            side_effect=UnsavedChangesError("unsaved"),
        ):
            code = _run_main(["checkout", "v1"])
        assert code == 1

    def test_checkout_force_flag_passed(self):
        with patch("prompt_vc.commands.checkout.checkout", return_value=None) as mock_co:
            _run_main(["checkout", "v1", "--force"])
            mock_co.assert_called_once()
            _, kwargs = mock_co.call_args
            assert kwargs["force"] is True

    def test_bind_success_exits_0(self):
        mock_meta = MagicMock()
        mock_meta.version = "v1"
        mock_meta.benchmark = "word-counter"
        with patch("prompt_vc.commands.bind.bind", return_value=mock_meta):
            code = _run_main(["bind", "v1", "--result", "run.json"])
        assert code == 0

    def test_bind_invalid_result_exits_1(self):
        from prompt_vc.commands.bind import InvalidResultError

        with patch(
            "prompt_vc.commands.bind.bind",
            side_effect=InvalidResultError("invalid"),
        ):
            code = _run_main(["bind", "v1", "-r", "bad.json"])
        assert code == 1

    def test_compare_success_exits_0(self):
        with patch("prompt_vc.commands.compare.compare", return_value="=== Comparison ==="):
            code = _run_main(["compare", "v1", "v2"])
        assert code == 0

    def test_compare_no_benchmarks_exits_1(self):
        from prompt_vc.commands.compare import NoBenchmarksError

        with patch(
            "prompt_vc.commands.compare.compare",
            side_effect=NoBenchmarksError("no benchmarks"),
        ):
            code = _run_main(["compare", "v1", "v2"])
        assert code == 1

    def test_compare_benchmark_filter_passed(self):
        with patch(
            "prompt_vc.commands.compare.compare", return_value="filtered"
        ) as mock_cmp:
            _run_main(["compare", "v1", "v2", "--benchmark", "word-counter"])
            _, kwargs = mock_cmp.call_args
            assert kwargs["benchmark"] == "word-counter"

    def test_compare_no_benchmark_filter_is_none(self):
        with patch(
            "prompt_vc.commands.compare.compare", return_value="all"
        ) as mock_cmp:
            _run_main(["compare", "v1", "v2"])
            _, kwargs = mock_cmp.call_args
            assert kwargs["benchmark"] is None

    def test_trend_success_exits_0(self):
        with patch("prompt_vc.commands.trend.trend", return_value="=== Trend ==="):
            code = _run_main(["trend"])
        assert code == 0

    def test_trend_not_initialized_exits_1(self):
        from prompt_vc.commands.trend import NotInitializedError

        with patch(
            "prompt_vc.commands.trend.trend",
            side_effect=NotInitializedError("not init"),
        ):
            code = _run_main(["trend"])
        assert code == 1

    def test_compare_format_html_exits_0(self, capsys):
        with patch(
            "prompt_vc.commands.compare.compare",
            return_value="=== Prompt A/B Comparison: v1 vs v2 ===",
        ):
            code = _run_main(["compare", "v1", "v2", "--format", "html"])
        assert code == 0
        out = capsys.readouterr().out
        assert "<!DOCTYPE html>" in out

    def test_compare_format_markdown_exits_0(self, capsys):
        with patch(
            "prompt_vc.commands.compare.compare",
            return_value="=== Prompt A/B Comparison: v1 vs v2 ===",
        ):
            code = _run_main(["compare", "v1", "v2", "--format", "markdown"])
        assert code == 0
        out = capsys.readouterr().out
        assert "## Prompt A/B Comparison" in out

    def test_trend_format_html_exits_0(self, capsys):
        with patch("prompt_vc.commands.trend.trend", return_value="=== Metric Trend ==="):
            code = _run_main(["trend", "--format", "html"])
        assert code == 0
        out = capsys.readouterr().out
        assert "<!DOCTYPE html>" in out

    def test_trend_format_markdown_exits_0(self, capsys):
        with patch("prompt_vc.commands.trend.trend", return_value="=== Metric Trend ==="):
            code = _run_main(["trend", "--format", "markdown"])
        assert code == 0
        out = capsys.readouterr().out
        assert "## Metric Trend" in out
