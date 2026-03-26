from __future__ import annotations

import re
from pathlib import Path

from .models import ClarityEntry

# Ordered list of known field labels used in ambiguity blocks.
_FIELD_LABELS = (
    "Round",
    "Spec",
    "Category",
    "Severity",
    "Q",
    "A",
    "Confidence",
    "Remaining_Ambiguity",
    "Resolution",
)

# Regex to capture content between pairs of ``` fences (non-greedy).
_FENCE_RE = re.compile(r"```\n(.*?)```", re.DOTALL)


def _parse_block_fields(block: str) -> dict[str, str]:
    """Extract key→value pairs from a single ambiguity block."""
    fields: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    for line in block.splitlines():
        matched = False
        for label in _FIELD_LABELS:
            prefix = f"{label}: "
            if line.startswith(prefix):
                if current_key is not None:
                    fields[current_key] = "\n".join(current_lines)
                current_key = label
                current_lines = [line[len(prefix) :]]
                matched = True
                break

        if not matched:
            if line.rstrip() == "---":
                # Block terminator — flush current field.
                if current_key is not None:
                    fields[current_key] = "\n".join(current_lines)
                    current_key = None
                    current_lines = []
            elif current_key is not None:
                current_lines.append(line)

    # Flush any field that wasn't terminated by ---.
    if current_key is not None:
        fields[current_key] = "\n".join(current_lines)

    return fields


def parse_clarity_log(file_path: Path | str) -> list[ClarityEntry]:
    """Parse a CLARITY_LOG.md file and return a list of ClarityEntry objects.

    Returns an empty list if the file does not exist or contains no blocks.
    """
    path = Path(file_path)
    if not path.exists():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    if not text.strip():
        return []

    entries: list[ClarityEntry] = []
    for match in _FENCE_RE.finditer(text):
        block = match.group(1)
        fields = _parse_block_fields(block)

        # A valid ambiguity block must have at least Round and Q.
        if "Round" not in fields or "Q" not in fields:
            continue

        try:
            round_num = int(fields["Round"].strip())
        except ValueError:
            continue

        entries.append(
            ClarityEntry(
                round=round_num,
                question=fields.get("Q", "").strip(),
                answer=fields.get("A", "").strip(),
                decision=fields.get("Resolution", "").strip(),
            )
        )

    return entries
