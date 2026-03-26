"""Tests for src/agent_replay/parsers.py — Items 3–8: log file parsers."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

import subprocess

from agent_replay.models import CostEntry, GitCommit, MetricsEntry, PhaseEntry, PlanItem, SessionBlock
from agent_replay.parsers import parse_cost_log, parse_git_log, parse_harness_state, parse_metrics_log, parse_phase_log, parse_plan, parse_progress


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


# ---------------------------------------------------------------------------
# Happy-path: fixture file
# ---------------------------------------------------------------------------

class TestParseCostLogFixture:
    def test_returns_correct_count(self, sample_project: Path) -> None:
        """The fixture has 5 valid lines and 1 malformed line → 5 entries."""
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        assert len(entries) == 5

    def test_first_entry_fields(self, sample_project: Path) -> None:
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        e = entries[0]
        assert isinstance(e, CostEntry)
        assert e.phase == "socratic"
        assert e.iter == 1
        assert e.model == "opus"
        assert e.tokens_in == 15
        assert e.tokens_out == 8500
        assert e.item == ""

    def test_first_entry_cost_is_decimal(self, sample_project: Path) -> None:
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        e = entries[0]
        assert isinstance(e.cost, Decimal)
        assert isinstance(e.cumulative, Decimal)
        assert e.cost == Decimal("0.6384")
        assert e.cumulative == Decimal("0.6384")

    def test_entry_with_item_number(self, sample_project: Path) -> None:
        """Third entry has item=1."""
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        e = entries[2]
        assert e.item == "1"
        assert e.phase == "build"
        assert e.iter == 1

    def test_last_entry_item_number(self, sample_project: Path) -> None:
        """Last entry has item=2."""
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        e = entries[-1]
        assert e.item == "2"

    def test_timestamps_are_timezone_aware(self, sample_project: Path) -> None:
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        for e in entries:
            assert e.timestamp.tzinfo is not None

    def test_cumulative_increases_monotonically(self, sample_project: Path) -> None:
        entries = parse_cost_log(sample_project / ".harness-logs" / "cost.log")
        cumulatives = [e.cumulative for e in entries]
        for prev, curr in zip(cumulatives, cumulatives[1:]):
            assert curr >= prev


# ---------------------------------------------------------------------------
# Missing / empty file
# ---------------------------------------------------------------------------

class TestParseCostLogMissing:
    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_cost_log(tmp_path / "nonexistent" / "cost.log")
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "cost.log", "")
        assert parse_cost_log(p) == []

    def test_only_blank_lines_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "cost.log", "\n\n   \n")
        assert parse_cost_log(p) == []


# ---------------------------------------------------------------------------
# Malformed line handling
# ---------------------------------------------------------------------------

class TestParseCostLogMalformed:
    def test_malformed_line_skipped(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        content = (
            "2026-03-24T09:00:00+00:00 phase=build iter=1 model=opus in=10 out=9000 cost=$0.6753 cumulative=$0.6753 item=\n"
            "this line is completely wrong\n"
        )
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 1
        captured = capsys.readouterr()
        assert "malformed" in captured.err

    def test_missing_field_skipped(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        # Missing item= at end
        content = "2026-03-24T09:00:00+00:00 phase=build iter=1 model=opus in=10 out=9000 cost=$0.6753 cumulative=$0.6753\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 0
        assert "malformed" in capsys.readouterr().err

    def test_all_malformed_returns_empty_list(self, tmp_path: Path) -> None:
        content = "garbage\nmore garbage\n!!!\n"
        p = _write(tmp_path / "cost.log", content)
        assert parse_cost_log(p) == []

    def test_malformed_line_does_not_crash(self, tmp_path: Path) -> None:
        """Malformed lines should never raise exceptions."""
        p = _write(tmp_path / "cost.log", "bad line\n")
        result = parse_cost_log(p)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestParseCostLogEdgeCases:
    def test_item_empty_string(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 phase=socratic iter=1 model=opus in=15 out=8500 cost=$0.6384 cumulative=$0.6384 item=\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert entries[0].item == ""

    def test_item_digit_string(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 phase=build iter=1 model=sonnet in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=3\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert entries[0].item == "3"

    def test_item_is_str_not_int(self, tmp_path: Path) -> None:
        """item field must be stored as str, not int."""
        content = "2026-03-24T09:00:00+00:00 phase=build iter=1 model=sonnet in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=5\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert isinstance(entries[0].item, str)

    def test_decimal_precision_preserved(self, tmp_path: Path) -> None:
        """Decimal values must match the log exactly — no float rounding."""
        content = "2026-03-24T09:00:00+00:00 phase=build iter=1 model=sonnet in=20 out=9500 cost=$0.1426 cumulative=$1.6214 item=1\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert entries[0].cost == Decimal("0.1426")
        assert entries[0].cumulative == Decimal("1.6214")

    def test_multiple_phases_parsed(self, tmp_path: Path) -> None:
        """Lines from different phases are all parsed."""
        content = (
            "2026-03-24T09:00:00+00:00 phase=socratic iter=1 model=opus in=15 out=8500 cost=$0.6384 cumulative=$0.6384 item=\n"
            "2026-03-24T09:30:00+00:00 phase=plan iter=1 model=opus in=10 out=9200 cost=$0.6903 cumulative=$1.3287 item=\n"
            "2026-03-24T10:00:00+00:00 phase=build iter=1 model=sonnet in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=1\n"
        )
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 3
        phases = [e.phase for e in entries]
        assert phases == ["socratic", "plan", "build"]

    def test_multiple_iter_same_phase(self, tmp_path: Path) -> None:
        """Multiple iter values within the same phase are parsed correctly."""
        content = (
            "2026-03-24T10:00:00+00:00 phase=build iter=1 model=sonnet in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=1\n"
            "2026-03-24T10:30:00+00:00 phase=build iter=2 model=sonnet in=20 out=9500 cost=$0.1426 cumulative=$1.6214 item=1\n"
            "2026-03-24T11:00:00+00:00 phase=build iter=3 model=sonnet in=22 out=8000 cost=$0.1201 cumulative=$1.7415 item=2\n"
        )
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 3
        assert entries[0].iter == 1
        assert entries[1].iter == 2
        assert entries[2].iter == 3

    def test_valid_and_malformed_mixed(self, tmp_path: Path) -> None:
        """Valid lines before and after a malformed line are all returned."""
        content = (
            "2026-03-24T09:00:00+00:00 phase=socratic iter=1 model=opus in=15 out=8500 cost=$0.6384 cumulative=$0.6384 item=\n"
            "bad line here\n"
            "2026-03-24T10:00:00+00:00 phase=build iter=1 model=sonnet in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=1\n"
        )
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 2

    def test_single_line_file(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 phase=socratic iter=1 model=opus in=15 out=8500 cost=$0.6384 cumulative=$0.6384 item=\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert len(entries) == 1

    def test_model_field_preserved(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 phase=build iter=1 model=claude-sonnet-4-6 in=25 out=10000 cost=$0.1501 cumulative=$1.4788 item=1\n"
        p = _write(tmp_path / "cost.log", content)
        entries = parse_cost_log(p)
        assert entries[0].model == "claude-sonnet-4-6"


# ===========================================================================
# Item 4: parse_phase_log
# ===========================================================================

# ---------------------------------------------------------------------------
# Happy-path: fixture file
# ---------------------------------------------------------------------------

class TestParsePhaseLogFixture:
    """Tests against tests/fixtures/phase.log (via sample_project)."""

    def test_returns_correct_count(self, sample_project: Path) -> None:
        """Fixture has 7 valid lines and 1 malformed → 7 entries."""
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        assert len(entries) == 7

    def test_all_entries_are_phase_entry_instances(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        for e in entries:
            assert isinstance(e, PhaseEntry)

    def test_first_event_is_start(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        assert entries[0].event_type == "START"

    def test_start_event_params(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        assert entries[0].params["phase"] == "socratic"
        assert entries[0].params["version"] == "v2"

    def test_transition_event_type(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        assert entries[1].event_type == "TRANSITION"

    def test_transition_params(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        e = entries[1]
        assert e.params["from"] == "socratic"
        assert e.params["to"] == "plan"
        assert e.params["iter"] == "1"

    def test_circuit_breaker_event_detected(self, sample_project: Path) -> None:
        """CIRCUIT_BREAKER event must appear in the parsed entries."""
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        event_types = [e.event_type for e in entries]
        assert "CIRCUIT_BREAKER" in event_types

    def test_circuit_breaker_phase_param(self, sample_project: Path) -> None:
        """phase=build must be extracted from CIRCUIT_BREAKER free-text line."""
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        cb = next(e for e in entries if e.event_type == "CIRCUIT_BREAKER")
        assert cb.params.get("phase") == "build"

    def test_parallel_start_params(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        ps = next(e for e in entries if e.event_type == "PARALLEL_START")
        assert ps.params["items"] == "2"
        assert ps.params["max"] == "3"

    def test_parallel_done_no_kv_params(self, sample_project: Path) -> None:
        """PARALLEL_DONE success — 'success' is free text, no key=value pairs."""
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        pd = next(e for e in entries if e.event_type == "PARALLEL_DONE")
        assert pd.params == {}

    def test_complete_event_present(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        event_types = [e.event_type for e in entries]
        assert "COMPLETE" in event_types

    def test_timestamps_are_timezone_aware(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        for e in entries:
            assert e.timestamp.tzinfo is not None

    def test_timestamps_chronological_order(self, sample_project: Path) -> None:
        entries = parse_phase_log(sample_project / ".harness-logs" / "phase.log")
        for prev, curr in zip(entries, entries[1:]):
            assert prev.timestamp <= curr.timestamp


# ---------------------------------------------------------------------------
# Missing / empty file
# ---------------------------------------------------------------------------

class TestParsePhaseLogMissing:
    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_phase_log(tmp_path / "nonexistent" / "phase.log")
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "phase.log", "")
        assert parse_phase_log(p) == []

    def test_only_blank_lines_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "phase.log", "\n\n   \n")
        assert parse_phase_log(p) == []


# ---------------------------------------------------------------------------
# Malformed line handling
# ---------------------------------------------------------------------------

class TestParsePhaseLogMalformed:
    def test_malformed_line_skipped(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        content = (
            "2026-03-24T09:00:00+00:00 event=START phase=build\n"
            "this line has no event field\n"
        )
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert len(entries) == 1

    def test_malformed_line_warning_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        content = "not a valid phase log line\n"
        p = _write(tmp_path / "phase.log", content)
        parse_phase_log(p)
        assert "malformed" in capsys.readouterr().err

    def test_all_malformed_returns_empty_list(self, tmp_path: Path) -> None:
        content = "garbage\nmore garbage\n!!!\n"
        p = _write(tmp_path / "phase.log", content)
        assert parse_phase_log(p) == []

    def test_malformed_line_does_not_crash(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "phase.log", "bad line\n")
        result = parse_phase_log(p)
        assert isinstance(result, list)

    def test_valid_and_malformed_mixed(self, tmp_path: Path) -> None:
        content = (
            "2026-03-24T09:00:00+00:00 event=START phase=socratic\n"
            "bad line here\n"
            "2026-03-24T10:00:00+00:00 event=COMPLETE phase=build\n"
        )
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestParsePhaseLogEdgeCases:
    def test_single_start_event(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 event=START phase=socratic version=v2\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert len(entries) == 1
        assert entries[0].event_type == "START"
        assert entries[0].params == {"phase": "socratic", "version": "v2"}

    def test_circuit_breaker_free_text_not_in_params(self, tmp_path: Path) -> None:
        """Free text 'Stuck 1 iteration,' must not appear as a param key."""
        content = "2026-03-24T10:45:00+00:00 event=CIRCUIT_BREAKER Stuck 1 iteration, phase=build\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert entries[0].params == {"phase": "build"}

    def test_event_type_preserved_exactly(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 event=PREDICT_FAILURE reason=cost\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert entries[0].event_type == "PREDICT_FAILURE"

    def test_params_empty_when_no_kv_pairs(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 event=PARALLEL_DONE success\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert entries[0].params == {}

    def test_params_is_dict(self, tmp_path: Path) -> None:
        content = "2026-03-24T09:00:00+00:00 event=START phase=plan\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert isinstance(entries[0].params, dict)

    def test_multiple_transitions_parsed(self, tmp_path: Path) -> None:
        content = (
            "2026-03-24T09:02:00+00:00 event=TRANSITION from=socratic to=plan iter=1\n"
            "2026-03-24T09:35:00+00:00 event=TRANSITION from=plan to=build iter=1\n"
            "2026-03-24T11:00:00+00:00 event=TRANSITION from=build to=build iter=2\n"
        )
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert len(entries) == 3
        assert all(e.event_type == "TRANSITION" for e in entries)

    def test_timestamp_parsed_correctly(self, tmp_path: Path) -> None:
        content = "2026-03-24T10:45:00+00:00 event=CIRCUIT_BREAKER phase=build\n"
        p = _write(tmp_path / "phase.log", content)
        entries = parse_phase_log(p)
        assert entries[0].timestamp == _ts("2026-03-24T10:45:00+00:00")


# ===========================================================================
# Item 5: parse_progress
# ===========================================================================

_PROGRESS_FIXTURE = """\
=== Harness initialized: 2026-03-24T08:50:00+00:00 ===
Project type: python-uv

