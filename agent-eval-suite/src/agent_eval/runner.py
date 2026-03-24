"""Runner orchestrator — run_single, run_compare, run_suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from agent_eval.backends.base import AgentBackend
from agent_eval.models import RunResult, SuiteConfig


def run_single(
    benchmark_dir: Path | str,
    agent_backend: AgentBackend,
    output_dir: Path | str,
) -> RunResult:
    """Run one agent against one benchmark.

    Creates {output_dir}/{benchmark_name}/{agent_name}/ as the run directory,
    calls backend.run(benchmark_dir, run_dir), then writes result.json.

    Any exception from the backend is caught; an error RunResult is produced
    and still serialized to result.json so callers can collect partial results.
    """
    benchmark_dir = Path(benchmark_dir)
    output_dir = Path(output_dir)

    benchmark_name = benchmark_dir.name
    agent_name: str = getattr(agent_backend, "agent_name", type(agent_backend).__name__)
    run_dir = output_dir / benchmark_name / agent_name
    run_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = agent_backend.run(benchmark_dir, run_dir)
    except Exception as exc:  # noqa: BLE001
        result = RunResult(
            agent=agent_name,
            benchmark=benchmark_name,
            success=False,
            build_success=False,
            test_total=0,
            test_passed=0,
            test_pass_rate=0.0,
            total_iterations=0,
            total_time_seconds=0.0,
            error=f"{type(exc).__name__}: {exc}",
        )

    (run_dir / "result.json").write_text(json.dumps(result.to_dict(), indent=2))
    return result


def run_compare(
    benchmark_dir: Path | str,
    agents: list[AgentBackend],
    output_dir: Path | str,
) -> list[RunResult]:
    """Run multiple agents against the same benchmark sequentially.

    Returns one RunResult per backend, in the same order as agents.
    Errors in individual runs are captured (not propagated) by run_single.
    """
    benchmark_dir = Path(benchmark_dir)
    output_dir = Path(output_dir)
    return [run_single(benchmark_dir, backend, output_dir) for backend in agents]


def run_suite(
    suite_config: SuiteConfig,
    backend_factory: Callable[[str], AgentBackend],
) -> list[RunResult]:
    """Run every benchmark × agent combination defined in suite_config.

    Calls backend_factory(agent_name) for each agent in the suite.
    Results are collected in benchmark-major, agent-minor order.
    Errors in individual runs are captured (not propagated) by run_single.
    """
    output_dir = Path(suite_config.output)
    results: list[RunResult] = []
    for bench_ref in suite_config.benchmarks:
        benchmark_dir = Path(bench_ref.path)
        for agent_ref in suite_config.agents:
            backend = backend_factory(agent_ref.name)
            result = run_single(benchmark_dir, backend, output_dir)
            results.append(result)
    return results
