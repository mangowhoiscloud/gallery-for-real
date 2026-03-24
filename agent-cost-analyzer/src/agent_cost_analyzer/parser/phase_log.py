"""Parsers for phase.log and metrics.log files."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from agent_cost_analyzer.models import MetricEntry, PhaseEvent

logger = logging.getLogger(__name__)

# Matches: {timestamp} event={EVENT}{rest}
_PHASE_LINE_RE = re.compile(
    r"^(?P<timestamp>\S+)\s+event=(?P<event>\S+)(?P<rest>.*)$"
)

# Extracts key=value pairs from event rest (stops at comma or whitespace)
_KV_RE = re.compile(r"(\w+)=([^,\s]+)")

# Matches a full metrics.log line
_METRIC_LINE_RE = re.compile(
    r"^(?P<timestamp>\S+)"
    r"\s+metric=(?P<metric>\S+)"
    r"\s+context=(?P<context>\S+)"
    r"\s+value=(?P<value>\d+)"
    r"\s+detail=(?P<detail>\d+)$"
)


def _parse_timestamp(raw: str) -> datetime:
    """Parse an ISO 8601 timestamp, ensuring timezone info is present."""
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_phase_log(path: Path) -> list[PhaseEvent]:
    """Parse a phase.log file into a list of PhaseEvent objects.

    Returns an empty list if the file does not exist.
    Malformed lines are skipped with a warning.
    """
    if not path.exists():
        return []

    events: list[PhaseEvent] = []

    with path.open() as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue

            m = _PHASE_LINE_RE.match(line)
            if m is None:
                logger.warning("Skipping malformed phase.log line %d: %r", lineno, line)
                continue

            try:
                timestamp = _parse_timestamp(m.group("timestamp"))
            except ValueError as exc:
                logger.warning("Skipping phase.log line %d due to parse error: %s", lineno, exc)
                continue

            event = m.group("event")
            rest = m.group("rest").strip()
            metadata: dict[str, str] = {}

            if event == "CIRCUIT_BREAKER":
                if rest:
                    metadata["message"] = rest
                    # Also extract embedded key=value pairs from the free-text message
                    for k, v in _KV_RE.findall(rest):
                        metadata[k] = v
            else:
                for k, v in _KV_RE.findall(rest):
                    metadata[k] = v

            events.append(PhaseEvent(timestamp=timestamp, event=event, metadata=metadata))

    return events


def parse_metrics_log(path: Path) -> list[MetricEntry]:
    """Parse a metrics.log file into a list of MetricEntry objects.

    Returns an empty list if the file does not exist.
    Malformed lines are skipped with a warning.
    """
    if not path.exists():
        return []

    entries: list[MetricEntry] = []

    with path.open() as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue

            m = _METRIC_LINE_RE.match(line)
            if m is None:
                logger.warning("Skipping malformed metrics.log line %d: %r", lineno, line)
                continue

            try:
                timestamp = _parse_timestamp(m.group("timestamp"))
            except ValueError as exc:
                logger.warning("Skipping metrics.log line %d due to parse error: %s", lineno, exc)
                continue

            entries.append(
                MetricEntry(
                    timestamp=timestamp,
                    metric=m.group("metric"),
                    context=m.group("context"),
                    value=int(m.group("value")),
                    detail=int(m.group("detail")),
                )
            )

    return entries