=== Session 2026-03-24T10:15:00+00:00 ===
Completed: Item 1 - Data Models
Changes: Created models.py with all dataclasses
Why: Foundation for all parsers
Discovered: Cost.log uses raw token counts not thousands
Difficulty: S

=== Session 2026-03-24T11:30:00+00:00 ===
Completed: Item 2 - Test Fixtures
Changes: Created tests/fixtures/ directory with sample log files
Why: Enables all parser tests to use realistic data
Discovered: conftest.py sample_project fixture builds temp project dir
Difficulty: S
"""


# ---------------------------------------------------------------------------
# Happy-path: fixture file
# ---------------------------------------------------------------------------


class TestParseProgressFixture:
    """Tests against tests/fixtures/progress.txt (via sample_project)."""

    def test_returns_correct_block_count(self, sample_project: Path) -> None:
        """Fixture has 2 Session blocks (Harness initialized header is ignored)."""
        blocks = parse_progress(sample_project / "progress.txt")
        assert len(blocks) == 2

    def test_all_blocks_are_session_block_instances(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        for b in blocks:
            assert isinstance(b, SessionBlock)

    def test_first_block_timestamp(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        assert blocks[0].timestamp == _ts("2026-03-24T10:15:00+00:00")

    def test_second_block_timestamp(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        assert blocks[1].timestamp == _ts("2026-03-24T11:30:00+00:00")

    def test_first_block_items_completed(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        assert blocks[0].items_completed == ["Item 1 - Data Models"]

    def test_second_block_items_completed(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        assert blocks[1].items_completed == ["Item 2 - Test Fixtures"]

    def test_first_block_content_contains_changes(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        assert "Changes:" in blocks[0].content

    def test_timestamps_are_timezone_aware(self, sample_project: Path) -> None:
        blocks = parse_progress(sample_project / "progress.txt")
        for b in blocks:
            assert b.timestamp.tzinfo is not None

    def test_harness_initialized_header_not_in_blocks(self, sample_project: Path) -> None:
        """The '=== Harness initialized ===' preamble must be excluded."""
        blocks = parse_progress(sample_project / "progress.txt")
        for b in blocks:
            assert "Harness initialized" not in b.content


# ---------------------------------------------------------------------------
# Missing / empty file
# ---------------------------------------------------------------------------


class TestParseProgressMissing:
    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_progress(tmp_path / "nonexistent" / "progress.txt")
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "progress.txt", "")
        assert parse_progress(p) == []

    def test_only_blank_lines_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "progress.txt", "\n\n   \n")
        assert parse_progress(p) == []

    def test_only_harness_initialized_returns_empty_list(self, tmp_path: Path) -> None:
        content = "=== Harness initialized: 2026-03-24T08:50:00+00:00 ===\nProject type: python-uv\n"
        p = _write(tmp_path / "progress.txt", content)
        assert parse_progress(p) == []


# ---------------------------------------------------------------------------
# Parsing logic
# ---------------------------------------------------------------------------


class TestParseProgressBlocks:
    def test_single_session_block(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Completed: Item 1 - Some Feature\n"
            "Difficulty: S\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert len(blocks) == 1
        assert blocks[0].items_completed == ["Item 1 - Some Feature"]

    def test_multiple_completed_in_one_block(self, tmp_path: Path) -> None:
        """A block can list multiple Completed: lines."""
        content = (
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Completed: Item 1 - Alpha\n"
            "Completed: Item 2 - Beta\n"
            "Difficulty: M\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert blocks[0].items_completed == ["Item 1 - Alpha", "Item 2 - Beta"]

    def test_content_holds_full_block_text(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Completed: Item 3 - Parser\n"
            "Why: Because\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert "Why: Because" in blocks[0].content

    def test_no_completed_lines_gives_empty_list(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Changes: Nothing done yet.\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert blocks[0].items_completed == []

    def test_three_blocks_parsed(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T09:00:00+00:00 ===\n"
            "Completed: Item 1 - First\n"
            "\n"
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Completed: Item 2 - Second\n"
            "\n"
            "=== Session 2026-03-24T11:00:00+00:00 ===\n"
            "Completed: Item 3 - Third\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert len(blocks) == 3
        assert [b.items_completed[0] for b in blocks] == [
            "Item 1 - First",
            "Item 2 - Second",
            "Item 3 - Third",
        ]

    def test_blocks_chronological_order(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T09:00:00+00:00 ===\n"
            "Completed: Item 1 - A\n"
            "\n"
            "=== Session 2026-03-24T11:00:00+00:00 ===\n"
            "Completed: Item 2 - B\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert blocks[0].timestamp < blocks[1].timestamp

    def test_preamble_before_first_session_ignored(self, tmp_path: Path) -> None:
        """Text before the first === Session === header is not included in any block."""
        content = (
            "=== Harness initialized: 2026-03-24T08:00:00+00:00 ===\n"
            "Project type: python-uv\n"
            "\n"
            "=== Session 2026-03-24T09:00:00+00:00 ===\n"
            "Completed: Item 1 - Feature\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert len(blocks) == 1
        assert "Harness initialized" not in blocks[0].content

    def test_items_completed_is_list(self, tmp_path: Path) -> None:
        content = (
            "=== Session 2026-03-24T10:00:00+00:00 ===\n"
            "Completed: Item 1 - Thing\n"
        )
        p = _write(tmp_path / "progress.txt", content)
        blocks = parse_progress(p)
        assert isinstance(blocks[0].items_completed, list)


# ===========================================================================
# Item 6: parse_metrics_log
# ===========================================================================

# ---------------------------------------------------------------------------
# Happy-path: fixture file
# ---------------------------------------------------------------------------


class TestParseMetricsLogFixture:
    """Tests against tests/fixtures/metrics.log (via sample_project)."""

    def test_returns_correct_count(self, sample_project: Path) -> None:
        """Fixture has 3 valid lines and 1 malformed → 3 entries."""
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        assert len(entries) == 3

    def test_all_entries_are_metrics_entry_instances(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        for e in entries:
            assert isinstance(e, MetricsEntry)

    def test_first_entry_fields(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        e = entries[0]
        assert e.metric == "error_count"
        assert e.context == "build"
        assert e.value == "3"
        assert e.detail == "lint_errors"

    def test_second_entry_fields(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        e = entries[1]
        assert e.metric == "error_count"
        assert e.context == "build"
        assert e.value == "5"
        assert e.detail == "test_failures"

    def test_third_entry_detail(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        assert entries[2].detail == "all_clear"

    def test_timestamps_are_timezone_aware(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        for e in entries:
            assert e.timestamp.tzinfo is not None

    def test_timestamps_chronological_order(self, sample_project: Path) -> None:
        entries = parse_metrics_log(sample_project / ".harness-logs" / "metrics.log")
        for prev, curr in zip(entries, entries[1:]):
            assert prev.timestamp <= curr.timestamp


# ---------------------------------------------------------------------------
# Missing / empty file
# ---------------------------------------------------------------------------


class TestParseMetricsLogMissing:
    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_metrics_log(tmp_path / "nonexistent" / "metrics.log")
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "metrics.log", "")
        assert parse_metrics_log(p) == []

    def test_only_blank_lines_returns_empty_list(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "metrics.log", "\n\n   \n")
        assert parse_metrics_log(p) == []


# ---------------------------------------------------------------------------
# Malformed line handling
# ---------------------------------------------------------------------------


class TestParseMetricsLogMalformed:
    def test_malformed_line_skipped(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        content = (
            "2026-03-24T10:00:00+00:00 metric=error_count context=build value=3 detail=lint_errors\n"
            "this is not a valid metrics line\n"
        )
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert len(entries) == 1

    def test_malformed_line_warning_to_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        p = _write(tmp_path / "metrics.log", "bad line here\n")
        parse_metrics_log(p)
        assert "malformed" in capsys.readouterr().err

    def test_all_malformed_returns_empty_list(self, tmp_path: Path) -> None:
        content = "garbage\nmore garbage\n!!!\n"
        p = _write(tmp_path / "metrics.log", content)
        assert parse_metrics_log(p) == []

    def test_malformed_line_does_not_crash(self, tmp_path: Path) -> None:
        p = _write(tmp_path / "metrics.log", "bad line\n")
        result = parse_metrics_log(p)
        assert isinstance(result, list)

    def test_valid_and_malformed_mixed(self, tmp_path: Path) -> None:
        content = (
            "2026-03-24T09:00:00+00:00 metric=error_count context=build value=3 detail=lint_errors\n"
            "bad line here\n"
            "2026-03-24T10:00:00+00:00 metric=error_count context=build value=0 detail=all_clear\n"
        )
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestParseMetricsLogEdgeCases:
    def test_single_valid_line(self, tmp_path: Path) -> None:
        content = "2026-03-24T10:00:00+00:00 metric=error_count context=build value=0 detail=all_clear\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert len(entries) == 1

    def test_value_is_str(self, tmp_path: Path) -> None:
        """value field is stored as str (could be integer or other token)."""
        content = "2026-03-24T10:00:00+00:00 metric=error_count context=build value=42 detail=some_detail\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert isinstance(entries[0].value, str)
        assert entries[0].value == "42"

    def test_metric_field_preserved_exactly(self, tmp_path: Path) -> None:
        content = "2026-03-24T10:00:00+00:00 metric=token_usage context=plan value=8500 detail=output_tokens\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert entries[0].metric == "token_usage"

    def test_context_field_preserved(self, tmp_path: Path) -> None:
        content = "2026-03-24T10:00:00+00:00 metric=error_count context=socratic value=0 detail=none\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert entries[0].context == "socratic"

    def test_timestamp_parsed_correctly(self, tmp_path: Path) -> None:
        content = "2026-03-24T11:00:00+00:00 metric=error_count context=build value=0 detail=all_clear\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert entries[0].timestamp == _ts("2026-03-24T11:00:00+00:00")

    def test_multiple_distinct_metrics(self, tmp_path: Path) -> None:
        content = (
            "2026-03-24T09:00:00+00:00 metric=error_count context=build value=3 detail=lint_errors\n"
            "2026-03-24T09:30:00+00:00 metric=token_usage context=build value=9500 detail=output\n"
            "2026-03-24T10:00:00+00:00 metric=iteration_count context=build value=2 detail=done\n"
        )
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert len(entries) == 3
        metrics = [e.metric for e in entries]
        assert metrics == ["error_count", "token_usage", "iteration_count"]

    def test_missing_field_is_malformed(self, tmp_path: Path) -> None:
        """Line missing the 'detail' field must be treated as malformed."""
        content = "2026-03-24T10:00:00+00:00 metric=error_count context=build value=3\n"
        p = _write(tmp_path / "metrics.log", content)
        entries = parse_metrics_log(p)
        assert entries == []


# ===========================================================================
# Item 7: parse_harness_state
# ===========================================================================


class TestParseHarnessStateFixture:
    def test_returns_dict_for_valid_fixture(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert isinstance(state, dict)

    def test_phase_field_present(self, sample_project: Path) -> None:
        """Fixture uses 'phase', not 'current_phase' (clarity Round 2)."""
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert "phase" in state
        assert state["phase"] == "build"

    def test_iteration_field(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert state["iteration"] == 3

    def test_total_iteration_field(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert state["total_iteration"] == 5

    def test_stuck_count_field(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert state["stuck_count"] == 0

    def test_current_item_field(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert state["current_item"] == "2"

    def test_item_fail_count_field(self, sample_project: Path) -> None:
        state = parse_harness_state(sample_project / ".harness-logs" / "harness-state.json")
        assert state is not None
        assert state["item_fail_count"] == 1


class TestParseHarnessStateMissing:
    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        state = parse_harness_state(tmp_path / "no-such-file.json")
        assert state is None

    def test_returns_none_not_raises(self, tmp_path: Path) -> None:
        """Must not raise for a missing file."""
        result = parse_harness_state(tmp_path / "nonexistent.json")
        assert result is None


class TestParseHarnessStateInvalidJson:
    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "harness-state.json"
        p.write_text("{ not valid json }")
        assert parse_harness_state(p) is None

    def test_empty_file_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "harness-state.json"
        p.write_text("")
        assert parse_harness_state(p) is None

    def test_truncated_json_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "harness-state.json"
        p.write_text('{"phase":"build"')
        assert parse_harness_state(p) is None


class TestParseHarnessStateEdgeCases:
    def test_extra_fields_preserved(self, tmp_path: Path) -> None:
        """Unknown/extra fields in the JSON should pass through in the returned dict."""
        p = tmp_path / "harness-state.json"
        p.write_text('{"phase":"plan","iteration":1,"extra_future_field":"hello"}')
        state = parse_harness_state(p)
        assert state is not None
        assert state["extra_future_field"] == "hello"

    def test_minimal_valid_json_object(self, tmp_path: Path) -> None:
        """Any valid JSON object (even empty) should be returned as a dict."""
        p = tmp_path / "harness-state.json"
        p.write_text("{}")
        state = parse_harness_state(p)
        assert state == {}

    def test_json_array_returns_none(self, tmp_path: Path) -> None:
        """A JSON array (not an object) should return None — only dicts are valid state."""
        p = tmp_path / "harness-state.json"
        p.write_text('[{"phase":"build"}]')
        state = parse_harness_state(p)
        assert state is None

# ===========================================================================
# Item 8: parse_plan
# ===========================================================================

# Minimal plan fixture content matching tests/fixtures/IMPLEMENTATION_PLAN.md structure
_PLAN_FIXTURE_CONTENT = """\
# Implementation Plan
Generated: 2026-03-24T08:00:00+00:00
Total_Items: 5

