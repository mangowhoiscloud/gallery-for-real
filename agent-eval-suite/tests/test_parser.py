"""Tests for parser.py — cost log, plan, test output, phase log parsers."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_eval.parser import parse_cost_log, parse_phase_log, parse_plan, parse_test_output

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Cost log parser
# ---------------------------------------------------------------------------


class TestCostLogParser:
    def test_parse_fixture(self) -> None:
        result = parse_cost_log(FIXTURES / "cost.log")
        assert result.total_tokens_in == 17700
        assert result.total_tokens_out == 64700
        assert result.estimated_cost == pytest.approx(2.4543)
        assert result.total_iterations == 7
        assert result.total_time_seconds == pytest.approx(1800.0)

    def test_phase_times_keys(self) -> None:
        result = parse_cost_log(FIXTURES / "cost.log")
        assert set(result.phase_times.keys()) == {"socratic", "plan", "build", "verify"}

    def test_phase_times_build_elapsed(self) -> None:
        result = parse_cost_log(FIXTURES / "cost.log")
        # build: 10:07:30 → 10:25:10 = 17 min 40 sec = 1060 s
        assert result.phase_times["build"] == pytest.approx(1060.0)

    def test_phase_times_single_entry_is_zero(self) -> None:
        result = parse_cost_log(FIXTURES / "cost.log")
        # socratic, plan, verify each appear once → 0.0 elapsed
        assert result.phase_times["socratic"] == pytest.approx(0.0)
        assert result.phase_times["plan"] == pytest.approx(0.0)
        assert result.phase_times["verify"] == pytest.approx(0.0)

    def test_missing_file_returns_zeros(self, tmp_path: Path) -> None:
        result = parse_cost_log(tmp_path / "nonexistent.log")
        assert result.total_tokens_in == 0
        assert result.total_tokens_out == 0
        assert result.estimated_cost == 0.0
        assert result.phase_times == {}
        assert result.total_iterations == 0
        assert result.total_time_seconds == 0.0

    def test_empty_file_returns_zeros(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.log"
        log.write_text("")
        result = parse_cost_log(log)
        assert result.total_iterations == 0
        assert result.estimated_cost == 0.0

    def test_malformed_lines_are_skipped(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.log"
        log.write_text(
            "garbage line\n"
            "2026-03-24T10:00:00+09:00 phase=build iter=1 model=sonnet in=500 out=1000 "
            "cost=$0.05 cumulative=$0.05 item=1\n"
            "another bad line\n"
        )
        result = parse_cost_log(log)
        assert result.total_iterations == 1
        assert result.total_tokens_in == 500
        assert result.total_tokens_out == 1000

    def test_single_line_file(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.log"
        log.write_text(
            "2026-03-24T10:00:00+09:00 phase=build iter=1 model=sonnet in=100 out=200 "
            "cost=$0.01 cumulative=$0.01 item=1\n"
        )
        result = parse_cost_log(log)
        assert result.total_iterations == 1
        assert result.total_time_seconds == pytest.approx(0.0)
        assert result.total_tokens_in == 100
        assert result.total_tokens_out == 200
        assert result.estimated_cost == pytest.approx(0.01)


# ---------------------------------------------------------------------------
# Implementation plan parser
# ---------------------------------------------------------------------------


class TestPlanParser:
    def test_parse_fixture(self) -> None:
        result = parse_plan(FIXTURES / "IMPLEMENTATION_PLAN.md")
        assert result.items_completed == 3
        assert result.items_total == 5

    def test_missing_file_returns_zeros(self, tmp_path: Path) -> None:
        result = parse_plan(tmp_path / "IMPLEMENTATION_PLAN.md")
        assert result.items_completed == 0
        assert result.items_total == 0

    def test_zero_items(self, tmp_path: Path) -> None:
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text("# Implementation Plan\nNo items yet.\n")
        result = parse_plan(plan)
        assert result.items_total == 0
        assert result.items_completed == 0

    def test_all_done(self, tmp_path: Path) -> None:
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text(
            "## Item 1: Foo\n- status: DONE\n\n## Item 2: Bar\n- status: DONE\n"
        )
        result = parse_plan(plan)
        assert result.items_total == 2
        assert result.items_completed == 2

    def test_none_done(self, tmp_path: Path) -> None:
        plan = tmp_path / "IMPLEMENTATION_PLAN.md"
        plan.write_text(
            "## Item 1: Foo\n- status: TODO\n\n## Item 2: Bar\n- status: TODO\n"
        )
        result = parse_plan(plan)
        assert result.items_total == 2
        assert result.items_completed == 0


# ---------------------------------------------------------------------------
# Test output parser
# ---------------------------------------------------------------------------


class TestTestOutputParser:
    def test_pytest_all_passed(self) -> None:
        output = (FIXTURES / "pytest_output.txt").read_text()
        result = parse_test_output(output, "pytest")
        assert result.test_total == 23
        assert result.test_passed == 23
        assert result.test_failed == 0

    def test_pytest_with_failures(self) -> None:
        output = (FIXTURES / "pytest_output_with_failures.txt").read_text()
        result = parse_test_output(output, "pytest")
        assert result.test_total == 23
        assert result.test_passed == 21
        assert result.test_failed == 2  # 1 failed + 1 error

    def test_maven_all_passed(self) -> None:
        output = (FIXTURES / "maven_output.txt").read_text()
        result = parse_test_output(output, "maven")
        assert result.test_total == 18
        assert result.test_passed == 18
        assert result.test_failed == 0

    def test_maven_with_failures(self) -> None:
        output = "Tests run: 10, Failures: 2, Errors: 1, Skipped: 0"
        result = parse_test_output(output, "maven")
        assert result.test_total == 10
        assert result.test_passed == 7
        assert result.test_failed == 3

    def test_empty_output_returns_zeros(self) -> None:
        result = parse_test_output("", "pytest")
        assert result.test_total == 0
        assert result.test_passed == 0
        assert result.test_failed == 0

    def test_no_summary_line_returns_zeros(self) -> None:
        result = parse_test_output("some random output with no summary", "pytest")
        assert result.test_total == 0

    def test_unknown_framework_returns_zeros(self) -> None:
        result = parse_test_output("23 passed in 1.0s", "gradle")
        assert result.test_total == 0

    def test_pytest_only_failures(self) -> None:
        output = "3 failed in 0.5s"
        result = parse_test_output(output, "pytest")
        assert result.test_total == 3
        assert result.test_passed == 0
        assert result.test_failed == 3

    def test_pytest_only_errors(self) -> None:
        output = "2 error in 0.3s"
        result = parse_test_output(output, "pytest")
        assert result.test_total == 2
        assert result.test_passed == 0
        assert result.test_failed == 2

    def test_whitespace_only_returns_zeros(self) -> None:
        result = parse_test_output("   \n\t  ", "pytest")
        assert result.test_total == 0


# ---------------------------------------------------------------------------
# Phase log parser
# ---------------------------------------------------------------------------


class TestPhaseLogParser:
    def test_parse_fixture(self) -> None:
        result = parse_phase_log(FIXTURES / "phase.log")
        assert result.circuit_breaker_count == 2
        assert result.stuck_count == 1

    def test_missing_file_returns_zeros(self, tmp_path: Path) -> None:
        result = parse_phase_log(tmp_path / "phase.log")
        assert result.circuit_breaker_count == 0
        assert result.stuck_count == 0

    def test_empty_file_returns_zeros(self, tmp_path: Path) -> None:
        log = tmp_path / "phase.log"
        log.write_text("")
        result = parse_phase_log(log)
        assert result.circuit_breaker_count == 0
        assert result.stuck_count == 0

    def test_no_matching_events(self, tmp_path: Path) -> None:
        log = tmp_path / "phase.log"
        log.write_text("2026-03-24T10:00:00+09:00 event=PHASE_START phase=build\n")
        result = parse_phase_log(log)
        assert result.circuit_breaker_count == 0
        assert result.stuck_count == 0

    def test_multiple_events(self, tmp_path: Path) -> None:
        log = tmp_path / "phase.log"
        log.write_text(
            "event=CIRCUIT_BREAKER\n"
            "event=CIRCUIT_BREAKER\n"
            "event=CIRCUIT_BREAKER\n"
            "event=PREDICT_FAILURE\n"
            "event=PREDICT_FAILURE\n"
        )
        result = parse_phase_log(log)
        assert result.circuit_breaker_count == 3
        assert result.stuck_count == 2
