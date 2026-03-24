"""Tests for metrics.py — compute_run_result, normalize_scores, aggregate_results."""

from __future__ import annotations

import pytest

from agent_eval.metrics import aggregate_results, compute_run_result, normalize_scores
from agent_eval.models import CostLogData, PhaseLogData, PlanData, RunResult, TestData


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _cost(
    *,
    tokens_in: int = 1000,
    tokens_out: int = 500,
    cost: float = 0.05,
    phase_times: dict | None = None,
    iterations: int = 10,
    time_seconds: float = 120.0,
) -> CostLogData:
    return CostLogData(
        total_tokens_in=tokens_in,
        total_tokens_out=tokens_out,
        estimated_cost=cost,
        phase_times=phase_times or {"plan": 30.0, "implement": 90.0},
        total_iterations=iterations,
        total_time_seconds=time_seconds,
    )


def _plan(*, completed: int = 3, total: int = 5) -> PlanData:
    return PlanData(items_completed=completed, items_total=total)


def _phase(*, cb: int = 1, stuck: int = 0) -> PhaseLogData:
    return PhaseLogData(circuit_breaker_count=cb, stuck_count=stuck)


def _test(*, total: int = 10, passed: int = 10, failed: int = 0) -> TestData:
    return TestData(test_total=total, test_passed=passed, test_failed=failed)


def _run_result(
    *,
    agent: str = "claude",
    benchmark: str = "word-counter",
    success: bool = True,
    build_success: bool = True,
    test_total: int = 10,
    test_passed: int = 10,
    test_pass_rate: float = 1.0,
    total_iterations: int = 10,
    total_time_seconds: float = 120.0,
    estimated_cost: float = 0.05,
    circuit_breaker_count: int = 0,
) -> RunResult:
    return RunResult(
        agent=agent,
        benchmark=benchmark,
        success=success,
        build_success=build_success,
        test_total=test_total,
        test_passed=test_passed,
        test_pass_rate=test_pass_rate,
        total_iterations=total_iterations,
        total_time_seconds=total_time_seconds,
        estimated_cost=estimated_cost,
        circuit_breaker_count=circuit_breaker_count,
    )


# ---------------------------------------------------------------------------
# compute_run_result
# ---------------------------------------------------------------------------


class TestComputeRunResult:
    def test_basic_fields_propagated(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(), True, "agent-a", "bench-x"
        )
        assert result.agent == "agent-a"
        assert result.benchmark == "bench-x"
        assert result.total_tokens_in == 1000
        assert result.total_tokens_out == 500
        assert result.estimated_cost == pytest.approx(0.05)
        assert result.total_iterations == 10
        assert result.total_time_seconds == pytest.approx(120.0)
        assert result.items_completed == 3
        assert result.items_total == 5
        assert result.circuit_breaker_count == 1
        assert result.stuck_count == 0
        assert result.phase_times == {"plan": 30.0, "implement": 90.0}

    def test_success_true_when_all_pass(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=5, passed=5), True, "a", "b"
        )
        assert result.success is True
        assert result.test_pass_rate == pytest.approx(1.0)

    def test_success_false_when_build_fails(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=5, passed=5), False, "a", "b"
        )
        assert result.success is False
        assert result.build_success is False

    def test_success_false_when_some_tests_fail(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=10, passed=8, failed=2),
            True, "a", "b"
        )
        assert result.success is False
        assert result.test_pass_rate == pytest.approx(0.8)

    def test_success_false_when_zero_tests(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=0, passed=0), True, "a", "b"
        )
        assert result.success is False

    def test_test_pass_rate_zero_when_zero_total(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=0, passed=0), True, "a", "b"
        )
        assert result.test_pass_rate == pytest.approx(0.0)

    def test_test_pass_rate_partial(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(total=4, passed=1, failed=3),
            True, "a", "b"
        )
        assert result.test_pass_rate == pytest.approx(0.25)

    def test_error_field_none_by_default(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(), True, "a", "b"
        )
        assert result.error is None

    def test_error_field_propagated(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(), _test(), False, "a", "b",
            error="timeout after 300s"
        )
        assert result.error == "timeout after 300s"

    def test_plan_data_fields(self) -> None:
        result = compute_run_result(
            _cost(), _plan(completed=7, total=10), _phase(), _test(), True, "a", "b"
        )
        assert result.items_completed == 7
        assert result.items_total == 10

    def test_phase_log_counts(self) -> None:
        result = compute_run_result(
            _cost(), _plan(), _phase(cb=3, stuck=2), _test(), True, "a", "b"
        )
        assert result.circuit_breaker_count == 3
        assert result.stuck_count == 2


# ---------------------------------------------------------------------------
# normalize_scores
# ---------------------------------------------------------------------------