## Item 1: Data Models
- status: DONE
- priority: P0
- complexity: S
- description: Define dataclasses

## Item 2: Test Fixtures
- status: DONE
- priority: P0
- complexity: S
- description: Create fixtures

## Item 3: Parsers
- status: TODO
- priority: P0
- complexity: M
- description: Implement parsers

## Item 4: Timeline Builder
- status: TODO
- priority: P0
- complexity: M
- description: Build timeline

## Item 5: TUI App
- status: TODO
- priority: P1
- complexity: L
- description: Textual TUI
"""


# ---------------------------------------------------------------------------
# Happy-path: fixture file
# ---------------------------------------------------------------------------


class TestParsePlanFixture:
    """Tests against tests/fixtures/IMPLEMENTATION_PLAN.md (via sample_project)."""

    def test_returns_correct_count(self, sample_project: Path) -> None:
        """Fixture has 5 Item headers → 5 plan items."""
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert len(items) == 5

    def test_all_entries_are_plan_item_instances(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        for item in items:
            assert isinstance(item, PlanItem)

    def test_first_item_number(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert items[0].number == 1

    def test_first_item_title(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert items[0].title == "Data Models"

    def test_first_item_status_done(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert items[0].status == "DONE"

    def test_first_item_priority(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert items[0].priority == "P0"

    def test_done_items_detected(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        done = [i for i in items if i.status == "DONE"]
        assert len(done) == 2

    def test_todo_items_detected(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        todo = [i for i in items if i.status == "TODO"]
        assert len(todo) == 3

    def test_item_numbers_sequential(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert [i.number for i in items] == [1, 2, 3, 4, 5]

    def test_last_item_priority_p1(self, sample_project: Path) -> None:
        items = parse_plan(sample_project / "IMPLEMENTATION_PLAN.md")
        assert items[-1].priority == "P1"


# ---------------------------------------------------------------------------
# Missing / empty file
# ---------------------------------------------------------------------------


class TestParsePlanMissing:
    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_plan(tmp_path / "nonexistent" / "IMPLEMENTATION_PLAN.md")
        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text("")
        assert parse_plan(p) == []

    def test_only_blank_lines_returns_empty_list(self, tmp_path: Path) -> None:
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text("\n\n   \n")
        assert parse_plan(p) == []

    def test_no_item_headers_returns_empty_list(self, tmp_path: Path) -> None:
        """Document with metadata but no ## Item headers → empty list."""
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text("# Implementation Plan\nGenerated: 2026-03-24T08:00:00\nTotal_Items: 0\n")
        assert parse_plan(p) == []


