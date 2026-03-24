"""Parser for progress.txt harness log file."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path

from agent_cost_analyzer.models import ProgressData

logger = logging.getLogger(__name__)

_INIT_RE = re.compile(r"^=== Harness initialized: (.+?) ===$")
_PROJECT_TYPE_RE = re.compile(r"^Project type: (.+)$")
_SESSION_RE = re.compile(r"^=== Session (.+?) ===$")
_COMPLETED_RE = re.compile(r"^Completed: Item (\d+) - (.+)$")
_HARNESS_COMPLETE = "HARNESS_COMPLETE"

_TYPE_MAP: dict[str, str] = {
    "python-uv": "Python",
    "java-maven": "Java",
    "java-gradle": "Java",
    "typescript-npm": "TypeScript",
    "node-npm": "TypeScript",
}


def _normalize_type(raw: str) -> str:
    return _TYPE_MAP.get(raw.strip(), raw.strip())


def _parse_timestamp(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.strip())
    except ValueError:
        logger.warning("Could not parse timestamp: %r", s)
        return None


def parse_progress(path: Path) -> ProgressData:
    """Parse progress.txt and return structured ProgressData.

    Returns a default (empty) ProgressData if the file does not exist.
    Unrecognised lines are silently ignored.
    """
    if not path.exists():
        return ProgressData()

    result = ProgressData()

    with path.open() as fh:
        for line in fh:
            line = line.rstrip("\n")

            m = _INIT_RE.match(line)
            if m:
                result.init_time = _parse_timestamp(m.group(1))
                continue

            m = _PROJECT_TYPE_RE.match(line)
            if m:
                result.project_type = _normalize_type(m.group(1))
                continue

            m = _SESSION_RE.match(line)
            if m:
                ts = _parse_timestamp(m.group(1))
                if ts is not None:
                    result.sessions.append(ts)
                continue

            m = _COMPLETED_RE.match(line)
            if m:
                result.completed_items.append((int(m.group(1)), m.group(2).strip()))
                continue

            if line.strip() == _HARNESS_COMPLETE:
                result.is_complete = True

    return result
