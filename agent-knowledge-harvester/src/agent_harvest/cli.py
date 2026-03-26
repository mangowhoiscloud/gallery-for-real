from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

from .clarity_parser import parse_clarity_log
from .git_analyzer import analyze_git
from .learnings_parser import parse_learnings
from .models import ClarityEntry, FileChurn, HarvestResult, HarvestRule
from .progress_parser import parse_progress
from .report_writer import write_instability_report, write_spec_guide, write_summary
from .rule_writer import _CONFIDENCE_ORDER, _passes_filters, write_rules
from .skill_writer import write_skills
from .stack import detect_project_stacks
from .synthesizer import synthesize_cross, synthesize_single

_MARKER_FILES = (
    "pyproject.toml",
    "setup.py",
    "pom.xml",
    "package.json",
    "Cargo.toml",
    "go.mod",
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-harvest",
        description="Extract reusable patterns and skills from completed agent sessions.",
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        metavar="project-dir",
        help="Single project directory to analyze.",
    )
    parser.add_argument(
        "--gallery",
        metavar="gallery-dir",
        help="Analyze all projects found as immediate subdirectories.",
    )
    parser.add_argument(
        "--output",
        default="harvest-output",
        metavar="dir",
        help="Output directory (default: harvest-output/).",
    )
    parser.add_argument(
        "--stack",
        metavar="stack",
        help="Only output rules for this stack.",
    )
    parser.add_argument(
        "--min-confidence",
        choices=["low", "medium", "high"],
        default="low",
        dest="min_confidence",
        help="Minimum confidence level to include (default: low).",
    )
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Rule output format (default: yaml).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Print summary without writing files.",
    )
    return parser


def _discover_projects(gallery_dir: Path) -> list[Path]:
    """Return sorted immediate subdirectories that look like projects.

    A directory qualifies if it contains a .git/ directory or any marker file
    (pyproject.toml, setup.py, pom.xml, package.json, Cargo.toml, go.mod).
    Hidden directories (name starts with '.') are excluded.
    """
    if not gallery_dir.is_dir():
        return []

    projects: list[Path] = []
    for child in sorted(gallery_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        is_project = (child / ".git").is_dir() or any(
            (child / m).exists() for m in _MARKER_FILES
        )
        if is_project:
            projects.append(child)

    return projects


def _analyze_project(
    project_dir: Path,
) -> tuple[list[HarvestRule], HarvestResult, list[ClarityEntry], list[FileChurn]]:
    """Run the full analysis pipeline for one project directory."""
    project_name = project_dir.name
    stacks = detect_project_stacks(project_dir)

    learnings = parse_learnings(project_dir / "LEARNINGS.md", project_name, stacks)
    clarity = parse_clarity_log(project_dir / "CLARITY_LOG.md")
    progress = parse_progress(project_dir / "progress.txt", project_name, stacks)
    file_churns, git_learnings = analyze_git(project_dir, project_name, stacks)

    all_learnings = learnings + progress + git_learnings
    rules, result = synthesize_single(all_learnings, clarity, file_churns, project_name)

    return rules, result, clarity, file_churns


def _print_summary(
    result: HarvestResult,
    *,
    filtered_count: int | None = None,
    stack: str | None = None,
    min_confidence: str = "low",
) -> None:
    """Print a human-readable HarvestResult summary to stdout."""
    print(f"Projects analyzed: {result.projects_analyzed}")
    print(f"Total learnings:   {result.total_learnings}")
    print(f"Total rules:       {result.total_rules}")
    # Show filtered count when active filters would reduce the output
    if filtered_count is not None and (
        filtered_count != result.total_rules or stack or min_confidence != "low"
    ):
        parts: list[str] = []
        if stack:
            parts.append(f"stack={stack}")
        if min_confidence != "low":
            parts.append(f"min-confidence={min_confidence}")
        filter_suffix = f" (filtered by {', '.join(parts)})" if parts else ""
        print(f"Would write:       {filtered_count} rules{filter_suffix}")
    print(f"High confidence:   {result.high_confidence_rules}")
    if result.categories:
        cats = ", ".join(f"{k}={v}" for k, v in sorted(result.categories.items()))
        print(f"Categories:        {cats}")
    if result.stacks:
        stacks_str = ", ".join(f"{k}={v}" for k, v in sorted(result.stacks.items()))
        print(f"Stacks:            {stacks_str}")
    print(f"Unstable files:    {len(result.unstable_files)}")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.project_dir is None and args.gallery is None:
        parser.error("provide either project-dir or --gallery")
    if args.project_dir is not None and args.gallery is not None:
        parser.error("cannot use both project-dir and --gallery at the same time")

    output_dir = Path(args.output)

    if args.gallery is not None:
        gallery_dir = Path(args.gallery)
        if not gallery_dir.is_dir():
            print(f"Error: gallery directory not found: {gallery_dir}", file=sys.stderr)
            sys.exit(1)

        project_dirs = _discover_projects(gallery_dir)
        if not project_dirs:
            print("No projects found in gallery directory.")
            sys.exit(0)

        project_results: list[tuple[list[HarvestRule], HarvestResult]] = []
        all_clarity: list[ClarityEntry] = []
        all_file_churns: list[FileChurn] = []

        for project_dir in project_dirs:
            project_name = project_dir.name
            p_rules, p_result, p_clarity, p_churns = _analyze_project(project_dir)
            project_results.append((p_rules, p_result))
            all_clarity.extend(p_clarity)
            # Prefix each path with project name to disambiguate same-named files
            all_file_churns.extend(
                dataclasses.replace(fc, path=f"{project_name}/{fc.path}")
                for fc in p_churns
            )

        rules, result = synthesize_cross(project_results)
        clarity = all_clarity
        file_churns = all_file_churns

    else:
        project_dir = Path(args.project_dir)
        if not project_dir.is_dir():
            print(f"Error: project directory not found: {project_dir}", file=sys.stderr)
            sys.exit(1)

        rules, result, clarity, file_churns = _analyze_project(project_dir)

    if not rules:
        print("No patterns found.")
        sys.exit(0)

    if args.dry_run:
        min_level = _CONFIDENCE_ORDER.get(args.min_confidence, 0)
        filtered_count = sum(
            1 for r in rules if _passes_filters(r, min_level, args.stack)
        )
        _print_summary(
            result,
            filtered_count=filtered_count,
            stack=args.stack,
            min_confidence=args.min_confidence,
        )
        return

    write_rules(
        rules,
        output_dir,
        format=args.format,
        min_confidence=args.min_confidence,
        stack=args.stack,
    )
    write_skills(rules, output_dir)
    write_instability_report(file_churns, output_dir)
    write_spec_guide(clarity, output_dir)
    write_summary(result, output_dir)


if __name__ == "__main__":
    main()
