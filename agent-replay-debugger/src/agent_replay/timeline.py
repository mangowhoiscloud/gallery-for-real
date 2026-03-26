"""Timeline builder — merges all parser outputs into a list of Iteration objects.

Clarity resolutions applied:
- Group by (phase, iter) from cost.log (Round 3)
- Assign global numbers chronologically (Round 3)
- STUCK from CIRCUIT_BREAKER/ABORT events, FAIL from zero commits (Round 6)
- duration = last_event - first_event (Round 13)
- Empty session (no cost.log entries) → return [] (Round 14)
- Git commits attached by timestamp range (Round 5)
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agent_replay.models import (
    Iteration,
    PhaseEntry,
    TimelineEvent,
)
from agent_replay.parsers import (
    parse_cost_log,
    parse_git_log,
    parse_metrics_log,
    parse_phase_log,
    parse_progress,
)

# Event types that mark an iteration as STUCK (per clarity Round 6)
_STUCK_EVENTS = frozenset({"CIRCUIT_BREAKER", "ABORT"})


def build_timeline(project_dir: Path) -> list[Iteration]:
    """Build a unified session timeline from all harness log files.

    Groups cost.log entries by (phase, iter) to form Iteration objects.
    Attaches phase events, git commits, metrics, and session blocks by
    timestamp proximity — each event is assigned to the iteration whose
    start timestamp is the latest one that does not exceed the event's
    timestamp. Events before the first iteration's start are discarded.

    Returns an empty list if cost.log has no parseable entries (empty
    session per clarity Round 14).
    """
    logs_dir = project_dir / ".harness-logs"

    cost_entries = parse_cost_log(logs_dir / "cost.log")
    phase_entries = parse_phase_log(logs_dir / "phase.log")
    metrics_entries = parse_metrics_log(logs_dir / "metrics.log")
    session_blocks = parse_progress(project_dir / "progress.txt")
    git_commits = parse_git_log(project_dir)

    if not cost_entries:
        return []

    # -----------------------------------------------------------------------
    # Step 1: Group cost entries by (phase, iter) in chronological order
    # -----------------------------------------------------------------------
    groups: dict[tuple[str, int], list] = {}
    group_order: list[tuple[str, int]] = []
    for entry in cost_entries:
        key = (entry.phase, entry.iter)
        if key not in groups:
            groups[key] = []
            group_order.append(key)
        groups[key].append(entry)

    # -----------------------------------------------------------------------
    # Step 2: Build Iteration objects with cost data
    # -----------------------------------------------------------------------
    iterations: list[Iteration] = []
    for global_num, key in enumerate(group_order, start=1):
        phase_name, _ = key
        entries = groups[key]
        it = Iteration(number=global_num, phase=phase_name)
        for ce in entries:
            it.cost_total += ce.cost
            it.tokens_in += ce.tokens_in
            it.tokens_out += ce.tokens_out
            it.events.append(
                TimelineEvent(
                    timestamp=ce.timestamp,
                    event_type="cost",
                    phase=phase_name,
                    iteration=global_num,
                    data=ce,
                )
            )
        iterations.append(it)

    # -----------------------------------------------------------------------
    # Step 3: Compute start timestamp for each iteration (min of cost events)
    # -----------------------------------------------------------------------
    iter_starts: list[datetime] = [
        min(ev.timestamp for ev in it.events) for it in iterations
    ]

    def _find_iter_idx(ts: datetime) -> int | None:
        """Return the index of the iteration this timestamp belongs to.

        Returns the index of the last iteration whose start <= ts.
        Returns None if ts precedes all iteration starts.
        """
        result: int | None = None
        for i, start in enumerate(iter_starts):
            if ts >= start:
                result = i
        return result

    # -----------------------------------------------------------------------
    # Step 4: Attach phase events
    # -----------------------------------------------------------------------
    for pe in phase_entries:
        idx = _find_iter_idx(pe.timestamp)
        if idx is None:
            continue
        it = iterations[idx]
        it.events.append(
            TimelineEvent(
                timestamp=pe.timestamp,
                event_type="phase",
                phase=it.phase,
                iteration=it.number,
                data=pe,
            )
        )

    # -----------------------------------------------------------------------
    # Step 5: Attach metrics events
    # -----------------------------------------------------------------------
    for me in metrics_entries:
        idx = _find_iter_idx(me.timestamp)
        if idx is None:
            continue
        it = iterations[idx]
        it.events.append(
            TimelineEvent(
                timestamp=me.timestamp,
                event_type="metrics",
                phase=it.phase,
                iteration=it.number,
                data=me,
            )
        )

    # -----------------------------------------------------------------------
    # Step 6: Attach git commits and populate git_commits list
    # -----------------------------------------------------------------------
    for commit in git_commits:
        idx = _find_iter_idx(commit.timestamp)
        if idx is None:
            continue
        it = iterations[idx]
        it.git_commits.append(commit)
        it.events.append(
            TimelineEvent(
                timestamp=commit.timestamp,
                event_type="commit",
                phase=it.phase,
                iteration=it.number,
                data=commit,
            )
        )

    # -----------------------------------------------------------------------
    # Step 7: Attach session blocks, extract items_done
    # -----------------------------------------------------------------------
    for sb in session_blocks:
        idx = _find_iter_idx(sb.timestamp)
        if idx is None:
            continue
        it = iterations[idx]
        it.items_done.extend(sb.items_completed)
        it.events.append(
            TimelineEvent(
                timestamp=sb.timestamp,
                event_type="session",
                phase=it.phase,
                iteration=it.number,
                data=sb,
            )
        )

    # -----------------------------------------------------------------------
    # Step 8: Assign status and compute duration per iteration
    # -----------------------------------------------------------------------
    last_idx = len(iterations) - 1
    for i, it in enumerate(iterations):
        # STUCK: any CIRCUIT_BREAKER or ABORT phase event in this iteration
        stuck = any(
            ev.event_type == "phase"
            and isinstance(ev.data, PhaseEntry)
            and ev.data.event_type in _STUCK_EVENTS
            for ev in it.events
        )
        if stuck:
            it.status = "STUCK"
        elif not it.git_commits and i != 0 and i != last_idx:
            # FAIL: no git commits produced, and not first or last iteration
            it.status = "FAIL"
        else:
            it.status = "OK"

        # Duration = last event timestamp − first event timestamp (Round 13)
        if len(it.events) > 1:
            timestamps = [ev.timestamp for ev in it.events]
            it.duration = max(timestamps) - min(timestamps)
        # Single-event iteration: duration stays at timedelta(0)

    return iterations
