from __future__ import annotations

from pathlib import Path

from .models import HarvestRule

_HIGH_MED: set[str] = {"high", "medium"}


def write_skills(rules: list[HarvestRule], output_dir: Path) -> list[Path]:
    """Group medium/high-confidence rules by primary stack and write one markdown
    file per stack group to output_dir/skills/.

    Primary stack is the first element of rule.stacks; rules with an empty stacks
    list are grouped under "all".

    Args:
        rules: All harvest rules (may include low-confidence — those are skipped).
        output_dir: Root output directory; skills/ subdir is created automatically.

    Returns:
        List of file paths that were written.
    """
    # Filter to medium/high only
    eligible = [r for r in rules if r.confidence in _HIGH_MED]
    if not eligible:
        return []

    # Group by primary stack
    groups: dict[str, list[HarvestRule]] = {}
    for rule in eligible:
        primary = rule.stacks[0] if rule.stacks else "all"
        groups.setdefault(primary, []).append(rule)

    skills_dir = output_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for stack, stack_rules in sorted(groups.items()):
        file_path = skills_dir / f"{stack}-common.md"
        file_path.write_text(_render_skill_file(stack, stack_rules), encoding="utf-8")
        written.append(file_path)

    return written


def _render_skill_file(stack: str, rules: list[HarvestRule]) -> str:
    lines: list[str] = []

    title = stack.capitalize() if stack != "all" else "All"
    lines.append(f"# {title} Common Rules")
    lines.append("")

    # Collect unique source projects (preserve insertion order)
    seen_projects: dict[str, None] = {}
    for rule in rules:
        for project in rule.source_projects:
            seen_projects[project] = None

    lines.append("## Source")
    for project in seen_projects:
        lines.append(f"- {project}")
    lines.append("")

    for rule in rules:
        lines.append(f"- {rule.rule}")

    lines.append("")
    return "\n".join(lines)
