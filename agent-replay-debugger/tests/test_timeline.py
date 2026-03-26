"""Tests for src/agent_replay/timeline.py — Item 10: Timeline Builder.

Fixture-based integration tests use sample_project (from conftest.py).
The sample_project is a tmp_path that is NOT a git repository, so
parse_git_log returns [] and git-related status/commit tests use
synthetic project directories with monkeypatched subprocess.

Fixture data summary (from tests/fixtures/):
  cost.log  → 5 valid entries, 1 malformed:
      iter 1: socratic iter=1  09:00  model=opus   in=15  out=8500  cost=$0.6384
      iter 2: plan     iter=1  09:30  model=opus   in=10  out=9200  cost=$0.6903
      iter 3: build    iter=1  10:00  model=sonnet in=25  out=10000 cost=$0.1501
      iter 4: build    iter=2  10:30  model=sonnet in=20  out=9500  cost=$0.1426
      iter 5: build    iter=3  11:00  model=sonnet in=22  out=8000  cost=$0.1201

  phase.log → 7 valid events, 1 malformed:
      08:55  START       phase=socratic  (before all iterations — discarded)
      09:02  TRANSITION  from=socratic to=plan   → attached to iter #1
      09:35  TRANSITION  from=plan to=build      → attached to iter #2
      09:35:01 PARALLEL_START                    → attached to iter #2
      09:35:05 PARALLEL_DONE                     → attached to iter #2
      10:45  CIRCUIT_BREAKER phase=build         → attached to iter #4  → STUCK
      11:35  COMPLETE    phase=build             → attached to iter #5

  metrics.log → 3 valid entries, 1 malformed:
      10:00  error_count context=build value=3  → attached to iter #3
      10:30  error_count context=build value=5  → attached to iter #4
      11:00  error_count context=build value=0  → attached to iter #5

  progress.txt → 2 session blocks:
      10:15  "Item 1 - Data Models"             → attached to iter #3
      11:30  "Item 2 - Test Fixtures"           → attached to iter #5

  harness-state.json → read separately (not used by build_timeline directly)

Expected iteration statuses (no git commits since tmp_path is not a repo):
  #1  socratic/1  OK   (first iteration)
  #2  plan/1      FAIL (middle, no commits)
  #3  build/1     FAIL (middle, no commits)
  #4  build/2     STUCK (CIRCUIT_BREAKER event)
  #5  build/3     OK   (last iteration)
"""
from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest

from agent_replay.models import Iteration, PhaseEntry
from agent_replay.timeline import build_timeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _make_cost_line(
    ts: str, phase: str, it: int, model: str, inp: int, out: int,
    cost: str, cumulative: str, item: str = ""
) -> str:
    return (
        f"{ts} phase={phase} iter={it} model={model} "
        f"in={inp} out={out} cost=${cost} cumulative=${cumulative} item={item}"
    )


# ---------------------------------------------------------------------------
# Full integration: sample_project fixture
# ---------------------------------------------------------------------------

