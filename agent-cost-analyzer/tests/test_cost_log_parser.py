"""Tests for the cost.log parser."""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from agent_cost_analyzer.models import CostEntry
from agent_cost_analyzer.parser.cost_log import parse_cost_log


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Valid fixture parsing
# ---------------------------------------------------------------------------


class TestValidFixture:
    def test_entry_count(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        assert len(entries) == 11

    def test_all_entries_are_cost_entry(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        assert all(isinstance(e, CostEntry) for e in entries)

    def test_cost_is_decimal(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        for e in entries:
            assert isinstance(e.cost, Decimal), f"cost is {type(e.cost)}"
            assert isinstance(e.cumulative, Decimal), f"cumulative is {type(e.cumulative)}"

    def test_tokens_are_int(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        for e in entries:
            assert isinstance(e.input_tokens, int)
            assert isinstance(e.output_tokens, int)

    def test_timestamp_has_tzinfo(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        for e in entries:
            assert e.timestamp.tzinfo is not None

    def test_item_is_none_for_non_build_phases(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        non_build = [e for e in entries if e.phase != "build"]
        assert all(e.item is None for e in non_build)

    def test_item_is_int_for_build_phase(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        build = [e for e in entries if e.phase == "build"]
        assert all(isinstance(e.item, int) for e in build)

    def test_phases_present(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        phases = {e.phase for e in entries}
        assert phases == {"socratic", "plan", "build", "verify"}

    def test_specific_costs(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        assert entries[0].cost == Decimal("0.6257")
        assert entries[1].cost == Decimal("0.5914")

    def test_first_entry_values(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        e = entries[0]
        assert e.phase == "socratic"
        assert e.iteration == 1
        assert e.model == "claude-sonnet-4-5"
        assert e.input_tokens == 12563
        assert e.output_tokens == 8734
        assert e.item is None

    def test_build_item_numbers(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path)
        build = [e for e in entries if e.phase == "build"]
        items = [e.item for e in build]
        # items 1,2,3,4,5,5,5,5 per fixture
        assert items == [1, 2, 3, 4, 5, 5, 5, 5]


# ---------------------------------------------------------------------------
# Malformed fixture
# ---------------------------------------------------------------------------


class TestMalformedFixture:
    def test_valid_lines_still_parsed(self, malformed_cost_log_path: Path) -> None:
        entries = parse_cost_log(malformed_cost_log_path)
        # fixture has 3 valid lines (line 1, 3, 7 with item=) and 4 malformed/blank
        assert len(entries) == 3

    def test_malformed_lines_logged(
        self, malformed_cost_log_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="agent_cost_analyzer.parser.cost_log"):
            parse_cost_log(malformed_cost_log_path)
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        # expect warnings for: "completely malformed", "missing_fields", "not_a_number"
        assert len(warnings) >= 2

    def test_non_numeric_token_skipped(self, malformed_cost_log_path: Path) -> None:
        entries = parse_cost_log(malformed_cost_log_path)
        # line with in=not_a_number should be skipped (not present in valid entries)
        iter2_entries = [e for e in entries if e.phase == "build" and e.iteration == 2]
        assert len(iter2_entries) == 0


# ---------------------------------------------------------------------------
# Missing file
# ---------------------------------------------------------------------------


class TestMissingFile:
    def test_raises_file_not_found(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.log"
        with pytest.raises(FileNotFoundError):
            parse_cost_log(missing)

    def test_error_message_includes_path(self, tmp_path: Path) -> None:
        missing = tmp_path / "nonexistent.log"
        with pytest.raises(FileNotFoundError, match="nonexistent.log"):
            parse_cost_log(missing)


# ---------------------------------------------------------------------------
# Empty file
# ---------------------------------------------------------------------------


class TestEmptyFile:
    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        empty = tmp_path / "cost.log"
        empty.write_text("")
        result = parse_cost_log(empty)
        assert result == []

    def test_blank_lines_only_returns_empty_list(self, tmp_path: Path) -> None:
        blank = tmp_path / "cost.log"
        blank.write_text("\n\n\n")
        result = parse_cost_log(blank)
        assert result == []


# ---------------------------------------------------------------------------
# Date filtering
# ---------------------------------------------------------------------------


class TestDateFiltering:
    # NOTE: Fixture timestamps are +09:00. In UTC:
    # - Entry 1 (08:00+09:00) → 2026-03-18 UTC
    # - Entries 2-11 (09:00+09:00 through 18:00+09:00) → 2026-03-19 UTC
    # Date filtering uses UTC dates, so entry 1 is "2026-03-18" for filtering purposes.

    def test_after_includes_entries_on_that_utc_date(self, cost_log_path: Path) -> None:
        # after=2026-03-19: includes entries 2-11 (UTC date 2026-03-19); entry 1 (UTC 2026-03-18) excluded
        entries = parse_cost_log(cost_log_path, after=date(2026, 3, 19))
        assert len(entries) == 10

    def test_after_includes_all_when_date_is_early(self, cost_log_path: Path) -> None:
        # after=2026-03-18: all 11 entries included (earliest UTC date is 2026-03-18)
        entries = parse_cost_log(cost_log_path, after=date(2026, 3, 18))
        assert len(entries) == 11

    def test_after_excludes_all_when_date_is_late(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(cost_log_path, after=date(2026, 3, 20))
        assert len(entries) == 0

    def test_before_exclusive_excludes_entries_on_that_utc_date(self, cost_log_path: Path) -> None:
        # before=2026-03-19: only entry 1 (UTC 2026-03-18) is included
        entries = parse_cost_log(cost_log_path, before=date(2026, 3, 19))
        assert len(entries) == 1

    def test_before_includes_all_when_date_is_late(self, cost_log_path: Path) -> None:
        # before=2026-03-20: all 11 entries (UTC 2026-03-18 and 2026-03-19) are included
        entries = parse_cost_log(cost_log_path, before=date(2026, 3, 20))
        assert len(entries) == 11

    def test_after_and_before_range_utc(self, cost_log_path: Path) -> None:
        # 2026-03-19 <= UTC date < 2026-03-20 → entries 2-11 (10 entries)
        entries = parse_cost_log(
            cost_log_path,
            after=date(2026, 3, 19),
            before=date(2026, 3, 20),
        )
        assert len(entries) == 10

    def test_narrow_range_excludes_all(self, cost_log_path: Path) -> None:
        entries = parse_cost_log(
            cost_log_path,
            after=date(2026, 3, 20),
            before=date(2026, 3, 21),
        )
        assert len(entries) == 0


# ---------------------------------------------------------------------------
# Empty item field (item=) → None
# ---------------------------------------------------------------------------


class TestEmptyItemField:
    def test_empty_item_field_is_none(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.log"
        log.write_text(
            "2026-03-19T08:00:00+00:00 phase=plan iter=1 model=claude-sonnet-4-5"
            " in=100 out=200 cost=$0.01 cumulative=$0.01 item=\n"
        )
        entries = parse_cost_log(log)
        assert len(entries) == 1
        assert entries[0].item is None

    def test_numeric_item_field_is_int(self, tmp_path: Path) -> None:
        log = tmp_path / "cost.log"
        log.write_text(
            "2026-03-19T08:00:00+00:00 phase=build iter=3 model=claude-sonnet-4-5"
            " in=100 out=200 cost=$0.01 cumulative=$0.02 item=7\n"
        )
        entries = parse_cost_log(log)
        assert len(entries) == 1
        assert entries[0].item == 7
        assert isinstance(entries[0].item, int)
