"""Failure pattern detector for agent cost and phase log entries."""
from __future__ import annotations

import re

from agent_cost_analyzer.models import (
    CircuitBreakerEvent,
    CostEntry,
    FailurePatterns,
    PhaseEvent,
    SessionError,
    StuckEvent,
)

_STUCK_COUNT_RE = re.compile(r"Stuck\s+(\d+)\s+iterations?", re.IGNORECASE)


def detect_failures(
    cost_entries: list[CostEntry],
    phase_events: list[PhaseEvent],
    session_errors: list[SessionError] | None = None,
) -> FailurePatterns:
    """Detect failure patterns from cost entries, phase events, and session errors.

    Stuck events: extracted from CIRCUIT_BREAKER phase events (primary) or
    detected from 3+ consecutive cost entries with the same item (fallback).
    Build failure rate: fraction of build iterations where the next iteration
    retries the same item number (Clarity #9).
    """
    circuit_breakers = _extract_circuit_breakers(phase_events)

    if circuit_breakers:
        stuck_events = _stuck_from_circuit_breakers(circuit_breakers, cost_entries)
    else:
        stuck_events = _stuck_from_cost_entries(cost_entries)

    build_failure_rate = _compute_build_failure_rate(cost_entries)

    error_categories: dict[str, int] = {}
    if session_errors:
        for err in session_errors:
            error_categories[err.error_type] = (
                error_categories.get(err.error_type, 0) + 1
            )

    recovery_times = _compute_recovery_times(cost_entries, stuck_events)

    return FailurePatterns(
        stuck_events=stuck_events,
        circuit_breakers=circuit_breakers,
        build_failure_rate=build_failure_rate,
        error_categories=error_categories,
        recovery_times=recovery_times,
    )


def _extract_circuit_breakers(
    phase_events: list[PhaseEvent],
) -> list[CircuitBreakerEvent]:
    result = []
    for event in phase_events:
        if event.event == "CIRCUIT_BREAKER":
            message = event.metadata.get("message", "")
            metadata = {k: v for k, v in event.metadata.items() if k != "message"}
            result.append(
                CircuitBreakerEvent(
                    timestamp=event.timestamp,
                    message=message,
                    metadata=metadata,
                )
            )
    return result


def _stuck_from_circuit_breakers(
    circuit_breakers: list[CircuitBreakerEvent],
    cost_entries: list[CostEntry],
) -> list[StuckEvent]:
    build_entries = [
        e for e in cost_entries if e.phase == "build" and e.item is not None
    ]
    stuck_events = []
    for cb in circuit_breakers:
        count = _parse_stuck_count(cb.message)
        if count == 0:
            continue
        item = _find_stuck_item(cb, build_entries)
        if item is None:
            continue
        start_iter = _find_start_iteration(item, build_entries)
        stuck_events.append(StuckEvent(item=item, start_iteration=start_iter, count=count))
    return stuck_events


def _parse_stuck_count(message: str) -> int:
    m = _STUCK_COUNT_RE.search(message)
    if m:
        return int(m.group(1))
    return 0


def _find_stuck_item(
    cb: CircuitBreakerEvent,
    build_entries: list[CostEntry],
) -> int | None:
    """Return the item being processed at the time of the circuit breaker."""
    candidates = [e for e in build_entries if e.timestamp <= cb.timestamp]
    if candidates:
        return candidates[-1].item
    if build_entries:
        return build_entries[0].item
    return None


def _find_start_iteration(item: int, build_entries: list[CostEntry]) -> int:
    """Return the iteration number of the first entry with the given item."""
    for entry in build_entries:
        if entry.item == item:
            return entry.iteration
    return 0


def _stuck_from_cost_entries(cost_entries: list[CostEntry]) -> list[StuckEvent]:
    """Detect stuck patterns by finding 3+ consecutive build entries with the same item."""
    build_entries = [
        e for e in cost_entries if e.phase == "build" and e.item is not None
    ]
    if not build_entries:
        return []

    stuck_events = []
    i = 0
    while i < len(build_entries):
        j = i + 1
        while j < len(build_entries) and build_entries[j].item == build_entries[i].item:
            j += 1
        group_size = j - i
        if group_size >= 3:
            stuck_events.append(
                StuckEvent(
                    item=build_entries[i].item,  # type: ignore[arg-type]
                    start_iteration=build_entries[i].iteration,
                    count=group_size - 1,
                )
            )
        i = j
    return stuck_events


def _compute_build_failure_rate(cost_entries: list[CostEntry]) -> float:
    """Fraction of build iterations where the next iteration retries the same item."""
    build_entries = [
        e for e in cost_entries if e.phase == "build" and e.item is not None
    ]
    if not build_entries:
        return 0.0
    total = len(build_entries)
    failed = sum(
        1
        for k in range(len(build_entries) - 1)
        if build_entries[k].item == build_entries[k + 1].item
    )
    return failed / total


def _compute_recovery_times(
    cost_entries: list[CostEntry],
    stuck_events: list[StuckEvent],
) -> dict[int, int]:
    """Count iterations consumed for each stuck item (start through resolution)."""
    build_entries = [
        e for e in cost_entries if e.phase == "build" and e.item is not None
    ]
    result: dict[int, int] = {}
    for stuck in stuck_events:
        result[stuck.item] = sum(1 for e in build_entries if e.item == stuck.item)
    return result
