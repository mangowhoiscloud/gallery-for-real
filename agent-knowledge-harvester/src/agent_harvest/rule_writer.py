from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import yaml

from .models import HarvestRule

_CONFIDENCE_ORDER: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


def write_rules(
    rules: list[HarvestRule],
    output_dir: Path,
    *,
    format: str = "yaml",
    min_confidence: str = "low",
    stack: str | None = None,
) -> list[Path]:
    """Write each HarvestRule as a separate file in output_dir/rules/.

    Args:
        rules: Rules to write.
        output_dir: Root output directory; rules/ subdir is created automatically.
        format: "yaml" (default) or "json".
        min_confidence: Minimum confidence level to include ("low", "medium", "high").
        stack: If set, only write rules whose stacks list contains this stack
               (rules with empty stacks are included regardless — they apply to all).

    Returns:
        List of file paths that were written.
    """
    min_level = _CONFIDENCE_ORDER.get(min_confidence, 0)
    ext = ".json" if format == "json" else ".yaml"

    filtered = [r for r in rules if _passes_filters(r, min_level, stack)]

    if not filtered:
        return []

    rules_dir = output_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for rule in filtered:
        file_path = rules_dir / (rule.id + ext)
        data = dataclasses.asdict(rule)
        if format == "json":
            file_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        else:
            file_path.write_text(
                yaml.safe_dump(data, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )
        written.append(file_path)

    return written


def _passes_filters(rule: HarvestRule, min_level: int, stack: str | None) -> bool:
    if _CONFIDENCE_ORDER.get(rule.confidence, 0) < min_level:
        return False
    # Empty stacks means "all stacks" — never excluded by stack filter
    if stack is not None and rule.stacks and stack not in rule.stacks:
        return False
    return True
