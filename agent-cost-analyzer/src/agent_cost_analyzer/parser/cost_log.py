"""Parser for cost.log files."""
from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from agent_cost_analyzer.models import CostEntry

logger = logging.getLogger(__name__)

_LINE_RE = re.compile(
    r"^(?P<timestamp>\S+)"
    r"\s+phase=(?P<phase>\S+)"
    r"\s+iter=(?P<iter>\d+)"
    r"\s+model=(?P<model>\S+)"
    r"\s+in=(?P<in_tokens>\d+)"
    r"\s+out=(?P<out_tokens>\d+)"
    r"\s+cost=\$(?P<cost>[\d.]+)"
    r"\s+cumulative=\$(?P<cumulative>[\d.]+)"
    r"\s+item=(?P<item>\d*)$"
)


def _parse_timestamp(raw: str) -> datetime:
    """Parse an ISO 8601 timestamp, ensuring timezone info is present."""
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def parse_cost_log(
    path: Path,
    after: date | None = None,
    before: date | None = None,
) -> list[CostEntry]:
    """Parse a cost.log file into a list of CostEntry objects.

    Args:
        path: Path to cost.log. Raises FileNotFoundError if missing.
        after: Inclusive lower bound (UTC date). Entries on this date are included.
        before: Exclusive upper bound (UTC date). Entries on this date are excluded.

    Returns:
        List of CostEntry objects, one per valid log line.
    """
    if not path.exists():
        raise FileNotFoundError(f"cost.log not found: {path}")

    entries: list[CostEntry] = []

    with path.open() as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue  # blank line — skip silently

            m = _LINE_RE.match(line)
            if m is None:
                logger.warning("Skipping malformed line %d: %r", lineno, line)
                continue

            try:
                timestamp = _parse_timestamp(m.group("timestamp"))
                cost = Decimal(m.group("cost"))
                cumulative = Decimal(m.group("cumulative"))
                in_tokens = int(m.group("in_tokens"))
                out_tokens = int(m.group("out_tokens"))
            except (ValueError, InvalidOperation) as exc:
                logger.warning("Skipping line %d due to parse error: %s", lineno, exc)
                continue

            item_str = m.group("item")
            item: int | None = int(item_str) if item_str else None

            # Date filtering uses UTC date of the entry
            entry_date = timestamp.astimezone(timezone.utc).date()
            if after is not None and entry_date < after:
                continue
            if before is not None and entry_date >= before:
                continue

            entries.append(
                CostEntry(
                    timestamp=timestamp,
                    phase=m.group("phase"),
                    iteration=int(m.group("iter")),
                    model=m.group("model"),
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    cost=cost,
                    cumulative=cumulative,
                    item=item,
                )
            )

    return entries
