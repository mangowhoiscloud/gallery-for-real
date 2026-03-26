from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from .models import ClarityEntry, FileChurn, HarvestResult


def write_instability_report(file_churns: list[FileChurn], output_dir: Path) -> Path:
    """Write instability-report.md sorted by modify_count descending.

    Args:
        file_churns: All FileChurn records for the analyzed project(s).
        output_dir: Root output directory; file is written directly here.

    Returns:
        Path to the written file.
    """
    report_path = output_dir / "instability-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_instability(file_churns), encoding="utf-8")
    return report_path


def write_spec_guide(clarity_entries: list[ClarityEntry], output_dir: Path) -> Path:
    """Write spec-guide.md with resolved ambiguities as 'When writing specs, specify...'
    guidelines, grouped by round number.

    Args:
        clarity_entries: All resolved ambiguity entries from CLARITY_LOG.md parsing.
        output_dir: Root output directory; file is written directly here.

    Returns:
        Path to the written file.
    """
    guide_path = output_dir / "spec-guide.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(_render_spec_guide(clarity_entries), encoding="utf-8")
    return guide_path


def write_summary(result: HarvestResult, output_dir: Path) -> Path:
    """Write summary.json as a JSON serialization of HarvestResult.

    Args:
        result: The HarvestResult to serialize.
        output_dir: Root output directory; file is written directly here.

    Returns:
        Path to the written file.
    """
    summary_path = output_dir / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    data = dataclasses.asdict(result)
    summary_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary_path


def _render_instability(file_churns: list[FileChurn]) -> str:
    lines: list[str] = ["# Instability Report", ""]

    if not file_churns:
        lines.append("No file churn data available.")
        lines.append("")
        return "\n".join(lines)

    sorted_churns = sorted(file_churns, key=lambda fc: fc.modify_count, reverse=True)

    lines.append("| Path | Add | Modify | Delete | Revert | Net Changes |")
    lines.append("|------|-----|--------|--------|--------|-------------|")
    for fc in sorted_churns:
        lines.append(
            f"| {fc.path} | {fc.add_count} | {fc.modify_count} |"
            f" {fc.delete_count} | {fc.revert_count} | {fc.net_changes} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_spec_guide(clarity_entries: list[ClarityEntry]) -> str:
    lines: list[str] = ["# Spec Guide", ""]

    if not clarity_entries:
        lines.append("No resolved ambiguities available.")
        lines.append("")
        return "\n".join(lines)

    # Group by round, sorted numerically
    rounds: dict[int, list[ClarityEntry]] = {}
    for entry in clarity_entries:
        rounds.setdefault(entry.round, []).append(entry)

    for round_num in sorted(rounds):
        lines.append(f"## Round {round_num}")
        lines.append("")
        for entry in rounds[round_num]:
            guideline = entry.decision if entry.decision else entry.answer
            lines.append(f"- When writing specs, specify: {guideline}")
        lines.append("")

    return "\n".join(lines)
