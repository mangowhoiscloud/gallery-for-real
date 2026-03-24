"""Tests for AgentBackend ABC, MockBackend, and ClaudeBackend."""

from __future__ import annotations

import inspect
import subprocess
from abc import ABC
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from agent_eval.backends.base import AgentBackend
from agent_eval.backends.claude import ClaudeBackend
from agent_eval.backends.mock import MockBackend
from agent_eval.models import RunResult

# Path to the mock_benchmark fixture directory
MOCK_BENCHMARK = Path(__file__).parent / "fixtures" / "mock_benchmark"


# ---------------------------------------------------------------------------
# AgentBackend ABC contract
# ---------------------------------------------------------------------------


class TestAgentBackendABC:
    def test_is_abstract(self) -> None:
        assert issubclass(AgentBackend, ABC)

    def test_run_is_abstract(self) -> None:
        assert getattr(AgentBackend.run, "__isabstractmethod__", False)

    def test_cannot_instantiate_directly(self) -> None:
        with pytest.raises(TypeError):
            AgentBackend()  # type: ignore[abstract]

    def test_run_signature(self) -> None:
        sig = inspect.signature(AgentBackend.run)
        params = list(sig.parameters)
        assert "benchmark_dir" in params
        assert "output_dir" in params

    def test_concrete_subclass_must_implement_run(self) -> None:
        class Incomplete(AgentBackend):
            pass

        with pytest.raises(TypeError):
            Incomplete()  # type: ignore[abstract]

    def test_concrete_subclass_with_run_instantiates(self) -> None:
        class Complete(AgentBackend):
            def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:  # type: ignore[override]
                raise NotImplementedError

        backend = Complete()
        assert isinstance(backend, AgentBackend)


# ---------------------------------------------------------------------------
# MockBackend construction
# ---------------------------------------------------------------------------


class TestMockBackendConstruction:
    def test_default_agent_name(self) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        assert backend.agent_name == "mock-agent"

    def test_custom_agent_name(self) -> None:
        backend = MockBackend(MOCK_BENCHMARK, agent_name="claude-opus")
        assert backend.agent_name == "claude-opus"

    def test_fixture_dir_stored_as_path(self) -> None:
        backend = MockBackend(str(MOCK_BENCHMARK))  # str input
        assert isinstance(backend.fixture_dir, Path)

    def test_is_agent_backend(self) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        assert isinstance(backend, AgentBackend)


# ---------------------------------------------------------------------------
# MockBackend.run() — end-to-end
# ---------------------------------------------------------------------------


