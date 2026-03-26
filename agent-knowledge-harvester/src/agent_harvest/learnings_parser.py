"""Parser for LEARNINGS.md files produced by the harness."""

from __future__ import annotations

import re
from pathlib import Path

from agent_harvest.category import classify_category
from agent_harvest.models import LearningEntry
from agent_harvest.stack import extract_text_stacks
from agent_harvest.utils import make_unique_id, slugify

# Matches `### Learning: <title>` lines; capturing group captures the title.
_HEADER_RE = re.compile(r"^###\s+Learning:\s*(.+)$", re.MULTILINE)

# Matches `- FieldName: value` lines.
_FIELD_RE = re.compile(r"^-\s+(\w+):\s*(.*)$", re.MULTILINE)

_KNOWN_FIELDS = {"Context", "Discovery", "Rule"}


def _parse_fields(body: str) -> dict[str, str]:
    """Extract Context, Discovery, Rule from a learning section body.

    Returns empty string for any field not found.
    """
    fields: dict[str, str] = {"Context": "", "Discovery": "", "Rule": ""}
    for m in _FIELD_RE.finditer(body):
        key = m.group(1)
        if key in _KNOWN_FIELDS:
            fields[key] = m.group(2).strip()
    return fields


def parse_learnings(
    file_path: Path,
    project_name: str,
    project_stacks: list[str],
) -> list[LearningEntry]:
    """Parse a LEARNINGS.md file and return LearningEntry objects.

    Returns an empty list if the file does not exist or contains no entries.
    Handles missing sub-bullets gracefully (empty string).
    """
    if not file_path.exists():
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return []

    if not content.strip():
        return []

    # re.split with a capturing group interleaves [before, group1, after, group1, after, ...]
    parts = _HEADER_RE.split(content)
    # parts[0]    = content before the first ### Learning: header (discard)
    # parts[1::2] = captured titles
    # parts[2::2] = section bodies (text until the next header)
    titles = parts[1::2]
    bodies = parts[2::2]

    entries: list[LearningEntry] = []
    used_ids: set[str] = set()

    for title, body in zip(titles, bodies):
        title = title.strip()
        fields = _parse_fields(body)

        context = fields["Context"]
        discovery = fields["Discovery"]
        rule_text = fields["Rule"]

        # context field = Context + Discovery combined
        combined_context = " ".join(filter(None, [context, discovery])).strip()

        # Full text used for category classification and stack extraction
        full_text = f"{title} {combined_context} {rule_text}"

        entry_id = make_unique_id(slugify(title), used_ids)
        used_ids.add(entry_id)

        category = classify_category(full_text)

        text_stacks = extract_text_stacks(full_text)
        all_stacks = sorted(set(project_stacks) | set(text_stacks))

        entries.append(
            LearningEntry(
                id=entry_id,
                category=category,
                description=title,
                context=combined_context,
                applicable_stacks=all_stacks,
                source_project=project_name,
                source_file="LEARNINGS.md",
            )
        )

    return entries
