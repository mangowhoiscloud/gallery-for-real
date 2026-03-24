"""Tests for phase.log and metrics.log parsers."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent_cost_analyzer.parser.phase_log import parse_metrics_log, parse_phase_log


# ---------------------------------------------------------------------------
# parse_phase_log tests
# ---------------------------------------------------------------------------


class TestParsePhaseLog:
    def test_parses_all_events(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        # Fixture has 6 non-blank lines
        assert len(events) == 6

    def test_event_types(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        event_names = [e.event for e in events]
        assert "START" in event_names
        assert "TRANSITION" in event_names
        assert "PARALLEL_START" in event_names
        assert "CIRCUIT_BREAKER" in event_names
        assert "PARALLEL_DONE" in event_names
        assert "COMPLETE" in event_names

    def test_start_metadata(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        start = next(e for e in events if e.event == "START")
        assert start.metadata["phase"] == "build"
        assert start.metadata["version"] == "v1.6.1"

    def test_transition_metadata(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        trans = next(e for e in events if e.event == "TRANSITION")
        assert trans.metadata["from"] == "socratic"
        assert trans.metadata["to"] == "plan"

    def test_parallel_start_metadata(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        pstart = next(e for e in events if e.event == "PARALLEL_START")
        assert pstart.metadata["phase"] == "build"
        assert pstart.metadata["workers"] == "4"

    def test_circuit_breaker_message(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        cb = next(e for e in events if e.event == "CIRCUIT_BREAKER")
        assert "message" in cb.metadata
        assert "Stuck 3 iterations" in cb.metadata["message"]

    def test_circuit_breaker_embedded_kv(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        cb = next(e for e in events if e.event == "CIRCUIT_BREAKER")
        # Embedded key=value pairs are also extracted
        assert cb.metadata["phase"] == "build"
        assert cb.metadata["model"] == "claude-opus-4-5"

    def test_complete_metadata(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        complete = next(e for e in events if e.event == "COMPLETE")
        assert complete.metadata["total_iter"] == "9"
        assert complete.metadata["cost"] == "$3.0590"

    def test_parallel_done_metadata(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        pdone = next(e for e in events if e.event == "PARALLEL_DONE")
        assert pdone.metadata["phase"] == "build"
        assert pdone.metadata["completed"] == "8"

    def test_timestamp_is_timezone_aware(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        for event in events:
            assert isinstance(event.timestamp, datetime)
            assert event.timestamp.tzinfo is not None

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_phase_log(tmp_path / "nonexistent.log")
        assert result == []

    def test_malformed_line_skipped(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        log_file = tmp_path / "phase.log"
        log_file.write_text(
            "2026-03-19T09:00:00+09:00 event=START phase=build version=v1.6.1\n"
            "this is totally garbage\n"
            "2026-03-19T10:00:00+09:00 event=COMPLETE total_iter=1 cost=$0.50\n"
        )
        with caplog.at_level(logging.WARNING):
            events = parse_phase_log(log_file)
        assert len(events) == 2
        assert any("malformed" in msg for msg in caplog.messages)

    def test_blank_lines_silently_skipped(self, tmp_path: Path) -> None:
        log_file = tmp_path / "phase.log"
        log_file.write_text(
            "\n"
            "2026-03-19T09:00:00+09:00 event=START phase=build version=v1.0\n"
            "\n"
        )
        events = parse_phase_log(log_file)
        assert len(events) == 1

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        log_file = tmp_path / "phase.log"
        log_file.write_text("")
        assert parse_phase_log(log_file) == []

    def test_event_order_preserved(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        expected_order = [
            "START", "TRANSITION", "PARALLEL_START",
            "CIRCUIT_BREAKER", "PARALLEL_DONE", "COMPLETE",
        ]
        assert [e.event for e in events] == expected_order

    def test_start_timestamp_value(self, phase_log_path: Path) -> None:
        events = parse_phase_log(phase_log_path)
        start = next(e for e in events if e.event == "START")
        # 2026-03-19T07:55:00+09:00 → UTC 2026-03-18T22:55:00Z
        utc_ts = start.timestamp.astimezone(timezone.utc)
        assert utc_ts.year == 2026
        assert utc_ts.month == 3
        assert utc_ts.day == 18
        assert utc_ts.hour == 22
        assert utc_ts.minute == 55

    def test_circuit_breaker_only_event(self, tmp_path: Path) -> None:
        """CIRCUIT_BREAKER with no message body — metadata should have no 'message' key."""
        log_file = tmp_path / "phase.log"
        log_file.write_text("2026-03-19T10:00:00Z event=CIRCUIT_BREAKER\n")
        events = parse_phase_log(log_file)
        assert len(events) == 1
        cb = events[0]
        assert cb.event == "CIRCUIT_BREAKER"
        assert "message" not in cb.metadata


# ---------------------------------------------------------------------------
# parse_metrics_log tests
# ---------------------------------------------------------------------------


class TestParseMetricsLog:
    def test_parses_all_entries(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        # Fixture has 6 non-blank lines
        assert len(entries) == 6

    def test_field_types(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        for entry in entries:
            assert isinstance(entry.timestamp, datetime)
            assert isinstance(entry.metric, str)
            assert isinstance(entry.context, str)
            assert isinstance(entry.value, int)
            assert isinstance(entry.detail, int)

    def test_first_entry_values(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        first = entries[0]
        assert first.metric == "error_count"
        assert first.context == "build_iter1"
        assert first.value == 2
        assert first.detail == 0

    def test_high_value_entry(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        # Entry for build_iter7: value=6 detail=3
        last = entries[-1]
        assert last.context == "build_iter7"
        assert last.value == 6
        assert last.detail == 3

    def test_all_metrics_are_error_count(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        assert all(e.metric == "error_count" for e in entries)

    def test_timestamps_are_timezone_aware(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        for entry in entries:
            assert entry.timestamp.tzinfo is not None

    def test_missing_file_returns_empty_list(self, tmp_path: Path) -> None:
        result = parse_metrics_log(tmp_path / "nonexistent.log")
        assert result == []

    def test_malformed_line_skipped(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        log_file = tmp_path / "metrics.log"
        log_file.write_text(
            "2026-03-19T10:00:00+09:00 metric=error_count context=build_iter1 value=2 detail=0\n"
            "not a valid line at all\n"
            "2026-03-19T11:00:00+09:00 metric=error_count context=build_iter2 value=1 detail=0\n"
        )
        with caplog.at_level(logging.WARNING):
            entries = parse_metrics_log(log_file)
        assert len(entries) == 2
        assert any("malformed" in msg for msg in caplog.messages)

    def test_blank_lines_silently_skipped(self, tmp_path: Path) -> None:
        log_file = tmp_path / "metrics.log"
        log_file.write_text(
            "\n"
            "2026-03-19T10:00:00+09:00 metric=error_count context=build_iter1 value=2 detail=0\n"
            "\n"
        )
        entries = parse_metrics_log(log_file)
        assert len(entries) == 1

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        log_file = tmp_path / "metrics.log"
        log_file.write_text("")
        assert parse_metrics_log(log_file) == []

    def test_order_preserved(self, metrics_log_path: Path) -> None:
        entries = parse_metrics_log(metrics_log_path)
        contexts = [e.context for e in entries]
        assert contexts == [
            "build_iter1", "build_iter2", "build_iter3",
            "build_iter5", "build_iter6", "build_iter7",
        ]

    def test_custom_metric_types(self, tmp_path: Path) -> None:
        log_file = tmp_path / "metrics.log"
        log_file.write_text(
            "2026-03-19T10:00:00Z metric=token_spike context=phase_build value=99 detail=1\n"
        )
        entries = parse_metrics_log(log_file)
        assert len(entries) == 1
        assert entries[0].metric == "token_spike"
        assert entries[0].value == 99
