"""MockBackend — deterministic backend that replays fixture harness output."""

from __future__ import annotations

import shutil
from pathlib import Path

from agent_eval.backends.base import AgentBackend
from agent_eval.metrics import compute_run_result
from agent_eval.models import RunResult
from agent_eval.parser import (
    parse_cost_log,
    parse_phase_log,
    parse_plan,
    parse_test_output,
)

# Default canned pytest output used when test_output.txt is absent from fixture_dir.
_DEFAULT_TEST_OUTPUT = "1 passed in 0.01s"


class MockBackend(AgentBackend):
    """Simulates a completed agent run using pre-built fixture files.

    On each call to run():
      1. Copies .harness-logs/, IMPLEMENTATION_PLAN.md, and progress.txt
         from fixture_dir into output_dir.
      2. Parses copied files through the standard pipeline.
      3. Returns a RunResult with build_success=True.

    Test output is sourced from fixture_dir/test_output.txt (pytest format).
    If that file is absent, a minimal canned string is used.
    """

    def __init__(self, fixture_dir: Path, agent_name: str = "mock-agent") -> None:
        self.fixture_dir = Path(fixture_dir)
        self.agent_name = agent_name

    def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy harness log directory
        src_logs = self.fixture_dir / ".harness-logs"
        dst_logs = output_dir / ".harness-logs"
        if src_logs.exists():
            if dst_logs.exists():
                shutil.rmtree(dst_logs)
            shutil.copytree(src_logs, dst_logs)

        # Copy plan and session log
        for filename in ("IMPLEMENTATION_PLAN.md", "progress.txt"):
            src = self.fixture_dir / filename
            if src.exists():
                shutil.copy2(src, output_dir / filename)

        # Parse the copied artifacts
        cost = parse_cost_log(dst_logs / "cost.log")
        plan = parse_plan(output_dir / "IMPLEMENTATION_PLAN.md")
        phase = parse_phase_log(dst_logs / "phase.log")

        # Test output: prefer fixture file, fall back to default canned string
        test_output_path = self.fixture_dir / "test_output.txt"
        test_output = (
            test_output_path.read_text()
            if test_output_path.exists()
            else _DEFAULT_TEST_OUTPUT
        )
        test = parse_test_output(test_output, "pytest")

        benchmark_name = Path(benchmark_dir).name

        return compute_run_result(
            cost=cost,
            plan=plan,
            phase=phase,
            test=test,
            build_success=True,
            agent=self.agent_name,
            benchmark=benchmark_name,
        )
