"""Parsers for harness log files and test output."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from agent_eval.models import CostLogData, PhaseLogData, PlanData, TestData

# cost.log line format:
# TIMESTAMP phase=PHASE iter=N model=MODEL in=INPUT out=OUTPUT cost=$COST cumulative=$CUMULATIVE item=ITEM
_COST_LOG_RE = re.compile(
    r"^(\S+)"  # timestamp
    r"\s+phase=(\S+)"
    r"\s+iter=(\S+)"
    r"\s+model=(\S+)"
    r"\s+in=(\d+)"
    r"\s+out=(\d+)"
    r"\s+cost=\$([0-9.]+)"
    r"\s+cumulative=\$([0-9.]+)"
    r"\s+item=(\S*)"
)


def parse_cost_log(path: Path) -> CostLogData:
    """Parse .harness-logs/cost.log and return aggregated metrics."""
    if not path.exists():
        return CostLogData()

    lines: list[tuple[datetime, str, int, int, float]] = []  # (ts, phase, in, out, cumulative)

    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = _COST_LOG_RE.match(raw)
        if not m:
            continue
        ts_str, phase, _, _, tok_in, tok_out, _, cumulative, _ = m.groups()
        try:
            ts = datetime.fromisoformat(ts_str)
            lines.append((ts, phase, int(tok_in), int(tok_out), float(cumulative)))
        except ValueError:
            continue

    if not lines:
        return CostLogData()

    total_tokens_in = sum(r[2] for r in lines)
    total_tokens_out = sum(r[3] for r in lines)
    estimated_cost = lines[-1][4]
    total_iterations = len(lines)

    first_ts = lines[0][0]
    last_ts = lines[-1][0]
    total_time_seconds = (last_ts - first_ts).total_seconds()

    # phase_times: elapsed from first to last timestamp within each phase
    phase_buckets: dict[str, list[datetime]] = defaultdict(list)
    for ts, phase, _, _, _ in lines:
        phase_buckets[phase].append(ts)

    phase_times: dict[str, float] = {}
    for phase, timestamps in phase_buckets.items():
        phase_times[phase] = (max(timestamps) - min(timestamps)).total_seconds()

    return CostLogData(
        total_tokens_in=total_tokens_in,
        total_tokens_out=total_tokens_out,
        estimated_cost=estimated_cost,
        phase_times=phase_times,
        total_iterations=total_iterations,
        total_time_seconds=total_time_seconds,
    )


def parse_plan(path: Path) -> PlanData:
    """Parse IMPLEMENTATION_PLAN.md and return item counts.

    Counts '## Item' headers for items_total and '- status: DONE' lines
    for items_completed.
    """
    if not path.exists():
        return PlanData()

    text = path.read_text()
    items_total = len(re.findall(r"^## Item\b", text, re.MULTILINE))
    items_completed = len(re.findall(r"^- status: DONE", text, re.MULTILINE))
    return PlanData(items_completed=items_completed, items_total=items_total)


# Test output regexes
_PYTEST_PASSED = re.compile(r"\b(\d+)\s+passed\b")
_PYTEST_FAILED = re.compile(r"\b(\d+)\s+failed\b")
_PYTEST_ERROR = re.compile(r"\b(\d+)\s+error\b")
_MAVEN_SUMMARY = re.compile(
    r"Tests run:\s*(\d+),\s*Failures:\s*(\d+),\s*Errors:\s*(\d+),\s*Skipped:\s*(\d+)"
)


def parse_test_output(output: str, framework: str) -> TestData:
    """Parse test runner stdout and return pass/fail counts.

    Supported frameworks: 'pytest', 'maven'.
    Unrecognised frameworks or empty output return TestData(0, 0, 0).
    """
    if not output.strip():
        return TestData()

    if framework == "pytest":
        passed = int(m.group(1)) if (m := _PYTEST_PASSED.search(output)) else 0
        failed = int(m.group(1)) if (m := _PYTEST_FAILED.search(output)) else 0
        errors = int(m.group(1)) if (m := _PYTEST_ERROR.search(output)) else 0
        total = passed + failed + errors
        return TestData(test_total=total, test_passed=passed, test_failed=failed + errors)

    if framework == "maven":
        m = _MAVEN_SUMMARY.search(output)
        if not m:
            return TestData()
        run, failures, errors, _ = (int(x) for x in m.groups())
        failed = failures + errors
        passed = run - failed
        return TestData(test_total=run, test_passed=max(passed, 0), test_failed=failed)

    return TestData()


def parse_phase_log(path: Path) -> PhaseLogData:
    """Parse .harness-logs/phase.log and count circuit-breaker / stuck events."""
    if not path.exists():
        return PhaseLogData()

    circuit_breaker_count = 0
    stuck_count = 0
    for line in path.read_text().splitlines():
        if "event=CIRCUIT_BREAKER" in line:
            circuit_breaker_count += 1
        if "event=PREDICT_FAILURE" in line:
            stuck_count += 1

    return PhaseLogData(
        circuit_breaker_count=circuit_breaker_count,
        stuck_count=stuck_count,
    )