# ---------------------------------------------------------------------------
# Partial items (missing fields use defaults)
# ---------------------------------------------------------------------------


class TestParsePlanPartialItems:
    def test_item_without_status_defaults_to_todo(self, tmp_path: Path) -> None:
        """Items missing the - status: field should default to 'TODO'."""
        content = "## Item 1: My Feature\n- priority: P0\n- description: something\n"
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert len(items) == 1
        assert items[0].status == "TODO"

    def test_item_without_priority_defaults_to_p0(self, tmp_path: Path) -> None:
        """Items missing the - priority: field should default to 'P0'."""
        content = "## Item 1: My Feature\n- status: DONE\n- description: something\n"
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert len(items) == 1
        assert items[0].priority == "P0"

    def test_item_with_only_header_line(self, tmp_path: Path) -> None:
        """Header-only item (no field lines) still returns one item with defaults."""
        content = "## Item 1: Bare Item\n"
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert len(items) == 1
        assert items[0].number == 1
        assert items[0].title == "Bare Item"
        assert items[0].status == "TODO"
        assert items[0].priority == "P0"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestParsePlanEdgeCases:
    def test_single_item(self, tmp_path: Path) -> None:
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text("## Item 1: Only Item\n- status: IN_PROGRESS\n- priority: P2\n")
        items = parse_plan(p)
        assert len(items) == 1
        assert items[0].number == 1
        assert items[0].status == "IN_PROGRESS"
        assert items[0].priority == "P2"

    def test_status_values_preserved_exactly(self, tmp_path: Path) -> None:
        """DONE, TODO, IN_PROGRESS all preserved as-is."""
        content = (
            "## Item 1: A\n- status: DONE\n- priority: P0\n"
            "## Item 2: B\n- status: TODO\n- priority: P0\n"
            "## Item 3: C\n- status: IN_PROGRESS\n- priority: P0\n"
        )
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert [i.status for i in items] == ["DONE", "TODO", "IN_PROGRESS"]

    def test_priority_values_preserved(self, tmp_path: Path) -> None:
        content = (
            "## Item 1: A\n- status: DONE\n- priority: P0\n"
            "## Item 2: B\n- status: TODO\n- priority: P1\n"
            "## Item 3: C\n- status: TODO\n- priority: P2\n"
        )
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert [i.priority for i in items] == ["P0", "P1", "P2"]

    def test_non_item_headers_ignored(self, tmp_path: Path) -> None:
        """Lines like '# Title' or '### Sub' must not create items."""
        content = (
            "# Implementation Plan\n"
            "### Some Section\n"
            "## Item 1: Real Item\n"
            "- status: DONE\n- priority: P0\n"
        )
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert len(items) == 1

    def test_fields_after_next_header_belong_to_next_item(self, tmp_path: Path) -> None:
        """Fields that appear after the next ## Item header belong to the new item only."""
        content = (
            "## Item 1: First\n"
            "- status: DONE\n"
            "- priority: P0\n"
            "## Item 2: Second\n"
            "- status: TODO\n"
            "- priority: P1\n"
        )
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert items[0].status == "DONE"
        assert items[0].priority == "P0"
        assert items[1].status == "TODO"
        assert items[1].priority == "P1"

    def test_title_whitespace_stripped(self, tmp_path: Path) -> None:
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text("## Item 42:   Spaced Title   \n- status: TODO\n- priority: P0\n")
        items = parse_plan(p)
        assert items[0].title == "Spaced Title"

    def test_phase_1_complete_marker_does_not_break_parsing(self, tmp_path: Path) -> None:
        """The PHASE_1_COMPLETE line at end of file must not cause a crash."""
        content = (
            "## Item 1: Feature\n"
            "- status: DONE\n"
            "- priority: P0\n"
            "\nPHASE_1_COMPLETE\n"
        )
        p = tmp_path / "IMPLEMENTATION_PLAN.md"
        p.write_text(content)
        items = parse_plan(p)
        assert len(items) == 1


