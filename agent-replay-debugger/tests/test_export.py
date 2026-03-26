"""Tests for export.py: export_json() JSON schema (Round 9).

Covers:
- Top-level wrapper fields: project, total_iterations, total_cost, total_duration
- Iteration fields: number, phase, status, cost_total, tokens_in, tokens_out,
  duration, items_done, events, git_commits
- Decimal serialized as strings
- datetime serialized as ISO 8601 strings
- timedelta serialized as strings
- Events serialized with correct type discriminator + fields for all 5 data types:
  CostEntry, PhaseEntry, GitCommit, SessionBlock, MetricsEntry
- Empty iterations list
- Pretty-printed output (indent=2)
- File created at output_path
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from agent_replay.export import export_json
from agent_replay.models import (
    CostEntry,
    GitCommit,
    Iteration,
    MetricsEntry,
    PhaseEntry,
    SessionBlock,
    TimelineEvent,
)

TS = datetime(2026, 3, 25, 10, 0, 0, tzinfo=timezone.utc)
TS2 = datetime(2026, 3, 25, 10, 5, 0, tzinfo=timezone.utc)


def _make_cost_entry(**kw) -> CostEntry:
    defaults = dict(
        timestamp=TS,
        phase="build",
        iter=1,
        model="opus",
        tokens_in=10,
        tokens_out=500,
        cost=Decimal("0.04"),
        cumulative=Decimal("0.04"),
        item="",
    )
    defaults.update(kw)
    return CostEntry(**defaults)


def _make_iteration(
    number: int = 1,
    phase: str = "build",
    status: str = "OK",
    cost: str = "1.00",
    events: list[TimelineEvent] | None = None,
    commits: list[GitCommit] | None = None,
) -> Iteration:
    it = Iteration(
        number=number,
        phase=phase,
        status=status,
        cost_total=Decimal(cost),
        tokens_in=10,
        tokens_out=500,
        duration=timedelta(minutes=2),
    )
    it.events = events or []
    it.git_commits = commits or []
    return it


# ---------------------------------------------------------------------------
# File creation
# ---------------------------------------------------------------------------


class TestFileCreation:
    def test_creates_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        export_json([], out)
        assert out.exists()

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        out.write_text("old content")
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["total_iterations"] == 0

    def test_pretty_printed(self, tmp_path: Path) -> None:
        out = tmp_path / "report.json"
        export_json([_make_iteration()], out)
        raw = out.read_text()
        assert "\n" in raw
        assert "  " in raw  # indent=2


# ---------------------------------------------------------------------------
# Top-level schema
# ---------------------------------------------------------------------------


class TestTopLevelSchema:
    def test_is_dict(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_required_keys_present(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        for key in ("project", "total_iterations", "total_cost", "total_duration", "iterations"):
            assert key in data, f"missing top-level key: {key}"

    def test_project_default_empty_string(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["project"] == ""

    def test_project_kwarg(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out, project="my-project")
        data = json.loads(out.read_text())
        assert data["project"] == "my-project"

    def test_total_iterations_zero(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["total_iterations"] == 0

    def test_total_iterations_count(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([_make_iteration(i) for i in range(1, 4)], out)
        data = json.loads(out.read_text())
        assert data["total_iterations"] == 3

    def test_total_cost_zero(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["total_cost"] == "0"

    def test_total_cost_sum(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(1, cost="1.5"), _make_iteration(2, cost="2.5")]
        out = tmp_path / "r.json"
        export_json(iterations, out)
        data = json.loads(out.read_text())
        assert data["total_cost"] == "4.0"

    def test_total_cost_is_string(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([_make_iteration(1, cost="0.123456789")], out)
        data = json.loads(out.read_text())
        assert isinstance(data["total_cost"], str)

    def test_total_duration_zero(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["total_duration"] == "0:00:00"

    def test_total_duration_is_string(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([_make_iteration()], out)
        data = json.loads(out.read_text())
        assert isinstance(data["total_duration"], str)

    def test_iterations_is_list(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert isinstance(data["iterations"], list)


# ---------------------------------------------------------------------------
# Iteration serialization
# ---------------------------------------------------------------------------


class TestIterationFields:
    def _load_first(self, tmp_path: Path, it: Iteration) -> dict:
        out = tmp_path / "r.json"
        export_json([it], out)
        return json.loads(out.read_text())["iterations"][0]

    def test_number(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(7))
        assert entry["number"] == 7

    def test_phase(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(1, phase="verify"))
        assert entry["phase"] == "verify"

    def test_status(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(1, status="STUCK"))
        assert entry["status"] == "STUCK"

    def test_cost_total_as_string(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(1, cost="3.14159"))
        assert entry["cost_total"] == "3.14159"
        assert isinstance(entry["cost_total"], str)

    def test_tokens_in_out(self, tmp_path: Path) -> None:
        it = _make_iteration(1)
        it.tokens_in = 42
        it.tokens_out = 999
        entry = self._load_first(tmp_path, it)
        assert entry["tokens_in"] == 42
        assert entry["tokens_out"] == 999

    def test_duration_as_string(self, tmp_path: Path) -> None:
        it = _make_iteration(1)
        it.duration = timedelta(hours=1, minutes=23)
        entry = self._load_first(tmp_path, it)
        assert isinstance(entry["duration"], str)
        assert "1:23" in entry["duration"]

    def test_items_done(self, tmp_path: Path) -> None:
        it = _make_iteration(1)
        it.items_done = ["Item 3 - Parser", "Item 4 - Formatter"]
        entry = self._load_first(tmp_path, it)
        assert entry["items_done"] == ["Item 3 - Parser", "Item 4 - Formatter"]

    def test_events_is_list(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(1))
        assert isinstance(entry["events"], list)

    def test_git_commits_is_list(self, tmp_path: Path) -> None:
        entry = self._load_first(tmp_path, _make_iteration(1))
        assert isinstance(entry["git_commits"], list)

    def test_git_commit_fields(self, tmp_path: Path) -> None:
        commit = GitCommit(hash="deadbeef1234", message="fix: crash", timestamp=TS)
        it = _make_iteration(1, commits=[commit])
        entry = self._load_first(tmp_path, it)
        c = entry["git_commits"][0]
        assert c["hash"] == "deadbeef1234"
        assert c["message"] == "fix: crash"
        assert "2026-03-25" in c["timestamp"]

    def test_git_commit_timestamp_iso8601(self, tmp_path: Path) -> None:
        commit = GitCommit(hash="abc", message="m", timestamp=TS)
        it = _make_iteration(1, commits=[commit])
        entry = self._load_first(tmp_path, it)
        ts = entry["git_commits"][0]["timestamp"]
        # Must round-trip via fromisoformat
        from datetime import datetime
        parsed = datetime.fromisoformat(ts)
        assert parsed == TS


# ---------------------------------------------------------------------------
# Event serialization — all 5 data types
# ---------------------------------------------------------------------------


def _make_tl_event(data, event_type: str = "cost") -> TimelineEvent:
    return TimelineEvent(
        timestamp=TS,
        event_type=event_type,
        phase="build",
        iteration=1,
        data=data,
    )


class TestEventSerialization:
    def _load_event(self, tmp_path: Path, event: TimelineEvent) -> dict:
        it = _make_iteration(1, events=[event])
        out = tmp_path / "r.json"
        export_json([it], out)
        return json.loads(out.read_text())["iterations"][0]["events"][0]

    def test_event_has_timestamp(self, tmp_path: Path) -> None:
        ev = _make_tl_event(_make_cost_entry())
        entry = self._load_event(tmp_path, ev)
        assert "2026-03-25" in entry["timestamp"]

    def test_event_has_event_type(self, tmp_path: Path) -> None:
        ev = _make_tl_event(_make_cost_entry(), event_type="cost")
        entry = self._load_event(tmp_path, ev)
        assert entry["event_type"] == "cost"

    def test_event_has_data(self, tmp_path: Path) -> None:
        ev = _make_tl_event(_make_cost_entry())
        entry = self._load_event(tmp_path, ev)
        assert "data" in entry

    # CostEntry
    def test_cost_entry_type_discriminator(self, tmp_path: Path) -> None:
        ev = _make_tl_event(_make_cost_entry())
        entry = self._load_event(tmp_path, ev)
        assert entry["data"]["type"] == "cost"

    def test_cost_entry_fields(self, tmp_path: Path) -> None:
        ce = _make_cost_entry(model="sonnet", tokens_in=15, tokens_out=800, item="3")
        ev = _make_tl_event(ce)
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["model"] == "sonnet"
        assert d["tokens_in"] == 15
        assert d["tokens_out"] == 800
        assert d["item"] == "3"

    def test_cost_entry_decimal_as_string(self, tmp_path: Path) -> None:
        ce = _make_cost_entry(cost=Decimal("0.12345"), cumulative=Decimal("1.99"))
        ev = _make_tl_event(ce)
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["cost"] == "0.12345"
        assert d["cumulative"] == "1.99"
        assert isinstance(d["cost"], str)

    def test_cost_entry_timestamp_iso(self, tmp_path: Path) -> None:
        ce = _make_cost_entry(timestamp=TS)
        ev = _make_tl_event(ce)
        entry = self._load_event(tmp_path, ev)
        from datetime import datetime
        parsed = datetime.fromisoformat(entry["data"]["timestamp"])
        assert parsed == TS

    # PhaseEntry
    def test_phase_entry_type_discriminator(self, tmp_path: Path) -> None:
        pe = PhaseEntry(timestamp=TS, event_type="TRANSITION", params={"from": "plan", "to": "build"})
        ev = _make_tl_event(pe, event_type="phase")
        entry = self._load_event(tmp_path, ev)
        assert entry["data"]["type"] == "phase"

    def test_phase_entry_fields(self, tmp_path: Path) -> None:
        pe = PhaseEntry(
            timestamp=TS,
            event_type="CIRCUIT_BREAKER",
            params={"phase": "build", "stuck": "3"},
        )
        ev = _make_tl_event(pe, event_type="phase")
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["event_type"] == "CIRCUIT_BREAKER"
        assert d["params"]["phase"] == "build"
        assert d["params"]["stuck"] == "3"

    # GitCommit as event data
    def test_git_commit_event_type_discriminator(self, tmp_path: Path) -> None:
        gc = GitCommit(hash="abc123", message="feat: x", timestamp=TS)
        ev = _make_tl_event(gc, event_type="commit")
        entry = self._load_event(tmp_path, ev)
        assert entry["data"]["type"] == "commit"

    def test_git_commit_event_fields(self, tmp_path: Path) -> None:
        gc = GitCommit(hash="abc123", message="feat: x", timestamp=TS)
        ev = _make_tl_event(gc, event_type="commit")
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["hash"] == "abc123"
        assert d["message"] == "feat: x"

    # SessionBlock
    def test_session_block_type_discriminator(self, tmp_path: Path) -> None:
        sb = SessionBlock(
            timestamp=TS,
            content="Completed: Item 1 - Data Models",
            items_completed=["Item 1 - Data Models"],
        )
        ev = _make_tl_event(sb, event_type="session")
        entry = self._load_event(tmp_path, ev)
        assert entry["data"]["type"] == "session"

    def test_session_block_fields(self, tmp_path: Path) -> None:
        sb = SessionBlock(
            timestamp=TS,
            content="some content",
            items_completed=["Item 5 - Parser"],
        )
        ev = _make_tl_event(sb, event_type="session")
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["items_completed"] == ["Item 5 - Parser"]

    # MetricsEntry
    def test_metrics_entry_type_discriminator(self, tmp_path: Path) -> None:
        me = MetricsEntry(
            timestamp=TS, metric="error_count", context="build", value="2", detail="timeout"
        )
        ev = _make_tl_event(me, event_type="metrics")
        entry = self._load_event(tmp_path, ev)
        assert entry["data"]["type"] == "metrics"

    def test_metrics_entry_fields(self, tmp_path: Path) -> None:
        me = MetricsEntry(
            timestamp=TS,
            metric="token_total",
            context="phase=build",
            value="9500",
            detail="",
        )
        ev = _make_tl_event(me, event_type="metrics")
        entry = self._load_event(tmp_path, ev)
        d = entry["data"]
        assert d["metric"] == "token_total"
        assert d["context"] == "phase=build"
        assert d["value"] == "9500"
        assert d["detail"] == ""


# ---------------------------------------------------------------------------
# Empty session
# ---------------------------------------------------------------------------


class TestEmptySession:
    def test_empty_iterations_list(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([], out)
        data = json.loads(out.read_text())
        assert data["iterations"] == []
        assert data["total_iterations"] == 0
        assert data["total_cost"] == "0"

    def test_iteration_with_no_events(self, tmp_path: Path) -> None:
        out = tmp_path / "r.json"
        export_json([_make_iteration(1)], out)
        data = json.loads(out.read_text())
        assert data["iterations"][0]["events"] == []
        assert data["iterations"][0]["git_commits"] == []


# ---------------------------------------------------------------------------
# Multiple iterations ordering preserved
# ---------------------------------------------------------------------------


class TestOrdering:
    def test_iteration_order_preserved(self, tmp_path: Path) -> None:
        iterations = [_make_iteration(i) for i in [3, 1, 2]]
        out = tmp_path / "r.json"
        export_json(iterations, out)
        data = json.loads(out.read_text())
        numbers = [it["number"] for it in data["iterations"]]
        assert numbers == [3, 1, 2]  # input order preserved, not sorted
