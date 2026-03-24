"""Tests for runner orchestrator: run_single, run_compare, run_suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from agent_eval.backends.base import AgentBackend
from agent_eval.backends.mock import MockBackend
from agent_eval.models import AgentRef, BenchmarkRef, RunResult, SuiteConfig
from agent_eval.runner import run_compare, run_single, run_suite

FIXTURES = Path(__file__).parent / "fixtures"
MOCK_BENCHMARK = FIXTURES / "mock_benchmark"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _BrokenBackend(AgentBackend):
    """Always raises — used to test error isolation."""

    def __init__(self, agent_name: str = "broken-agent") -> None:
        self.agent_name = agent_name

    def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:
        raise RuntimeError("simulated backend failure")


def _mock_factory(fixture_dir: Path) -> Callable[[str], AgentBackend]:
    """Return a backend_factory that creates MockBackend with the given fixture_dir."""
    return lambda name: MockBackend(fixture_dir, agent_name=name)


def _suite_config(output_dir: Path) -> SuiteConfig:
    """Minimal SuiteConfig with two benchmarks and two agents."""
    return SuiteConfig(
        benchmarks=[
            BenchmarkRef(path="benchmarks/alpha"),
            BenchmarkRef(path="benchmarks/beta"),
        ],
        agents=[
            AgentRef(name="agent-a"),
            AgentRef(name="agent-b"),
        ],
        output=str(output_dir),
        timeout=3600,
    )


# ---------------------------------------------------------------------------
# run_single
# ---------------------------------------------------------------------------


class TestRunSingle:
    def test_returns_run_result(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        assert isinstance(result, RunResult)

    def test_benchmark_name_from_dir(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        assert result.benchmark == "mock_benchmark"

    def test_agent_name_from_backend(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK, agent_name="my-agent")
        result = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        assert result.agent == "my-agent"

    def test_result_json_written(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        run_dir = tmp_path / "out" / "mock_benchmark" / "mock-agent"
        assert (run_dir / "result.json").is_file()

    def test_result_json_valid(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        run_dir = tmp_path / "out" / "mock_benchmark" / "mock-agent"
        data = json.loads((run_dir / "result.json").read_text())
        assert "agent" in data
        assert "benchmark" in data
        assert "success" in data

    def test_result_json_roundtrips(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        original = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        run_dir = tmp_path / "out" / "mock_benchmark" / "mock-agent"
        loaded = RunResult.from_dict(json.loads((run_dir / "result.json").read_text()))
        assert loaded.agent == original.agent
        assert loaded.benchmark == original.benchmark
        assert loaded.test_total == original.test_total
        assert loaded.success == original.success

    def test_directory_structure(self, tmp_path: Path) -> None:
        """run dir must be {output}/{benchmark_name}/{agent_name}/."""
        backend = MockBackend(MOCK_BENCHMARK, agent_name="claude-opus")
        run_single(MOCK_BENCHMARK, backend, tmp_path / "results")
        run_dir = tmp_path / "results" / "mock_benchmark" / "claude-opus"
        assert run_dir.is_dir()

    def test_output_dir_created_if_missing(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        nested = tmp_path / "deep" / "nested" / "out"
        run_single(MOCK_BENCHMARK, backend, nested)
        assert nested.is_dir()

    def test_success_field_correct(self, tmp_path: Path) -> None:
        backend = MockBackend(MOCK_BENCHMARK)
        result = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        # mock_benchmark fixture has 10 passed, build_success=True → success=True
        assert result.success is True

    def test_error_isolation_returns_error_result(self, tmp_path: Path) -> None:
        backend = _BrokenBackend()
        result = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        assert result.success is False
        assert result.error is not None
        assert "RuntimeError" in result.error

    def test_error_isolation_writes_result_json(self, tmp_path: Path) -> None:
        backend = _BrokenBackend()
        run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        run_dir = tmp_path / "out" / "mock_benchmark" / "broken-agent"
        assert (run_dir / "result.json").is_file()

    def test_error_result_json_has_error_field(self, tmp_path: Path) -> None:
        backend = _BrokenBackend()
        run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        run_dir = tmp_path / "out" / "mock_benchmark" / "broken-agent"
        data = json.loads((run_dir / "result.json").read_text())
        assert data["error"] is not None

    def test_idempotent_second_call(self, tmp_path: Path) -> None:
        """Running run_single twice on same benchmark/agent/output should not crash."""
        backend = MockBackend(MOCK_BENCHMARK)
        r1 = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        r2 = run_single(MOCK_BENCHMARK, backend, tmp_path / "out")
        assert r1.total_tokens_in == r2.total_tokens_in


# ---------------------------------------------------------------------------
# run_compare
# ---------------------------------------------------------------------------


class TestRunCompare:
    def test_returns_list_of_run_results(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="agent-a"),
            MockBackend(MOCK_BENCHMARK, agent_name="agent-b"),
        ]
        results = run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        assert isinstance(results, list)
        assert all(isinstance(r, RunResult) for r in results)

    def test_returns_n_results_for_n_agents(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="a"),
            MockBackend(MOCK_BENCHMARK, agent_name="b"),
            MockBackend(MOCK_BENCHMARK, agent_name="c"),
        ]
        results = run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        assert len(results) == 3

    def test_result_agents_match_backends(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="alpha"),
            MockBackend(MOCK_BENCHMARK, agent_name="beta"),
        ]
        results = run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        agent_names = [r.agent for r in results]
        assert "alpha" in agent_names
        assert "beta" in agent_names

    def test_all_same_benchmark(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="x"),
            MockBackend(MOCK_BENCHMARK, agent_name="y"),
        ]
        results = run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        assert all(r.benchmark == "mock_benchmark" for r in results)

    def test_result_json_written_per_agent(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="agent-a"),
            MockBackend(MOCK_BENCHMARK, agent_name="agent-b"),
        ]
        run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        assert (tmp_path / "out" / "mock_benchmark" / "agent-a" / "result.json").is_file()
        assert (tmp_path / "out" / "mock_benchmark" / "agent-b" / "result.json").is_file()

    def test_empty_agents_returns_empty_list(self, tmp_path: Path) -> None:
        results = run_compare(MOCK_BENCHMARK, [], tmp_path / "out")
        assert results == []

    def test_error_in_one_does_not_stop_others(self, tmp_path: Path) -> None:
        agents = [
            MockBackend(MOCK_BENCHMARK, agent_name="good"),
            _BrokenBackend(agent_name="bad"),
            MockBackend(MOCK_BENCHMARK, agent_name="also-good"),
        ]
        results = run_compare(MOCK_BENCHMARK, agents, tmp_path / "out")
        assert len(results) == 3
        good = [r for r in results if r.agent == "good"]
        bad = [r for r in results if r.agent == "bad"]
        also_good = [r for r in results if r.agent == "also-good"]
        assert good[0].success is True
        assert bad[0].success is False
        assert also_good[0].success is True


# ---------------------------------------------------------------------------
# run_suite
# ---------------------------------------------------------------------------


class TestRunSuite:
    def test_returns_list_of_run_results(self, tmp_path: Path) -> None:
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        assert isinstance(results, list)
        assert all(isinstance(r, RunResult) for r in results)

    def test_returns_benchmark_times_agent_count(self, tmp_path: Path) -> None:
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        # 2 benchmarks × 2 agents = 4 results
        assert len(results) == 4

    def test_benchmark_names_from_suite_config(self, tmp_path: Path) -> None:
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        benchmarks = {r.benchmark for r in results}
        assert "alpha" in benchmarks
        assert "beta" in benchmarks

    def test_agent_names_from_suite_config(self, tmp_path: Path) -> None:
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        agents = {r.agent for r in results}
        assert "agent-a" in agents
        assert "agent-b" in agents

    def test_all_combinations_present(self, tmp_path: Path) -> None:
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        combos = {(r.benchmark, r.agent) for r in results}
        assert ("alpha", "agent-a") in combos
        assert ("alpha", "agent-b") in combos
        assert ("beta", "agent-a") in combos
        assert ("beta", "agent-b") in combos

    def test_result_jsons_written(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "results"
        config = _suite_config(output_dir)
        run_suite(config, _mock_factory(MOCK_BENCHMARK))
        assert (output_dir / "alpha" / "agent-a" / "result.json").is_file()
        assert (output_dir / "alpha" / "agent-b" / "result.json").is_file()
        assert (output_dir / "beta" / "agent-a" / "result.json").is_file()
        assert (output_dir / "beta" / "agent-b" / "result.json").is_file()

    def test_benchmark_major_ordering(self, tmp_path: Path) -> None:
        """Results should come out benchmark-major, agent-minor."""
        config = _suite_config(tmp_path / "results")
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        benchmarks = [r.benchmark for r in results]
        # Both agent-a and agent-b for 'alpha' come before any 'beta'
        assert benchmarks.index("alpha") < benchmarks.index("beta")

    def test_error_isolation_in_suite(self, tmp_path: Path) -> None:
        """Broken backend for one agent should not abort the rest."""
        call_count = 0

        def mixed_factory(name: str) -> AgentBackend:
            nonlocal call_count
            call_count += 1
            if name == "agent-a":
                return _BrokenBackend(agent_name=name)
            return MockBackend(MOCK_BENCHMARK, agent_name=name)

        config = _suite_config(tmp_path / "results")
        results = run_suite(config, mixed_factory)
        assert len(results) == 4
        assert call_count == 4
        broken = [r for r in results if r.agent == "agent-a"]
        good = [r for r in results if r.agent == "agent-b"]
        assert all(r.success is False for r in broken)
        assert all(r.success is True for r in good)

    def test_empty_suite_returns_empty_list(self, tmp_path: Path) -> None:
        config = SuiteConfig(
            benchmarks=[],
            agents=[],
            output=str(tmp_path / "results"),
            timeout=3600,
        )
        results = run_suite(config, _mock_factory(MOCK_BENCHMARK))
        assert results == []

    def test_factory_called_once_per_agent_per_benchmark(self, tmp_path: Path) -> None:
        factory_calls: list[str] = []

        def tracking_factory(name: str) -> AgentBackend:
            factory_calls.append(name)
            return MockBackend(MOCK_BENCHMARK, agent_name=name)

        config = _suite_config(tmp_path / "results")
        run_suite(config, tracking_factory)
        # 2 benchmarks × 2 agents = 4 factory calls
        assert len(factory_calls) == 4