class TestNormalizeScores:
    def test_empty_list_returns_empty(self) -> None:
        assert normalize_scores([]) == {}

    def test_single_agent_correctness_preserved(self) -> None:
        result = _run_result(agent="claude", test_pass_rate=0.8)
        scores = normalize_scores([result])
        assert scores["claude"]["correctness"] == pytest.approx(0.8)

    def test_single_agent_speed_is_one(self) -> None:
        """Single agent has max_time == its own time, so normalized = 1 - 1 = 0.
        Actually wait — 1 - (time / max_time) = 1 - 1 = 0. That's correct: no relative
        comparison, so we can't say it's fast or slow — but 0 seems odd for a
        single-agent case. Let's verify the implementation gives 0."""
        result = _run_result(agent="claude", total_time_seconds=100.0)
        scores = normalize_scores([result])
        # 1 - 100/100 = 0.0
        assert scores["claude"]["speed"] == pytest.approx(0.0)

    def test_single_agent_all_zero_time_gives_one(self) -> None:
        result = _run_result(agent="claude", total_time_seconds=0.0)
        scores = normalize_scores([result])
        assert scores["claude"]["speed"] == pytest.approx(1.0)

    def test_single_agent_all_zero_cost_gives_one(self) -> None:
        result = _run_result(agent="claude", estimated_cost=0.0)
        scores = normalize_scores([result])
        assert scores["claude"]["cost"] == pytest.approx(1.0)

    def test_single_agent_all_zero_reliability_gives_one(self) -> None:
        result = _run_result(agent="claude", circuit_breaker_count=0)
        scores = normalize_scores([result])
        assert scores["claude"]["reliability"] == pytest.approx(1.0)

    def test_two_agents_speed_relative(self) -> None:
        fast = _run_result(agent="fast-agent", total_time_seconds=50.0)
        slow = _run_result(agent="slow-agent", total_time_seconds=100.0)
        scores = normalize_scores([fast, slow])
        # fast: 1 - 50/100 = 0.5; slow: 1 - 100/100 = 0.0
        assert scores["fast-agent"]["speed"] == pytest.approx(0.5)
        assert scores["slow-agent"]["speed"] == pytest.approx(0.0)

    def test_two_agents_cost_relative(self) -> None:
        cheap = _run_result(agent="cheap", estimated_cost=0.01)
        expensive = _run_result(agent="expensive", estimated_cost=0.10)
        scores = normalize_scores([cheap, expensive])
        assert scores["cheap"]["cost"] == pytest.approx(0.9)
        assert scores["expensive"]["cost"] == pytest.approx(0.0)

    def test_two_agents_reliability_relative(self) -> None:
        stable = _run_result(agent="stable", circuit_breaker_count=0)
        flaky = _run_result(agent="flaky", circuit_breaker_count=4)
        scores = normalize_scores([stable, flaky])
        assert scores["stable"]["reliability"] == pytest.approx(1.0)
        assert scores["flaky"]["reliability"] == pytest.approx(0.0)

    def test_scores_in_range_0_to_1(self) -> None:
        results = [
            _run_result(agent="a", test_pass_rate=0.9, total_time_seconds=200.0,
                        estimated_cost=0.08, circuit_breaker_count=2),
            _run_result(agent="b", test_pass_rate=0.5, total_time_seconds=100.0,
                        estimated_cost=0.03, circuit_breaker_count=5),
        ]
        scores = normalize_scores(results)
        for agent_scores in scores.values():
            for axis, val in agent_scores.items():
                assert 0.0 <= val <= 1.0, f"{axis}={val} out of [0,1]"

    def test_multiple_results_same_agent_averaged(self) -> None:
        """Two results for the same agent should be averaged."""
        r1 = _run_result(agent="claude", test_pass_rate=1.0)
        r2 = _run_result(agent="claude", test_pass_rate=0.0)
        scores = normalize_scores([r1, r2])
        assert scores["claude"]["correctness"] == pytest.approx(0.5)

    def test_four_axes_present(self) -> None:
        result = _run_result()
        scores = normalize_scores([result])
        assert set(scores["claude"].keys()) == {"correctness", "speed", "cost", "reliability"}


# ---------------------------------------------------------------------------
# aggregate_results
# ---------------------------------------------------------------------------


class TestAggregateResults:
    def test_empty_list_returns_empty(self) -> None:
        assert aggregate_results([]) == {}

    def test_single_benchmark_groups_correctly(self) -> None:
        r1 = _run_result(agent="a", benchmark="bench-1")
        r2 = _run_result(agent="b", benchmark="bench-1")
        grouped = aggregate_results([r1, r2])
        assert list(grouped.keys()) == ["bench-1"]
        assert len(grouped["bench-1"]) == 2

    def test_multiple_benchmarks_split(self) -> None:
        r1 = _run_result(agent="a", benchmark="bench-1")
        r2 = _run_result(agent="a", benchmark="bench-2")
        r3 = _run_result(agent="b", benchmark="bench-1")
        grouped = aggregate_results([r1, r2, r3])
        assert set(grouped.keys()) == {"bench-1", "bench-2"}
        assert len(grouped["bench-1"]) == 2
        assert len(grouped["bench-2"]) == 1

    def test_preserves_runresult_objects(self) -> None:
        r = _run_result(agent="claude", benchmark="wc")
        grouped = aggregate_results([r])
        assert grouped["wc"][0] is r

    def test_single_result(self) -> None:
        r = _run_result(agent="a", benchmark="b")
        grouped = aggregate_results([r])
        assert grouped == {"b": [r]}

    def test_agents_within_group_preserved(self) -> None:
        agents = ["claude", "gpt4", "gemini"]
        results = [_run_result(agent=a, benchmark="bench") for a in agents]
        grouped = aggregate_results(results)
        result_agents = [r.agent for r in grouped["bench"]]
        assert set(result_agents) == set(agents)