# ===========================================================================
# Item 9: parse_git_log
# ===========================================================================

# Fake git log stdout with 3 commits (newest first, as git log emits)
_GIT_LOG_OUTPUT = (
    "fcad64b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8 2026-03-25T01:00:00+09:00"
    " feat: Item 8 — IMPLEMENTATION_PLAN.md parser\n"
    "183a71d2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8 2026-03-25T00:00:00+09:00"
    " feat: Item 7 — harness-state.json parser\n"
    "68024cd2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8 2026-03-24T16:00:00+09:00"
    " feat: Item 6 — metrics.log parser\n"
)


class _FakeResult:
    """Minimal stand-in for subprocess.CompletedProcess."""

    def __init__(self, returncode: int, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


# ---------------------------------------------------------------------------
# Happy-path: mocked subprocess output
# ---------------------------------------------------------------------------


class TestParseGitLogMocked:
    def test_returns_correct_count(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 3

    def test_returns_list_type(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        result = parse_git_log(tmp_path)
        assert isinstance(result, list)

    def test_all_commits_are_gitcommit_instances(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        for c in commits:
            assert isinstance(c, GitCommit)

    def test_first_commit_hash(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        assert commits[0].hash == "fcad64b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"

    def test_first_commit_message(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        assert commits[0].message == "feat: Item 8 — IMPLEMENTATION_PLAN.md parser"

    def test_first_commit_timestamp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        assert commits[0].timestamp == _ts("2026-03-25T01:00:00+09:00")

    def test_timestamps_are_timezone_aware(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        for c in commits:
            assert c.timestamp.tzinfo is not None

    def test_message_preserves_spaces(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Commit message with multiple words and special chars must be kept intact."""
        stdout = "abc123 2026-03-25T01:00:00+09:00 fix: resolve the merge conflict in src/foo.py\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert commits[0].message == "fix: resolve the merge conflict in src/foo.py"

    def test_cwd_passed_as_project_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[dict] = []

        def fake_run(cmd: list, **kwargs):  # type: ignore[override]
            captured.append(kwargs)
            return _FakeResult(0, "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        parse_git_log(tmp_path)
        assert captured[0]["cwd"] == tmp_path

    def test_correct_format_flag_used(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: list[list] = []

        def fake_run(cmd: list, **kwargs):  # type: ignore[override]
            captured.append(cmd)
            return _FakeResult(0, "")

        monkeypatch.setattr(subprocess, "run", fake_run)
        parse_git_log(tmp_path)
        assert "--format=%H %aI %s" in captured[0]


# ---------------------------------------------------------------------------
# Empty / non-repo
# ---------------------------------------------------------------------------


class TestParseGitLogEmpty:
    def test_empty_log_returns_empty_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, ""))
        assert parse_git_log(tmp_path) == []

    def test_non_git_dir_returns_empty_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """git exits with returncode=128 for non-git directories."""
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(128, ""))
        assert parse_git_log(tmp_path) == []

    def test_any_nonzero_returncode_returns_empty_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(1, ""))
        assert parse_git_log(tmp_path) == []


# ---------------------------------------------------------------------------
# git not installed
# ---------------------------------------------------------------------------


class TestParseGitLogGitNotAvailable:
    def test_file_not_found_returns_empty_list(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_fnf(*a, **kw):
            raise FileNotFoundError("git not found")

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        assert parse_git_log(tmp_path) == []

    def test_does_not_raise_when_git_missing(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_fnf(*a, **kw):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", raise_fnf)
        result = parse_git_log(tmp_path)  # must not raise
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Malformed output lines
# ---------------------------------------------------------------------------


class TestParseGitLogMalformed:
    def test_malformed_line_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = (
            "fcad64b 2026-03-25T01:00:00+09:00 good commit message\n"
            "onlyone\n"  # only 1 token — malformed
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 1

    def test_malformed_line_warning_to_stderr(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        stdout = "onlyone\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        parse_git_log(tmp_path)
        assert "malformed" in capsys.readouterr().err

    def test_invalid_timestamp_line_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        stdout = "abc123 NOT-A-TIMESTAMP commit message\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert commits == []
        assert "parse error" in capsys.readouterr().err

    def test_empty_lines_skipped(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = "\n   \nabc123 2026-03-25T01:00:00+09:00 real commit\n\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 1

    def test_message_absent_gives_empty_string(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Lines with only hash + timestamp (no message part) yield message=''."""
        stdout = "abc123 2026-03-25T01:00:00+09:00\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 1
        assert commits[0].message == ""

    def test_valid_and_malformed_mixed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = (
            "abc1 2026-03-25T01:00:00+09:00 good\n"
            "bad\n"
            "abc2 2026-03-25T02:00:00+09:00 also good\n"
        )
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestParseGitLogEdgeCases:
    def test_single_commit(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        stdout = "abc123def456 2026-03-24T10:00:00+00:00 chore: init\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert len(commits) == 1
        assert commits[0].hash == "abc123def456"

    def test_message_with_colon_and_spaces(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Colons and extra spaces in commit messages must not confuse the parser."""
        stdout = "abc123 2026-03-24T10:00:00+00:00 fix: handle edge case: empty input\n"
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, stdout))
        commits = parse_git_log(tmp_path)
        assert commits[0].message == "fix: handle edge case: empty input"

    def test_third_commit_hash(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: _FakeResult(0, _GIT_LOG_OUTPUT))
        commits = parse_git_log(tmp_path)
        assert commits[2].hash == "68024cd2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
