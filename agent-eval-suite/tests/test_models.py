"""Tests for agent_eval.models."""

import json

from agent_eval.models import (
    AgentRef,
    BenchmarkConfig,
    BenchmarkRef,
    CostLogData,
    PhaseLogData,
    PlanData,
    RunResult,
    SuiteConfig,
    TestData,
)


# --- RunResult ---


def make_run_result(**kwargs: object) -> RunResult:
    defaults = dict(
        agent="claude",
        benchmark="word-counter",
        success=True,
        build_success=True,
        test_total=10,
        test_passed=10,
        test_pass_rate=1.0,
        total_iterations=5,
        total_time_seconds=300.0,
    )
    defaults.update(kwargs)
    return RunResult(**defaults)  # type: ignore[arg-type]


def test_run_result_creation_minimal() -> None:
    r = make_run_result()
    assert r.agent == "claude"
    assert r.benchmark == "word-counter"
    assert r.success is True
    assert r.build_success is True
    assert r.test_total == 10
    assert r.test_passed == 10
    assert r.test_pass_rate == 1.0
    assert r.total_iterations == 5
    assert r.total_time_seconds == 300.0


def test_run_result_default_fields() -> None:
    r = make_run_result()
    assert r.phase_times == {}
    assert r.total_tokens_in == 0
    assert r.total_tokens_out == 0
    assert r.estimated_cost == 0.0
    assert r.items_completed == 0
    assert r.items_total == 0
    assert r.stuck_count == 0
    assert r.circuit_breaker_count == 0
    assert r.error is None


def test_run_result_with_all_fields() -> None:
    r = RunResult(
        agent="sonnet",
        benchmark="employee-crud",
        success=False,
        build_success=True,
        test_total=20,
        test_passed=18,
        test_pass_rate=0.9,
        total_iterations=10,
        total_time_seconds=600.0,
        phase_times={"build": 200.0, "verify": 100.0},
        total_tokens_in=5000,
        total_tokens_out=15000,
        estimated_cost=1.23,
        items_completed=8,
        items_total=10,
        stuck_count=2,
        circuit_breaker_count=1,
        error="Timeout after 600s",
    )
    assert r.agent == "sonnet"
    assert r.phase_times == {"build": 200.0, "verify": 100.0}
    assert r.estimated_cost == 1.23
    assert r.error == "Timeout after 600s"


def test_to_dict_is_json_serializable() -> None:
    r = make_run_result(phase_times={"plan": 60.0, "build": 180.0}, estimated_cost=0.55)
    d = r.to_dict()
    # Should not raise
    json_str = json.dumps(d)
    assert json_str is not None


def test_to_dict_keys() -> None:
    r = make_run_result()
    d = r.to_dict()
    expected_keys = {
        "agent", "benchmark", "success", "build_success", "test_total",
        "test_passed", "test_pass_rate", "total_iterations", "total_time_seconds",
        "phase_times", "total_tokens_in", "total_tokens_out", "estimated_cost",
        "items_completed", "items_total", "stuck_count", "circuit_breaker_count",
        "error",
    }
    assert set(d.keys()) == expected_keys


def test_from_dict_round_trip() -> None:
    r = RunResult(
        agent="opus",
        benchmark="word-counter",
        success=True,
        build_success=True,
        test_total=15,
        test_passed=15,
        test_pass_rate=1.0,
        total_iterations=7,
        total_time_seconds=450.0,
        phase_times={"socratic": 30.0, "plan": 90.0, "build": 300.0},
        total_tokens_in=12000,
        total_tokens_out=40000,
        estimated_cost=2.75,
        items_completed=5,
        items_total=5,
        stuck_count=0,
        circuit_breaker_count=0,
        error=None,
    )
    restored = RunResult.from_dict(r.to_dict())
    assert restored.agent == r.agent
    assert restored.benchmark == r.benchmark
    assert restored.success == r.success
    assert restored.build_success == r.build_success
    assert restored.test_total == r.test_total
    assert restored.test_passed == r.test_passed
    assert restored.test_pass_rate == r.test_pass_rate
    assert restored.total_iterations == r.total_iterations
    assert restored.total_time_seconds == r.total_time_seconds
    assert restored.phase_times == r.phase_times
    assert restored.total_tokens_in == r.total_tokens_in
    assert restored.total_tokens_out == r.total_tokens_out
    assert restored.estimated_cost == r.estimated_cost
    assert restored.items_completed == r.items_completed
    assert restored.items_total == r.items_total
    assert restored.stuck_count == r.stuck_count
    assert restored.circuit_breaker_count == r.circuit_breaker_count
    assert restored.error == r.error


