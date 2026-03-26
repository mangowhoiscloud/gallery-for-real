"""Parser for progress.txt session logs produced by the harness."""

from __future__ import annotations

import re
from pathlib import Path

from agent_harvest.category import classify_category
from agent_harvest.models import LearningEntry
from agent_harvest.stack import extract_text_stacks
from agent_harvest.utils import make_unique_id, slugify

# Matches `=== Session <timestamp> ===` delimiter lines; captures the timestamp.
_SESSION_RE = re.compile(r"^=== Session\s+(.+?)\s+===", re.MULTILINE)

# Matches the start of a labeled field: `FieldName: value`.
# Field names start with a capital letter and contain only word chars.
_FIELD_START_RE = re.compile(r"^([A-Z][A-Za-z_]*):\s*(.*)$")


def _parse_session_fields(body: str) -> dict[str, str]:
    """Extract labeled fields from a session block body.

    Handles multi-line field values: lines that do not start a new field are
    treated as continuations of the current field and joined with a space.
    """
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        m = _FIELD_START_RE.match(line)
        if m:
            # Save previous field before starting a new one.
            if current_key is not None:
                fields[current_key] = " ".join(current_lines).strip()
            current_key = m.group(1)
            value_start = m.group(2).strip()
            current_lines = [value_start] if value_start else []
        elif current_key is not None:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    # Flush last field.
    if current_key is not None:
        fields[current_key] = " ".join(current_lines).strip()

    return fields


def parse_progress(
    file_path: Path,
    project_name: str,
    project_stacks: list[str],
) -> list[LearningEntry]:
    """Parse a progress.txt file and return LearningEntry objects.

    Creates one LearningEntry per session that contains a `Discovered:` field.
    Sessions without that field are silently skipped.
    Returns an empty list if the file does not exist or contains no entries.
    """
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    if not content.strip():
        return []

    # re.split with a capturing group interleaves
    # [before, timestamp, body, timestamp, body, ...]
    parts = _SESSION_RE.split(content)
    # parts[0]    = content before the first === Session === line (discard)
    # parts[1::2] = captured timestamps
    # parts[2::2] = session bodies
    timestamps = parts[1::2]
    bodies = parts[2::2]

    entries: list[LearningEntry] = []
    used_ids: set[str] = set()

    for _timestamp, body in zip(timestamps, bodies):
        fields = _parse_session_fields(body)
        discovered = fields.get("Discovered", "").strip()
        if not discovered:
            continue

        why = fields.get("Why", "").strip()

        full_text = f"{discovered} {why}"

        entry_id = make_unique_id(slugify(discovered), used_ids)
        used_ids.add(entry_id)

        category = classify_category(full_text)
        text_stacks = extract_text_stacks(full_text)
        all_stacks = sorted(set(project_stacks) | set(text_stacks))

        entries.append(
            LearningEntry(
                id=entry_id,
                category=category,
                description=discovered,
                context=why,
                applicable_stacks=all_stacks,
                source_project=project_name,
                source_file="progress.txt",
            )
        )

    return entries