class TestMockBackendRun:
    def test_returns_run_result(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert isinstance(result, RunResult)

    def test_agent_name_propagated(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK, agent_name="test-agent")
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.agent == "test-agent"

    def test_benchmark_name_from_dir(self, tmp_path: Path) -> None:
        benchmark_dir = tmp_path / "my-benchmark"
        benchmark_dir.mkdir()
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(benchmark_dir, tmp_path / "out")
        assert result.benchmark == "my-benchmark"

    def test_build_success_is_true(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.build_success is True

    # --- cost.log derived fields ---

    def test_total_tokens_in(self, tmp_path: Path) -> None:
        # 800 + 1500 + 2000 + 1800 + 3000
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.total_tokens_in == 9100

    def test_total_tokens_out(self, tmp_path: Path) -> None:
        # 4200 + 3800 + 6000 + 5500 + 4500
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.total_tokens_out == 24000

    def test_estimated_cost(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert abs(result.estimated_cost - 1.2264) < 1e-6

    def test_total_iterations(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.total_iterations == 5

    def test_total_time_seconds(self, tmp_path: Path) -> None:
        # 08:00 → 08:45 = 2700 seconds
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.total_time_seconds == pytest.approx(2700.0)

    def test_phase_times_contains_build(self, tmp_path: Path) -> None:
        # build phase: 08:30 → 08:35 = 300 seconds
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert "build" in result.phase_times
        assert result.phase_times["build"] == pytest.approx(300.0)

    # --- IMPLEMENTATION_PLAN.md derived fields ---

    def test_items_completed(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.items_completed == 2

    def test_items_total(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.items_total == 3

    # --- phase.log derived fields ---

    def test_circuit_breaker_count(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.circuit_breaker_count == 2

    def test_stuck_count(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.stuck_count == 1

    # --- test_output.txt derived fields ---

    def test_test_total(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.test_total == 10

    def test_test_passed(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.test_passed == 10

    def test_success_true_when_all_pass(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.success is True

    def test_test_pass_rate_is_one(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.test_pass_rate == pytest.approx(1.0)

    def test_error_is_none(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.error is None

    # --- directory isolation ---

    def test_output_dir_created(self, tmp_path: Path) -> None:
        out = tmp_path / "nested" / "out"
        backend = MockBackend(MOCK_BENCHMARK)
        backend.run(MOCK_BENCHMARK, out)
        assert out.is_dir()

    def test_harness_logs_copied_to_output_dir(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        backend = MockBackend(MOCK_BENCHMARK)
        backend.run(MOCK_BENCHMARK, out)
        assert (out / ".harness-logs" / "cost.log").is_file()
        assert (out / ".harness-logs" / "phase.log").is_file()

    def test_implementation_plan_copied(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        backend = MockBackend(MOCK_BENCHMARK)
        backend.run(MOCK_BENCHMARK, out)
        assert (out / "IMPLEMENTATION_PLAN.md").is_file()

    def test_progress_txt_copied(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        backend = MockBackend(MOCK_BENCHMARK)
        backend.run(MOCK_BENCHMARK, out)
        assert (out / "progress.txt").is_file()

    def test_fixture_dir_unchanged(self, tmp_path: Path) -> None:
        """Source fixture files must not be modified."""
        original_cost = (MOCK_BENCHMARK / ".harness-logs" / "cost.log").read_text()
        backend = MockBackend(MOCK_BENCHMARK)
        backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert (MOCK_BENCHMARK / ".harness-logs" / "cost.log").read_text() == original_cost

    def test_run_is_idempotent(self, tmp_path: Path) -> None:
        """Calling run twice on the same output_dir should not crash."""
        out = tmp_path / "out"
        backend = MockBackend(MOCK_BENCHMARK)
        r1 = backend.run(MOCK_BENCHMARK, out)
        r2 = backend.run(MOCK_BENCHMARK, out)
        assert r1.total_tokens_in == r2.total_tokens_in

    # --- fallback when test_output.txt is absent ---

    def test_fallback_canned_test_output(self, tmp_path: Path) -> None:
        """When fixture_dir has no test_output.txt, use canned default (1 passed)."""
        # Create a stripped-down fixture dir with logs but no test_output.txt
        stripped = tmp_path / "stripped"
        shutil.copytree(MOCK_BENCHMARK, stripped)
        (stripped / "test_output.txt").unlink(missing_ok=True)

        backend = MockBackend(stripped)
        result = backend.run(stripped, tmp_path / "out")
        assert result.test_total == 1
        assert result.test_passed == 1


# shutil is used in the last test
import shutil  # noqa: E402  (must come after Write so ruff sees it as used)


# ---------------------------------------------------------------------------
# ClaudeBackend construction
# ---------------------------------------------------------------------------


class TestClaudeBackendConstruction:
    def test_is_agent_backend(self) -> None:
        backend = ClaudeBackend("claude-opus-4")
        assert isinstance(backend, AgentBackend)

    def test_model_stored(self) -> None:
        backend = ClaudeBackend("claude-opus-4")
        assert backend.model == "claude-opus-4"

    def test_agent_name_contains_model(self) -> None:
        backend = ClaudeBackend("claude-opus-4")
        assert "claude" in backend.agent_name
        assert "claude-opus-4" in backend.agent_name

    def test_different_models(self) -> None:
        b1 = ClaudeBackend("claude-sonnet-4-6")
        b2 = ClaudeBackend("claude-haiku-4-5")
        assert b1.agent_name != b2.agent_name
        assert "claude-sonnet-4-6" in b1.agent_name
        assert "claude-haiku-4-5" in b2.agent_name


# ---------------------------------------------------------------------------
# ClaudeBackend.run() — with mocked subprocess
# ---------------------------------------------------------------------------


def _make_proc(returncode: int = 0, stdout: str = "", stderr: str = "") -> MagicMock:
    """Build a fake CompletedProcess-like mock."""
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


class TestClaudeBackendRun:
    def test_run_returns_run_result(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_proc(0),
                _make_proc(0, stdout="5 passed in 0.1s"),
            ]
            backend = ClaudeBackend("claude-opus-4")
            result = backend.run(MOCK_BENCHMARK, tmp_path / "out")
        assert isinstance(result, RunResult)

    def test_run_calls_loop_sh(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        first_args = mock_run.call_args_list[0][0][0]
        assert first_args == ["bash", "loop.sh"]

    def test_run_sets_opus_model_env(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        env = mock_run.call_args_list[0][1]["env"]
        assert env["OPUS_MODEL"] == "claude-opus-4"

    def test_run_sets_sonnet_model_env(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            ClaudeBackend("claude-sonnet-4-6").run(MOCK_BENCHMARK, tmp_path / "out")
        env = mock_run.call_args_list[0][1]["env"]
        assert env["SONNET_MODEL"] == "claude-sonnet-4-6"

    def test_run_cwd_is_output_dir(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, out)
        cwd = mock_run.call_args_list[0][1]["cwd"]
        assert Path(cwd) == out

    def test_build_success_when_exit_0(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.build_success is True
        assert result.error is None

    def test_build_failure_when_nonzero_exit(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(1), _make_proc(0)]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.build_success is False
        assert result.error is not None
        assert "1" in result.error

    def test_timeout_sets_error(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired(cmd=["bash", "loop.sh"], timeout=300),
                _make_proc(0),
            ]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.build_success is False
        assert result.error is not None
        assert "timed out" in result.error

    def test_timeout_still_returns_run_result(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired(cmd=["bash", "loop.sh"], timeout=300),
                _make_proc(0),
            ]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert isinstance(result, RunResult)

    def test_result_agent_contains_model(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert "claude-opus-4" in result.agent

    def test_benchmark_name_from_dir(self, tmp_path: Path) -> None:
        bmark = tmp_path / "word-counter"
        shutil.copytree(MOCK_BENCHMARK, bmark)
        out = tmp_path / "out"
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            result = ClaudeBackend("claude-opus-4").run(bmark, out)
        assert result.benchmark == "word-counter"

    def test_benchmark_files_copied_to_output_dir(self, tmp_path: Path) -> None:
        out = tmp_path / "out"
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(0), _make_proc(0)]
            ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, out)
        assert (out / "benchmark.yaml").is_file()
        assert (out / ".harness-config").is_file()

    def test_test_output_parsed_from_test_cmd(self, tmp_path: Path) -> None:
        """Test output from TEST_CMD re-run is parsed into RunResult."""
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [
                _make_proc(0),
                _make_proc(0, stdout="7 passed in 0.5s"),
            ]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert result.test_total == 7
        assert result.test_passed == 7

    def test_timeout_error_mentions_seconds(self, tmp_path: Path) -> None:
        """Timeout message includes the configured timeout value."""
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [
                subprocess.TimeoutExpired(cmd=["bash", "loop.sh"], timeout=300),
                _make_proc(0),
            ]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        # benchmark.yaml in mock_benchmark has timeout=300
        assert "300" in result.error  # type: ignore[index]

    def test_exit_code_in_error_message(self, tmp_path: Path) -> None:
        with patch("agent_eval.backends.claude.subprocess.run") as mock_run:
            mock_run.side_effect = [_make_proc(42), _make_proc(0)]
            result = ClaudeBackend("claude-opus-4").run(MOCK_BENCHMARK, tmp_path / "out")
        assert "42" in (result.error or "")
