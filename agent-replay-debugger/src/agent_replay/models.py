"""Data models for agent session replay debugger.

Clarity resolutions applied:
- PhaseEntry: event-based model per Round 1 (not spec's simplified format)
- MetricsEntry: 4-field format per Round 7
- CostEntry.item: str (bare integer string or "") per Round 4
- Iteration.status: "OK" | "FAIL" | "STUCK" per Round 6
- Iteration.duration: timedelta per Round 13
- TimelineEvent.data union includes MetricsEntry per Round 7
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal


@dataclass
class CostEntry:
    """One LLM call recorded in cost.log.

    Format: timestamp phase=X iter=N model=M in=N out=N cost=$X cumulative=$X item=N
    """

    timestamp: datetime
    phase: str
    iter: int  # per-phase iteration number (resets each phase)
    model: str
    tokens_in: int
    tokens_out: int
    cost: Decimal
    cumulative: Decimal
    item: str  # "" or digit string like "3" (per clarity Round 4)


@dataclass
class PhaseEntry:
    """One event recorded in phase.log.

    Format: timestamp event=TYPE key=value...
    Per clarity Round 1: event-based model, not spec's simplified format.
    """

    timestamp: datetime
    event_type: str  # START, TRANSITION, CIRCUIT_BREAKER, PARALLEL_START, etc.
    params: dict[str, str]  # all key=value pairs from the log line


@dataclass
class GitCommit:
    """One git commit parsed from git log."""

    hash: str
    message: str
    timestamp: datetime


@dataclass
class SessionBlock:
    """One block from progress.txt delimited by '=== Session ... ===' headers."""

    timestamp: datetime
    content: str  # full text of the block (per clarity Round 8)
    items_completed: list[str]  # extracted "Item N - title" strings


@dataclass
class PlanItem:
    """One item from IMPLEMENTATION_PLAN.md."""

    number: int
    title: str
    status: str  # "DONE" | "TODO" | "IN_PROGRESS"
    priority: str  # "P0" | "P1" | "P2"


@dataclass
class MetricsEntry:
    """One event from metrics.log.

    Actual format has 4 fields per clarity Round 7:
    timestamp metric=X context=Y value=Z detail=W
    """

    timestamp: datetime
    metric: str
    context: str
    value: str
    detail: str


@dataclass
class TimelineEvent:
    """A single event in the unified session timeline.

    event_type: "cost" | "phase" | "commit" | "session" | "metrics"
    data: the parsed event object corresponding to event_type
    """

    timestamp: datetime
    event_type: str
    phase: str
    iteration: int  # global iteration number
    data: CostEntry | PhaseEntry | GitCommit | SessionBlock | MetricsEntry


@dataclass
class Iteration:
    """A single harness loop iteration, grouped by (phase, iter) from cost.log.

    Global iteration number assigned chronologically across all phases.
    status: derived per clarity Round 6:
      - "STUCK"  if a CIRCUIT_BREAKER or ABORT event falls in this iteration's range
      - "FAIL"   if zero git commits and not first/last iteration
      - "OK"     otherwise
    duration: last_event.timestamp - first_event.timestamp (per clarity Round 13)
    """

    number: int  # global chronological iteration number
    phase: str
    events: list[TimelineEvent] = field(default_factory=list)
    cost_total: Decimal = field(default_factory=lambda: Decimal("0"))
    tokens_in: int = 0
    tokens_out: int = 0
    items_done: list[str] = field(default_factory=list)
    git_commits: list[GitCommit] = field(default_factory=list)
    status: str = "OK"  # "OK" | "FAIL" | "STUCK"
    duration: timedelta = field(default_factory=timedelta)