def test_from_dict_round_trip_with_error() -> None:
    r = make_run_result(success=False, build_success=False, error="Build failed")
    restored = RunResult.from_dict(r.to_dict())
    assert restored.success is False
    assert restored.error == "Build failed"


def test_from_dict_with_missing_optional_keys() -> None:
    """from_dict should handle dicts missing optional fields gracefully."""
    minimal = {
        "agent": "claude",
        "benchmark": "test-bench",
        "success": True,
        "build_success": True,
        "test_total": 5,
        "test_passed": 5,
        "test_pass_rate": 1.0,
        "total_iterations": 2,
        "total_time_seconds": 100.0,
    }
    r = RunResult.from_dict(minimal)
    assert r.phase_times == {}
    assert r.total_tokens_in == 0
    assert r.estimated_cost == 0.0
    assert r.error is None


# --- Success field semantics ---


def test_success_requires_build_success() -> None:
    """Callers are responsible for computing success; confirm it stores correctly."""
    # success=False when build failed
    r = make_run_result(success=False, build_success=False)
    assert r.success is False


def test_success_false_when_test_total_zero() -> None:
    r = make_run_result(success=False, test_total=0, test_passed=0, test_pass_rate=0.0)
    assert r.success is False


def test_success_false_when_tests_failed() -> None:
    r = make_run_result(success=False, test_total=10, test_passed=8, test_pass_rate=0.8)
    assert r.success is False


def test_success_true_all_conditions_met() -> None:
    r = make_run_result(success=True, build_success=True, test_total=10, test_passed=10, test_pass_rate=1.0)
    assert r.success is True


# --- BenchmarkConfig ---


def test_benchmark_config_creation() -> None:
    bc = BenchmarkConfig(
        name="word-counter",
        language="python",
        complexity="medium",
        expected_tests=20,
        expected_items=17,
        timeout=3600,
    )
    assert bc.name == "word-counter"
    assert bc.language == "python"
    assert bc.complexity == "medium"
    assert bc.expected_tests == 20
    assert bc.expected_items == 17
    assert bc.timeout == 3600


# --- BenchmarkRef / AgentRef / SuiteConfig ---


def test_benchmark_ref_defaults() -> None:
    br = BenchmarkRef(path="benchmarks/word-counter")
    assert br.path == "benchmarks/word-counter"
    assert br.timeout is None


def test_benchmark_ref_with_timeout() -> None:
    br = BenchmarkRef(path="benchmarks/employee-crud", timeout=7200)
    assert br.timeout == 7200


def test_agent_ref_defaults() -> None:
    ar = AgentRef(name="claude")
    assert ar.name == "claude"
    assert ar.model is None
    assert ar.extra_args is None


def test_agent_ref_with_all_fields() -> None:
    ar = AgentRef(name="claude-sonnet", model="sonnet", extra_args={"--flag": "value"})
    assert ar.model == "sonnet"
    assert ar.extra_args == {"--flag": "value"}


def test_suite_config_creation() -> None:
    sc = SuiteConfig(
        benchmarks=[BenchmarkRef(path="benchmarks/word-counter")],
        agents=[AgentRef(name="claude"), AgentRef(name="sonnet", model="sonnet")],
        output="results/",
        timeout=3600,
    )
    assert len(sc.benchmarks) == 1
    assert len(sc.agents) == 2
    assert sc.output == "results/"
    assert sc.timeout == 3600


# --- Parser intermediate types ---


def test_cost_log_data_defaults() -> None:
    c = CostLogData()
    assert c.total_tokens_in == 0
    assert c.total_tokens_out == 0
    assert c.estimated_cost == 0.0
    assert c.phase_times == {}
    assert c.total_iterations == 0
    assert c.total_time_seconds == 0.0


def test_plan_data_defaults() -> None:
    p = PlanData()
    assert p.items_completed == 0
    assert p.items_total == 0


def test_phase_log_data_defaults() -> None:
    pl = PhaseLogData()
    assert pl.circuit_breaker_count == 0
    assert pl.stuck_count == 0


def test_test_data_defaults() -> None:
    td = TestData()
    assert td.test_total == 0
    assert td.test_passed == 0
    assert td.test_failed == 0


def test_test_data_with_values() -> None:
    td = TestData(test_total=10, test_passed=8, test_failed=2)
    assert td.test_total == 10
    assert td.test_passed == 8
    assert td.test_failed == 2
