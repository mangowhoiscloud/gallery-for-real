"""Parsers for agent session log files.

Each parser reads a specific log format, skips malformed lines with a warning,
and returns an empty list (or None) for missing/invalid files.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from agent_replay.models import CostEntry, GitCommit, MetricsEntry, PhaseEntry, PlanItem, SessionBlock


# Regex for one cost.log line:
# timestamp phase=X iter=N model=M in=N out=N cost=$X.XXXX cumulative=$X.XXXX item=\d*
_COST_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+"
    r"phase=(?P<phase>\S+)\s+"
    r"iter=(?P<iter>\d+)\s+"
    r"model=(?P<model>\S+)\s+"
    r"in=(?P<tokens_in>\d+)\s+"
    r"out=(?P<tokens_out>\d+)\s+"
    r"cost=\$(?P<cost>[\d.]+)\s+"
    r"cumulative=\$(?P<cumulative>[\d.]+)\s+"
    r"item=(?P<item>\d*)$"
)


def parse_cost_log(path: Path) -> list[CostEntry]:
    """Parse cost.log into a list of CostEntry objects.

    Malformed lines are skipped with a warning to stderr.
    Missing or empty file returns [].
    """
    if not path.exists():
        return []

    entries: list[CostEntry] = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        m = _COST_RE.match(line)
        if not m:
            print(
                f"WARNING: cost.log line {lineno}: malformed line skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        try:
            timestamp = datetime.fromisoformat(m.group("timestamp"))
            cost = Decimal(m.group("cost"))
            cumulative = Decimal(m.group("cumulative"))
        except (ValueError, InvalidOperation) as exc:
            print(
                f"WARNING: cost.log line {lineno}: parse error ({exc}), skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        entries.append(
            CostEntry(
                timestamp=timestamp,
                phase=m.group("phase"),
                iter=int(m.group("iter")),
                model=m.group("model"),
                tokens_in=int(m.group("tokens_in")),
                tokens_out=int(m.group("tokens_out")),
                cost=cost,
                cumulative=cumulative,
                item=m.group("item"),
            )
        )

    return entries


# Regex for phase.log main structure:
# timestamp event=TYPE [key=value or free text...]
_PHASE_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+event=(?P<event_type>\S+)(?P<rest>.*)$"
)

# Extracts key=value pairs from the rest of a phase.log line.
# Works for lines like " phase=build" and " Stuck 1 iteration, phase=build".
_PHASE_KV_RE = re.compile(r"\b(\w+)=(\S+)")


def parse_phase_log(path: Path) -> list[PhaseEntry]:
    """Parse phase.log into a list of PhaseEntry objects.

    Format: timestamp event=TYPE [key=value or free text...]
    CIRCUIT_BREAKER events may mix free text with key=value pairs;
    only key=value pairs are captured in params.
    Malformed lines are skipped with a warning to stderr.
    Missing or empty file returns [].
    """
    if not path.exists():
        return []

    entries: list[PhaseEntry] = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        m = _PHASE_RE.match(line)
        if not m:
            print(
                f"WARNING: phase.log line {lineno}: malformed line skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        try:
            timestamp = datetime.fromisoformat(m.group("timestamp"))
        except ValueError as exc:
            print(
                f"WARNING: phase.log line {lineno}: parse error ({exc}), skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        params = dict(_PHASE_KV_RE.findall(m.group("rest")))

        entries.append(
            PhaseEntry(
                timestamp=timestamp,
                event_type=m.group("event_type"),
                params=params,
            )
        )

    return entries


# Session block header: === Session TIMESTAMP ===
_SESSION_HEADER_RE = re.compile(r"^=== Session (?P<timestamp>\S+) ===$", re.MULTILINE)

# Completed item line: "Completed: Item N - title"
_COMPLETED_RE = re.compile(r"^Completed:\s+(?P<item>Item\s+\d+\s+-\s+.+)$", re.MULTILINE)


def parse_progress(path: Path) -> list[SessionBlock]:
    """Parse progress.txt into a list of SessionBlock objects.

    Splits on '=== Session TIMESTAMP ===' headers. Content before the first
    Session header (e.g. '=== Harness initialized ===' lines) is ignored.
    Malformed timestamp headers are skipped with a warning to stderr.
    Missing or empty file returns [].
    """
    if not path.exists():
        return []

    text = path.read_text()
    if not text.strip():
        return []

    headers = list(_SESSION_HEADER_RE.finditer(text))
    if not headers:
        return []

    blocks: list[SessionBlock] = []
    for i, header in enumerate(headers):
        block_start = header.end()
        block_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        content = text[block_start:block_end].strip()

        try:
            timestamp = datetime.fromisoformat(header.group("timestamp"))
        except ValueError as exc:
            print(
                f"WARNING: progress.txt: malformed timestamp {header.group('timestamp')!r}"
                f" ({exc}), skipped",
                file=sys.stderr,
            )
            continue

        items_completed = [
            m.group("item").strip() for m in _COMPLETED_RE.finditer(content)
        ]

        blocks.append(
            SessionBlock(
                timestamp=timestamp,
                content=content,
                items_completed=items_completed,
            )
        )

    return blocks


def parse_harness_state(path: Path) -> dict | None:
    """Parse harness-state.json into a dict.

    The file uses 'phase' (not 'current_phase') per clarity Round 2.
    Returns None if the file is missing, empty, invalid JSON, or not a JSON object.
    Extra/unknown fields are preserved in the returned dict.
    """
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    return data


# Regex for one metrics.log line:
# timestamp metric=X context=Y value=Z detail=W
_METRICS_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+"
    r"metric=(?P<metric>\S+)\s+"
    r"context=(?P<context>\S+)\s+"
    r"value=(?P<value>\S+)\s+"
    r"detail=(?P<detail>\S+)$"
)


def parse_metrics_log(path: Path) -> list[MetricsEntry]:
    """Parse metrics.log into a list of MetricsEntry objects.

    Format: timestamp metric=X context=Y value=Z detail=W
    Malformed lines are skipped with a warning to stderr.
    Missing or empty file returns [].
    """
    if not path.exists():
        return []

    entries: list[MetricsEntry] = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        m = _METRICS_RE.match(line)
        if not m:
            print(
                f"WARNING: metrics.log line {lineno}: malformed line skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        try:
            timestamp = datetime.fromisoformat(m.group("timestamp"))
        except ValueError as exc:
            print(
                f"WARNING: metrics.log line {lineno}: parse error ({exc}), skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        entries.append(
            MetricsEntry(
                timestamp=timestamp,
                metric=m.group("metric"),
                context=m.group("context"),
                value=m.group("value"),
                detail=m.group("detail"),
            )
        )

    return entries


# Regex for ## Item N: title headers in IMPLEMENTATION_PLAN.md
_PLAN_HEADER_RE = re.compile(r"^##\s+Item\s+(?P<number>\d+):\s+(?P<title>.+)$")

# Regex for - status: VALUE and - priority: VALUE fields
_PLAN_STATUS_RE = re.compile(r"^-\s+status:\s+(?P<status>\S+)")
_PLAN_PRIORITY_RE = re.compile(r"^-\s+priority:\s+(?P<priority>\S+)")


def parse_plan(path: Path) -> list[PlanItem]:
    """Parse IMPLEMENTATION_PLAN.md into a list of PlanItem objects.

    Extracts items from ``## Item N: title`` headers and their
    ``- status:`` / ``- priority:`` fields.  Fields missing from an item
    default to "TODO" and "P0" respectively.  Missing or empty file
    returns [].
    """
    if not path.exists():
        return []

    lines = path.read_text().splitlines()
    if not lines:
        return []

    items: list[PlanItem] = []
    current_number: int | None = None
    current_title: str = ""
    current_status: str | None = None
    current_priority: str | None = None

    def _flush() -> None:
        if current_number is not None:
            items.append(
                PlanItem(
                    number=current_number,
                    title=current_title,
                    status=current_status if current_status is not None else "TODO",
                    priority=current_priority if current_priority is not None else "P0",
                )
            )

    for line in lines:
        header_m = _PLAN_HEADER_RE.match(line.rstrip())
        if header_m:
            _flush()
            current_number = int(header_m.group("number"))
            current_title = header_m.group("title").strip()
            current_status = None
            current_priority = None
            continue

        if current_number is not None:
            status_m = _PLAN_STATUS_RE.match(line.rstrip())
            if status_m:
                current_status = status_m.group("status")
                continue

            priority_m = _PLAN_PRIORITY_RE.match(line.rstrip())
            if priority_m:
                current_priority = priority_m.group("priority")

    _flush()
    return items


def parse_git_log(project_dir: Path) -> list[GitCommit]:
    """Parse git log into a list of GitCommit objects.

    Runs ``git log --format=%H %aI %s`` inside *project_dir*.
    Returns [] if project_dir is not a git repository, git is not
    installed, or the log is empty.  Timestamps are timezone-aware.
    Malformed output lines are skipped with a warning to stderr.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H %aI %s"],
            cwd=project_dir,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        # git binary not found
        return []

    if result.returncode != 0:
        # not a git repo or other git error
        return []

    commits: list[GitCommit] = []
    for lineno, raw in enumerate(result.stdout.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue

        # format: HASH<space>ISO8601TIMESTAMP<space>MESSAGE...
        parts = line.split(" ", 2)
        if len(parts) < 2:
            print(
                f"WARNING: git log line {lineno}: malformed line skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        commit_hash = parts[0]
        timestamp_str = parts[1]
        message = parts[2] if len(parts) > 2 else ""

        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError as exc:
            print(
                f"WARNING: git log line {lineno}: parse error ({exc}), skipped: {line!r}",
                file=sys.stderr,
            )
            continue

        commits.append(GitCommit(hash=commit_hash, message=message, timestamp=timestamp))

    return commits
