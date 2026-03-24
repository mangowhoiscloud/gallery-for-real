"""Metrics computation for agent-eval-suite."""

from __future__ import annotations

from agent_eval.models import (
    CostLogData,
    PhaseLogData,
    PlanData,
    RunResult,
    TestData,
)


def compute_run_result(
    cost: CostLogData,
    plan: PlanData,
    phase: PhaseLogData,
    test: TestData,
    build_success: bool,
    agent: str,
    benchmark: str,
    error: str | None = None,
) -> RunResult:
    """Assemble a RunResult from parsed data and derived fields."""
    test_pass_rate = test.test_passed / test.test_total if test.test_total > 0 else 0.0
    success = (
        build_success
        and test.test_total > 0
        and test.test_passed == test.test_total
    )
    return RunResult(
        agent=agent,
        benchmark=benchmark,
        success=success,
        build_success=build_success,
        test_total=test.test_total,
        test_passed=test.test_passed,
        test_pass_rate=test_pass_rate,
        total_iterations=cost.total_iterations,
        total_time_seconds=cost.total_time_seconds,
        phase_times=cost.phase_times,
        total_tokens_in=cost.total_tokens_in,
        total_tokens_out=cost.total_tokens_out,
        estimated_cost=cost.estimated_cost,
        items_completed=plan.items_completed,
        items_total=plan.items_total,
        stuck_count=phase.stuck_count,
        circuit_breaker_count=phase.circuit_breaker_count,
        error=error,
    )


def normalize_scores(results: list[RunResult]) -> dict[str, dict[str, float]]:
    """Normalize 4-axis scores per agent to [0, 1].

    Axes:
      correctness — test_pass_rate (already in [0, 1])
      speed       — 1 - avg_time / max_avg_time  (higher is better)
      cost        — 1 - avg_cost / max_avg_cost   (lower cost is better)
      reliability — 1 - avg_cb / max_avg_cb       (fewer circuit breakers is better)
    """
    if not results:
        return {}

    # Aggregate per-agent averages
    agent_runs: dict[str, list[RunResult]] = {}
    for r in results:
        agent_runs.setdefault(r.agent, []).append(r)

    averages: dict[str, dict[str, float]] = {}
    for agent, runs in agent_runs.items():
        n = len(runs)
        averages[agent] = {
            "correctness": sum(r.test_pass_rate for r in runs) / n,
            "speed": sum(r.total_time_seconds for r in runs) / n,
            "cost": sum(r.estimated_cost for r in runs) / n,
            "reliability": sum(r.circuit_breaker_count for r in runs) / n,
        }

    max_time = max(v["speed"] for v in averages.values())
    max_cost = max(v["cost"] for v in averages.values())
    max_cb = max(v["reliability"] for v in averages.values())

    normalized: dict[str, dict[str, float]] = {}
    for agent, scores in averages.items():
        normalized[agent] = {
            "correctness": scores["correctness"],
            "speed": 1.0 - scores["speed"] / max_time if max_time > 0 else 1.0,
            "cost": 1.0 - scores["cost"] / max_cost if max_cost > 0 else 1.0,
            "reliability": 1.0 - scores["reliability"] / max_cb if max_cb > 0 else 1.0,
        }

    return normalized


def aggregate_results(results: list[RunResult]) -> dict[str, list[RunResult]]:
    """Group results by benchmark for multi-run comparison summaries."""
    grouped: dict[str, list[RunResult]] = {}
    for r in results:
        grouped.setdefault(r.benchmark, []).append(r)
    return grouped
