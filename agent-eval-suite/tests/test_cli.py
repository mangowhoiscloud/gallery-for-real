"""Tests for cli.py — argparse, exit codes, and subcommand integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_eval.backends.mock import MockBackend
from agent_eval.cli import _build_parser, _make_backend, main
from agent_eval.models import RunResult

FIXTURES = Path(__file__).parent / "fixtures"
MOCK_BENCHMARK = FIXTURES / "mock_benchmark"


# ── _build_parser ─────────────────────────────────────────────────────────────


class TestParser:
    def test_run_parses_required_args(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["run", "--benchmark", "b/", "--agent", "claude", "--output", "out/"]
        )
        assert args.command == "run"
        assert args.benchmark == "b/"
        assert args.agent == "claude"
        assert args.output == "out/"

    def test_compare_parses_agents_csv(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["compare", "--benchmark", "b/", "--agents", "claude,mock", "--output", "out/"]
        )
        assert args.command == "compare"
        assert args.agents == "claude,mock"

    def test_suite_parses_config(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["suite", "--config", "eval.yaml"])
        assert args.command == "suite"
        assert args.config == "eval.yaml"
        assert args.output is None

    def test_suite_parses_output_override(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["suite", "--config", "eval.yaml", "--output", "out/"])
        assert args.output == "out/"

    def test_report_default_format(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["report", "--results", "results/"])
        assert args.format == "json"
        assert args.output is None

    def test_report_explicit_format(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["report", "--results", "results/", "--format", "markdown"]
        )
        assert args.format == "markdown"

    def test_report_invalid_format_exits(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["report", "--results", "results/", "--format", "csv"])

    def test_no_subcommand_exits(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_run_missing_required_arg_exits(self) -> None:
        parser = _build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["run", "--benchmark", "b/"])  # missing --agent and --output

    def test_report_explicit_output(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(
            ["report", "--results", "results/", "--output", "my_report.json"]
        )
        assert args.output == "my_report.json"


# ── _make_backend ─────────────────────────────────────────────────────────────


class TestMakeBackend:
    def test_mock_returns_mock_backend(self) -> None:
        backend = _make_backend("mock")
        assert isinstance(backend, MockBackend)

    def test_mock_case_insensitive(self) -> None:
        backend = _make_backend("MOCK")
        assert isinstance(backend, MockBackend)

    def test_unknown_agent_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown agent backend"):
            _make_backend("openai")

    def test_claude_returns_claude_backend(self) -> None:
        from agent_eval.backends.claude import ClaudeBackend

        backend = _make_backend("claude")
        assert isinstance(backend, ClaudeBackend)
        assert backend.model == "sonnet"

    def test_claude_with_model_sets_model(self) -> None:
        from agent_eval.backends.claude import ClaudeBackend

        backend = _make_backend("claude:opus")
        assert isinstance(backend, ClaudeBackend)
        assert backend.model == "opus"


# ── run subcommand ────────────────────────────────────────────────────────────


class TestCmdRun:
    def _mock_result(self, success: bool) -> MagicMock:
        r = MagicMock(spec=RunResult)
        r.success = success
        r.to_dict.return_value = {
            "success": success,
            "agent": "mock",
            "benchmark": "bench",
        }
        return r

    def test_run_success_exits_0(self, tmp_path: Path) -> None:
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_single", return_value=self._mock_result(True)),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    [
                        "run",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agent",
                        "mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
            assert exc.value.code == 0

    def test_run_failure_exits_1(self, tmp_path: Path) -> None:
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_single", return_value=self._mock_result(False)),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    [
                        "run",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agent",
                        "mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
            assert exc.value.code == 1

    def test_run_missing_benchmark_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "run",
                    "--benchmark",
                    str(tmp_path / "nonexistent"),
                    "--agent",
                    "mock",
                    "--output",
                    str(tmp_path),
                ]
            )
        assert exc.value.code == 2

    def test_run_unknown_agent_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "run",
                    "--benchmark",
                    str(MOCK_BENCHMARK),
                    "--agent",
                    "openai",
                    "--output",
                    str(tmp_path),
                ]
            )
        assert exc.value.code == 2

    def test_run_integration_with_mock_backend(self, tmp_path: Path) -> None:
        """End-to-end: real MockBackend reads fixture data, run_single writes result.json."""
        with patch(
            "agent_eval.cli._make_backend", return_value=MockBackend(MOCK_BENCHMARK)
        ):
            with pytest.raises(SystemExit) as exc:
                main(
                    [
                        "run",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agent",
                        "mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
        assert exc.value.code in (0, 1)
        result_files = list(tmp_path.rglob("result.json"))
        assert len(result_files) == 1

    def test_run_result_json_written(self, tmp_path: Path) -> None:
        """result.json content is valid JSON after a successful run."""
        with patch(
            "agent_eval.cli._make_backend", return_value=MockBackend(MOCK_BENCHMARK)
        ):
            with pytest.raises(SystemExit):
                main(
                    [
                        "run",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agent",
                        "mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
        result_file = next(tmp_path.rglob("result.json"))
        data = json.loads(result_file.read_text())
        assert "agent" in data
        assert "benchmark" in data
        assert "success" in data


# ── compare subcommand ────────────────────────────────────────────────────────


class TestCmdCompare:
    def test_compare_all_success_exits_0(self, tmp_path: Path) -> None:
        ok = MagicMock(spec=RunResult, success=True)
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_compare", return_value=[ok, ok]),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    [
                        "compare",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agents",
                        "mock,mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
        assert exc.value.code == 0

    def test_compare_partial_failure_exits_1(self, tmp_path: Path) -> None:
        ok = MagicMock(spec=RunResult, success=True)
        fail = MagicMock(spec=RunResult, success=False)
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_compare", return_value=[ok, fail]),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    [
                        "compare",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agents",
                        "mock,mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
        assert exc.value.code == 1

    def test_compare_missing_benchmark_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--benchmark",
                    str(tmp_path / "no"),
                    "--agents",
                    "mock",
                    "--output",
                    str(tmp_path),
                ]
            )
        assert exc.value.code == 2

    def test_compare_unknown_agent_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--benchmark",
                    str(MOCK_BENCHMARK),
                    "--agents",
                    "openai,mock",
                    "--output",
                    str(tmp_path),
                ]
            )
        assert exc.value.code == 2

    def test_compare_calls_make_backend_per_agent(self, tmp_path: Path) -> None:
        ok = MagicMock(spec=RunResult, success=True)
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_compare", return_value=[ok, ok, ok]),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit):
                main(
                    [
                        "compare",
                        "--benchmark",
                        str(MOCK_BENCHMARK),
                        "--agents",
                        "mock,mock,mock",
                        "--output",
                        str(tmp_path),
                    ]
                )
        assert mk.call_count == 3


# ── suite subcommand ──────────────────────────────────────────────────────────


class TestCmdSuite:
    def test_suite_missing_config_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["suite", "--config", str(tmp_path / "no.yaml")])
        assert exc.value.code == 2

    def test_suite_all_success_exits_0(self, tmp_path: Path) -> None:
        config_path = FIXTURES / "eval-config.yaml"
        ok = MagicMock(spec=RunResult, success=True)
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_suite", return_value=[ok]),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    ["suite", "--config", str(config_path), "--output", str(tmp_path)]
                )
        assert exc.value.code == 0

    def test_suite_failure_exits_1(self, tmp_path: Path) -> None:
        config_path = FIXTURES / "eval-config.yaml"
        fail = MagicMock(spec=RunResult, success=False)
        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_suite", return_value=[fail]),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit) as exc:
                main(
                    ["suite", "--config", str(config_path), "--output", str(tmp_path)]
                )
        assert exc.value.code == 1

    def test_suite_output_override_applied(self, tmp_path: Path) -> None:
        """--output flag overrides suite_config.output."""
        config_path = FIXTURES / "eval-config.yaml"
        ok = MagicMock(spec=RunResult, success=True)

        captured_config: list = []

        def fake_run_suite(suite_config, backend_factory):  # type: ignore[no-untyped-def]
            captured_config.append(suite_config.output)
            return [ok]

        with (
            patch("agent_eval.cli._make_backend") as mk,
            patch("agent_eval.cli.run_suite", side_effect=fake_run_suite),
        ):
            mk.return_value = MagicMock()
            with pytest.raises(SystemExit):
                main(
                    [
                        "suite",
                        "--config",
                        str(config_path),
                        "--output",
                        str(tmp_path / "custom"),
                    ]
                )
        assert captured_config[0] == str(tmp_path / "custom")


# ── report subcommand ─────────────────────────────────────────────────────────


class TestCmdReport:
    def _make_results_dir(self, tmp_path: Path) -> Path:
        """Populate a minimal results dir with a result.json."""
        run_dir = tmp_path / "bench1" / "agent1"
        run_dir.mkdir(parents=True)
        result = RunResult(
            agent="agent1",
            benchmark="bench1",
            success=True,
            build_success=True,
            test_total=5,
            test_passed=5,
            test_pass_rate=1.0,
            total_iterations=10,
            total_time_seconds=120.0,
        )
        (run_dir / "result.json").write_text(json.dumps(result.to_dict()))
        return tmp_path

    def test_report_json_exits_0(self, tmp_path: Path) -> None:
        results_dir = self._make_results_dir(tmp_path)
        report_path = tmp_path / "report.json"
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "report",
                    "--results",
                    str(results_dir),
                    "--format",
                    "json",
                    "--output",
                    str(report_path),
                ]
            )
        assert exc.value.code == 0
        assert report_path.exists()

    def test_report_markdown_exits_0(self, tmp_path: Path) -> None:
        results_dir = self._make_results_dir(tmp_path)
        report_path = tmp_path / "report.md"
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "report",
                    "--results",
                    str(results_dir),
                    "--format",
                    "markdown",
                    "--output",
                    str(report_path),
                ]
            )
        assert exc.value.code == 0
        assert report_path.exists()

    def test_report_missing_results_dir_exits_2(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc:
            main(
                ["report", "--results", str(tmp_path / "no"), "--format", "json"]
            )
        assert exc.value.code == 2

    def test_report_empty_results_exits_1(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(SystemExit) as exc:
            main(["report", "--results", str(empty_dir), "--format", "json"])
        assert exc.value.code == 1

    def test_report_auto_output_path(self, tmp_path: Path) -> None:
        """When --output is omitted, report is written to <results_dir>/report.<format>."""
        results_dir = self._make_results_dir(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["report", "--results", str(results_dir), "--format", "json"])
        assert exc.value.code == 0
        assert (results_dir / "report.json").exists()

    def test_report_html_exits_0(self, tmp_path: Path) -> None:
        """HTML format is now supported — exits 0 and writes report.html."""
        results_dir = self._make_results_dir(tmp_path)
        with pytest.raises(SystemExit) as exc:
            main(["report", "--results", str(results_dir), "--format", "html"])
        assert exc.value.code == 0
        assert (results_dir / "report.html").exists()

    def test_report_json_content_valid(self, tmp_path: Path) -> None:
        """Generated JSON report is parseable and contains expected keys."""
        results_dir = self._make_results_dir(tmp_path)
        report_path = tmp_path / "out.json"
        with pytest.raises(SystemExit):
            main(
                [
                    "report",
                    "--results",
                    str(results_dir),
                    "--format",
                    "json",
                    "--output",
                    str(report_path),
                ]
            )
        data = json.loads(report_path.read_text())
        assert "results" in data
        assert "summary" in data

    def test_report_markdown_content_has_table(self, tmp_path: Path) -> None:
        """Generated Markdown contains a comparison table."""
        results_dir = self._make_results_dir(tmp_path)
        report_path = tmp_path / "out.md"
        with pytest.raises(SystemExit):
            main(
                [
                    "report",
                    "--results",
                    str(results_dir),
                    "--format",
                    "markdown",
                    "--output",
                    str(report_path),
                ]
            )
        content = report_path.read_text()
        assert "|" in content  # markdown table rows use |