class TestBuildTimelineFromFixtures:
    def test_returns_five_iterations(self, sample_project: Path) -> None:
        """Fixture has 5 valid (phase, iter) groups → 5 iterations."""
        iters = build_timeline(sample_project)
        assert len(iters) == 5

    def test_global_numbers_are_sequential(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert [it.number for it in iters] == [1, 2, 3, 4, 5]

    def test_phases_in_order(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert [it.phase for it in iters] == [
            "socratic", "plan", "build", "build", "build"
        ]

    def test_cost_totals(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[0].cost_total == Decimal("0.6384")
        assert iters[1].cost_total == Decimal("0.6903")
        assert iters[2].cost_total == Decimal("0.1501")
        assert iters[3].cost_total == Decimal("0.1426")
        assert iters[4].cost_total == Decimal("0.1201")

    def test_tokens_in_out(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[0].tokens_in == 15
        assert iters[0].tokens_out == 8500
        assert iters[2].tokens_in == 25
        assert iters[2].tokens_out == 10000

    def test_status_first_is_ok(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[0].status == "OK"

    def test_status_middle_no_commits_is_fail(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[1].status == "FAIL"  # plan iter=1
        assert iters[2].status == "FAIL"  # build iter=1

    def test_status_circuit_breaker_is_stuck(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # CIRCUIT_BREAKER at 10:45 is in iter #4 (build iter=2, range 10:30–11:00)
        assert iters[3].status == "STUCK"

    def test_status_last_is_ok(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[4].status == "OK"

    def test_phase_events_attached_to_correct_iterations(
        self, sample_project: Path
    ) -> None:
        iters = build_timeline(sample_project)
        # TRANSITION(09:02) → iter #1 (socratic starts 09:00)
        iter1_phase_events = [
            ev for ev in iters[0].events
            if ev.event_type == "phase"
        ]
        assert len(iter1_phase_events) == 1
        assert isinstance(iter1_phase_events[0].data, PhaseEntry)
        assert iter1_phase_events[0].data.event_type == "TRANSITION"

    def test_three_phase_events_in_iter2(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # TRANSITION + PARALLEL_START + PARALLEL_DONE → iter #2 (plan, 09:30–10:00)
        iter2_phase_events = [
            ev for ev in iters[1].events if ev.event_type == "phase"
        ]
        assert len(iter2_phase_events) == 3

    def test_circuit_breaker_in_iter4(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        iter4_phase_events = [
            ev for ev in iters[3].events if ev.event_type == "phase"
        ]
        assert len(iter4_phase_events) == 1
        assert iter4_phase_events[0].data.event_type == "CIRCUIT_BREAKER"

    def test_start_event_before_all_iters_discarded(
        self, sample_project: Path
    ) -> None:
        # START at 08:55 is before socratic iter=1 (09:00) — should not appear
        iters = build_timeline(sample_project)
        all_phase_types = [
            ev.data.event_type
            for it in iters
            for ev in it.events
            if ev.event_type == "phase"
        ]
        assert "START" not in all_phase_types

    def test_metrics_attached_to_iter3(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # error_count at 10:00 → iter #3 (build iter=1, starts 10:00)
        iter3_metrics = [ev for ev in iters[2].events if ev.event_type == "metrics"]
        assert len(iter3_metrics) == 1

    def test_metrics_attached_to_iter4(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # error_count at 10:30 → iter #4 (build iter=2, starts 10:30)
        iter4_metrics = [ev for ev in iters[3].events if ev.event_type == "metrics"]
        assert len(iter4_metrics) == 1

    def test_metrics_attached_to_iter5(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        iter5_metrics = [ev for ev in iters[4].events if ev.event_type == "metrics"]
        assert len(iter5_metrics) == 1

    def test_items_done_iter3(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # Session block at 10:15 → iter #3 (build iter=1, range [10:00, 10:30))
        assert iters[2].items_done == ["Item 1 - Data Models"]

    def test_items_done_iter5(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # Session block at 11:30 → iter #5 (build iter=3, range [11:00, ∞))
        assert iters[4].items_done == ["Item 2 - Test Fixtures"]

    def test_items_done_empty_for_others(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        assert iters[0].items_done == []
        assert iters[1].items_done == []
        assert iters[3].items_done == []

    def test_duration_iter1(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # iter #1: cost(09:00) + TRANSITION(09:02) → 2 min
        assert iters[0].duration == timedelta(minutes=2)

    def test_duration_iter3(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # iter #3: cost(10:00) + metrics(10:00) + session(10:15) → 15 min
        assert iters[2].duration == timedelta(minutes=15)

    def test_duration_iter4(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        # iter #4: cost(10:30) + metrics(10:30) + CIRCUIT_BREAKER(10:45) → 15 min
        assert iters[3].duration == timedelta(minutes=15)

    def test_no_git_commits_in_sample_project(self, sample_project: Path) -> None:
        """sample_project is not a git repo → git_commits empty on all iters."""
        iters = build_timeline(sample_project)
        for it in iters:
            assert it.git_commits == []

    def test_all_events_have_correct_iteration_number(
        self, sample_project: Path
    ) -> None:
        iters = build_timeline(sample_project)
        for it in iters:
            for ev in it.events:
                assert ev.iteration == it.number

    def test_all_events_have_correct_phase(self, sample_project: Path) -> None:
        iters = build_timeline(sample_project)
        for it in iters:
            for ev in it.events:
                assert ev.phase == it.phase

    def test_returns_list_of_iteration_instances(
        self, sample_project: Path
    ) -> None:
        iters = build_timeline(sample_project)
        assert all(isinstance(it, Iteration) for it in iters)


# ---------------------------------------------------------------------------
# Empty / missing cost.log → empty session
# ---------------------------------------------------------------------------

class TestBuildTimelineEmptySession:
    def test_missing_cost_log_returns_empty(self, tmp_path: Path) -> None:
        (tmp_path / ".harness-logs").mkdir()
        assert build_timeline(tmp_path) == []

    def test_empty_cost_log_returns_empty(self, tmp_path: Path) -> None:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text("")
        assert build_timeline(tmp_path) == []

    def test_missing_harness_logs_dir_returns_empty(self, tmp_path: Path) -> None:
        # .harness-logs/ doesn't exist → cost.log missing → []
        assert build_timeline(tmp_path) == []

    def test_only_malformed_cost_log_returns_empty(self, tmp_path: Path) -> None:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text("this line is malformed\nanother bad line\n")
        assert build_timeline(tmp_path) == []


# ---------------------------------------------------------------------------
# Synthetic project: status assignment
# ---------------------------------------------------------------------------

class TestBuildTimelineStatus:
    def _make_project(
        self,
        tmp_path: Path,
        cost_lines: list[str],
        phase_lines: list[str] | None = None,
    ) -> Path:
        logs = tmp_path / ".harness-logs"
        logs.mkdir(exist_ok=True)
        (logs / "cost.log").write_text("\n".join(cost_lines) + "\n")
        if phase_lines is not None:
            (logs / "phase.log").write_text("\n".join(phase_lines) + "\n")
        return tmp_path

    def test_single_iteration_is_ok(self, tmp_path: Path) -> None:
        self._make_project(tmp_path, [
            _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                            "sonnet", 10, 100, "0.01", "0.01"),
        ])
        iters = build_timeline(tmp_path)
        assert len(iters) == 1
        assert iters[0].status == "OK"  # only iteration → is both first and last

    def test_first_iteration_ok_even_without_commits(self, tmp_path: Path) -> None:
        self._make_project(tmp_path, [
            _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                            "sonnet", 10, 100, "0.01", "0.01"),
            _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                            "sonnet", 10, 100, "0.01", "0.02"),
        ])
        iters = build_timeline(tmp_path)
        assert iters[0].status == "OK"

    def test_last_iteration_ok_even_without_commits(self, tmp_path: Path) -> None:
        self._make_project(tmp_path, [
            _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                            "sonnet", 10, 100, "0.01", "0.01"),
            _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                            "sonnet", 10, 100, "0.01", "0.02"),
        ])
        iters = build_timeline(tmp_path)
        assert iters[-1].status == "OK"

    def test_middle_iteration_without_commits_is_fail(self, tmp_path: Path) -> None:
        self._make_project(tmp_path, [
            _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                            "sonnet", 10, 100, "0.01", "0.01"),
            _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                            "sonnet", 10, 100, "0.01", "0.02"),
            _make_cost_line("2026-01-01T12:00:00+00:00", "build", 3,
                            "sonnet", 10, 100, "0.01", "0.03"),
        ])
        iters = build_timeline(tmp_path)
        assert iters[1].status == "FAIL"

    def test_circuit_breaker_makes_iteration_stuck(self, tmp_path: Path) -> None:
        self._make_project(
            tmp_path,
            cost_lines=[
                _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                                "sonnet", 10, 100, "0.01", "0.01"),
                _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                                "sonnet", 10, 100, "0.01", "0.02"),
                _make_cost_line("2026-01-01T12:00:00+00:00", "build", 3,
                                "sonnet", 10, 100, "0.01", "0.03"),
            ],
            phase_lines=[
                "2026-01-01T11:30:00+00:00 event=CIRCUIT_BREAKER Stuck 1 iteration, phase=build",
            ],
        )
        iters = build_timeline(tmp_path)
        # CIRCUIT_BREAKER at 11:30 → iter #2 (range [11:00, 12:00)) → STUCK
        assert iters[1].status == "STUCK"

    def test_abort_makes_iteration_stuck(self, tmp_path: Path) -> None:
        self._make_project(
            tmp_path,
            cost_lines=[
                _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                                "sonnet", 10, 100, "0.01", "0.01"),
                _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                                "sonnet", 10, 100, "0.01", "0.02"),
                _make_cost_line("2026-01-01T12:00:00+00:00", "build", 3,
                                "sonnet", 10, 100, "0.01", "0.03"),
            ],
            phase_lines=[
                "2026-01-01T11:30:00+00:00 event=ABORT reason=budget",
            ],
        )
        iters = build_timeline(tmp_path)
        assert iters[1].status == "STUCK"

    def test_stuck_takes_priority_over_fail(self, tmp_path: Path) -> None:
        """Middle iteration with CIRCUIT_BREAKER + no commits → STUCK not FAIL."""
        self._make_project(
            tmp_path,
            cost_lines=[
                _make_cost_line("2026-01-01T10:00:00+00:00", "build", 1,
                                "sonnet", 10, 100, "0.01", "0.01"),
                _make_cost_line("2026-01-01T11:00:00+00:00", "build", 2,
                                "sonnet", 10, 100, "0.01", "0.02"),
                _make_cost_line("2026-01-01T12:00:00+00:00", "build", 3,
                                "sonnet", 10, 100, "0.01", "0.03"),
            ],
            phase_lines=[
                "2026-01-01T11:30:00+00:00 event=CIRCUIT_BREAKER Stuck 1 iteration, phase=build",
            ],
        )
        iters = build_timeline(tmp_path)
        assert iters[1].status == "STUCK"  # not FAIL


# ---------------------------------------------------------------------------
# Git commit attachment
# ---------------------------------------------------------------------------

class TestBuildTimelineGitCommits:
    def _make_cost_project(self, tmp_path: Path) -> Path:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 10, 100, "0.10", "0.10",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T11:00:00+00:00", "build", 2,
                "sonnet", 10, 100, "0.10", "0.20",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T12:00:00+00:00", "build", 3,
                "sonnet", 10, 100, "0.10", "0.30",
            ) + "\n"
        )
        return tmp_path

    def test_commit_in_range_attached_to_correct_iter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = self._make_cost_project(tmp_path)

        # One commit at 11:30 → should land in iter #2 ([11:00, 12:00))
        fake_output = "abc123 2026-01-01T11:30:00+00:00 feat: some feature\n"

        def fake_run(args, **kwargs):  # noqa: ANN001, ANN202
            class R:
                returncode = 0
                stdout = fake_output
            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)

        iters = build_timeline(project)
        assert iters[1].git_commits[0].hash == "abc123"
        assert len(iters[0].git_commits) == 0
        assert len(iters[2].git_commits) == 0

    def test_commit_before_all_iters_discarded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = self._make_cost_project(tmp_path)

        # Commit at 09:00, before first iter start 10:00
        fake_output = "dead001 2026-01-01T09:00:00+00:00 old commit\n"

        def fake_run(args, **kwargs):  # noqa: ANN001, ANN202
            class R:
                returncode = 0
                stdout = fake_output
            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)

        iters = build_timeline(project)
        assert all(len(it.git_commits) == 0 for it in iters)

    def test_commit_on_iter_start_timestamp_goes_to_that_iter(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = self._make_cost_project(tmp_path)

        # Commit exactly at 11:00 — the start of iter #2
        fake_output = "aaa111 2026-01-01T11:00:00+00:00 feat: exact start\n"

        def fake_run(args, **kwargs):  # noqa: ANN001, ANN202
            class R:
                returncode = 0
                stdout = fake_output
            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)

        iters = build_timeline(project)
        # 11:00 >= 11:00 → idx=1 (0-based) → iter #2
        assert len(iters[1].git_commits) == 1
        assert iters[1].git_commits[0].hash == "aaa111"

    def test_middle_iter_with_commit_is_ok(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = self._make_cost_project(tmp_path)

        # Commit in iter #2 (middle) → status should be OK, not FAIL
        fake_output = "bbb222 2026-01-01T11:30:00+00:00 feat: committed\n"

        def fake_run(args, **kwargs):  # noqa: ANN001, ANN202
            class R:
                returncode = 0
                stdout = fake_output
            return R()

        monkeypatch.setattr(subprocess, "run", fake_run)

        iters = build_timeline(project)
        assert iters[1].status == "OK"  # has a commit → not FAIL


# ---------------------------------------------------------------------------
# Duration calculation
# ---------------------------------------------------------------------------

class TestBuildTimelineDuration:
    def test_single_event_duration_is_zero(self, tmp_path: Path) -> None:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 10, 100, "0.01", "0.01",
            ) + "\n"
        )
        iters = build_timeline(tmp_path)
        assert iters[0].duration == timedelta(0)

    def test_two_cost_entries_same_iter_duration(self, tmp_path: Path) -> None:
        """Multiple cost entries in one (phase, iter) → duration spans them."""
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        # Two lines with same (build, 1) — grouped into one iteration
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 10, 100, "0.01", "0.01",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T10:30:00+00:00", "build", 1,
                "sonnet", 10, 100, "0.01", "0.02",
            ) + "\n"
        )
        iters = build_timeline(tmp_path)
        assert len(iters) == 1  # both lines are same (phase, iter) → 1 group
        assert iters[0].duration == timedelta(minutes=30)


# ---------------------------------------------------------------------------
# Multiple cost entries per (phase, iter) group
# ---------------------------------------------------------------------------

class TestBuildTimelineCostGrouping:
    def test_same_phase_iter_grouped(self, tmp_path: Path) -> None:
        """Two cost entries with same (phase, iter) → one Iteration."""
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 5, 200, "0.02", "0.02",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T10:10:00+00:00", "build", 1,
                "sonnet", 3, 150, "0.01", "0.03",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T11:00:00+00:00", "build", 2,
                "sonnet", 10, 300, "0.03", "0.06",
            ) + "\n"
        )
        iters = build_timeline(tmp_path)
        assert len(iters) == 2

    def test_cost_total_sums_across_group(self, tmp_path: Path) -> None:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 5, 200, "0.02", "0.02",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T10:10:00+00:00", "build", 1,
                "sonnet", 3, 150, "0.01", "0.03",
            ) + "\n"
        )
        iters = build_timeline(tmp_path)
        assert iters[0].cost_total == Decimal("0.03")

    def test_tokens_sum_across_group(self, tmp_path: Path) -> None:
        logs = tmp_path / ".harness-logs"
        logs.mkdir()
        (logs / "cost.log").write_text(
            _make_cost_line(
                "2026-01-01T10:00:00+00:00", "build", 1,
                "sonnet", 5, 200, "0.02", "0.02",
            ) + "\n" +
            _make_cost_line(
                "2026-01-01T10:10:00+00:00", "build", 1,
                "sonnet", 3, 150, "0.01", "0.03",
            ) + "\n"
        )
        iters = build_timeline(tmp_path)
        assert iters[0].tokens_in == 8
        assert iters[0].tokens_out == 350
