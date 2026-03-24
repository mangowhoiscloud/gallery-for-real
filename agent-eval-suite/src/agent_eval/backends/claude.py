"""ClaudeBackend — runs loop.sh via subprocess and parses harness output."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from agent_eval.backends.base import AgentBackend
from agent_eval.config import load_benchmark_config, load_harness_config
from agent_eval.metrics import compute_run_result
from agent_eval.models import RunResult
from agent_eval.parser import (
    parse_cost_log,
    parse_phase_log,
    parse_plan,
    parse_test_output,
)

_DEFAULT_TIMEOUT = 3600  # 1 hour fallback if benchmark.yaml is absent
_TEST_CMD_TIMEOUT = 120  # max seconds for the post-run test re-execution


class ClaudeBackend(AgentBackend):
    """Runs the harness loop.sh script via subprocess against a benchmark.

    On each call to run():
      1. Copies benchmark_dir into output_dir via shutil.copytree.
      2. Sets OPUS_MODEL / SONNET_MODEL env vars from self.model.
      3. Executes "bash loop.sh" in output_dir with a timeout read from
         benchmark.yaml (falls back to 3600 s).
      4. Re-runs TEST_CMD (from .harness-config) to capture clean test output.
      5. Parses all harness artifacts and returns a RunResult.

    On timeout: error field is set to a descriptive message, build_success=False,
    and any partial harness artifacts are still parsed.
    On non-zero exit: error field captures the exit code, build_success=False.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        self.agent_name = f"claude:{model}"

    def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:
        benchmark_dir = Path(benchmark_dir)
        output_dir = Path(output_dir)

        # Copy benchmark into the isolated output directory
        shutil.copytree(benchmark_dir, output_dir, dirs_exist_ok=True)

        benchmark_name = benchmark_dir.name

        # Determine timeout from benchmark.yaml when present
        timeout: int = _DEFAULT_TIMEOUT
        benchmark_yaml = output_dir / "benchmark.yaml"
        if benchmark_yaml.exists():
            try:
                cfg = load_benchmark_config(benchmark_yaml)
                timeout = cfg.timeout
            except (ValueError, FileNotFoundError):
                pass

        # Build the subprocess environment
        env = os.environ.copy()
        env["OPUS_MODEL"] = self.model
        env["SONNET_MODEL"] = self.model

        # Run loop.sh
        error: str | None = None
        build_success = False
        try:
            proc = subprocess.run(
                ["bash", "loop.sh"],
                cwd=str(output_dir),
                env=env,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            build_success = proc.returncode == 0
            if proc.returncode != 0:
                error = f"loop.sh exited with code {proc.returncode}"
        except subprocess.TimeoutExpired:
            error = f"loop.sh timed out after {timeout}s"
            build_success = False

        # Re-run TEST_CMD to capture clean test output
        test_output = ""
        harness_config_path = output_dir / ".harness-config"
        if harness_config_path.exists():
            try:
                harness_cfg = load_harness_config(harness_config_path)
                test_cmd = harness_cfg.get("TEST_CMD", "")
                if test_cmd:
                    test_proc = subprocess.run(
                        test_cmd,
                        cwd=str(output_dir),
                        env=env,
                        timeout=_TEST_CMD_TIMEOUT,
                        capture_output=True,
                        text=True,
                        shell=True,
                    )
                    test_output = test_proc.stdout + test_proc.stderr
            except (subprocess.TimeoutExpired, OSError, ValueError):
                pass

        # Parse harness artifacts (tolerant — missing files return zeroed data)
        logs_dir = output_dir / ".harness-logs"
        cost = parse_cost_log(logs_dir / "cost.log")
        plan = parse_plan(output_dir / "IMPLEMENTATION_PLAN.md")
        phase = parse_phase_log(logs_dir / "phase.log")
        test = parse_test_output(test_output, "pytest")

        return compute_run_result(
            cost=cost,
            plan=plan,
            phase=phase,
            test=test,
            build_success=build_success,
            agent=self.agent_name,
            benchmark=benchmark_name,
            error=error,
        )
