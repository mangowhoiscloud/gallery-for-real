"""Git log analyzer for project change history."""

from __future__ import annotations

import subprocess
from pathlib import Path

from agent_harvest.category import classify_category
from agent_harvest.models import FileChurn, LearningEntry
from agent_harvest.stack import extract_text_stacks
from agent_harvest.utils import make_unique_id, slugify

_FIX_PREFIX = "fix:"


def _run_git(project_dir: Path, args: list[str]) -> str:
    """Run a git command in project_dir; return stdout or "" on error."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _is_git_repo(project_dir: Path) -> bool:
    """Return True if project_dir is inside a git repository."""
    return bool(_run_git(project_dir, ["rev-parse", "--git-dir"]).strip())


def _parse_name_status(output: str) -> dict[str, list[str]]:
    """Parse ``git log --name-status`` output into per-file operation lists.

    Returns a dict mapping filepath → [op, ...] in git-log order (newest first).
    Rename operations (R*) are recorded as "M" on the destination file path.
    Lines without a tab character (commit hashes, blank lines) are skipped.
    """
    file_ops: dict[str, list[str]] = {}

    for line in output.splitlines():
        line = line.rstrip()
        if not line or "\t" not in line:
            continue

        parts = line.split("\t")
        op_code = parts[0]

        if op_code.startswith("R"):
            # "R100\told.py\tnew.py" — treat rename as modify on the new path
            filepath = parts[-1]
            op = "M"
        elif op_code in ("A", "M", "D") and len(parts) >= 2:
            filepath = parts[1]
            op = op_code
        else:
            continue

        if filepath not in file_ops:
            file_ops[filepath] = []
        file_ops[filepath].append(op)

    return file_ops


def _parse_numstat(output: str) -> dict[str, tuple[int, int]]:
    """Parse ``git log --numstat`` output into per-file (added, deleted) totals.

    Accumulates across all commits. Skips binary file entries (shown as "-").
    Lines without a tab character (commit hashes, blank lines) are skipped.
    """
    file_lines: dict[str, tuple[int, int]] = {}

    for line in output.splitlines():
        line = line.rstrip()
        if not line or "\t" not in line:
            continue

        parts = line.split("\t")
        if len(parts) < 3:
            continue

        added_str, deleted_str, filepath = parts[0], parts[1], parts[2]
        if added_str == "-" or deleted_str == "-":
            continue  # binary file

        try:
            added = int(added_str)
            deleted = int(deleted_str)
        except ValueError:
            continue

        prev_a, prev_d = file_lines.get(filepath, (0, 0))
        file_lines[filepath] = (prev_a + added, prev_d + deleted)

    return file_lines


def _detect_reverts(ops: list[str]) -> int:
    """Count A→D→A revert patterns in a file's operation history.

    *ops* is in git-log order (newest commit first).  We reverse to
    chronological order, filter to A/D only, then scan for consecutive A D A
    triples.  Each matched triple advances the cursor past all three operations
    so overlapping patterns are not double-counted.
    """
    chrono = [op for op in reversed(ops) if op in ("A", "D")]
    count = 0
    i = 0
    while i < len(chrono) - 2:
        if chrono[i] == "A" and chrono[i + 1] == "D" and chrono[i + 2] == "A":
            count += 1
            i += 3
        else:
            i += 1
    return count


def _extract_fix_learnings(
    subjects_output: str,
    project_name: str,
    project_stacks: list[str],
) -> list[LearningEntry]:
    """Convert ``fix:`` commit subjects into LearningEntry objects."""
    entries: list[LearningEntry] = []
    used_ids: set[str] = set()

    for line in subjects_output.splitlines():
        subject = line.strip()
        if not subject.startswith(_FIX_PREFIX):
            continue

        description = subject[len(_FIX_PREFIX):].strip()
        if not description:
            continue

        text_stacks = extract_text_stacks(subject)
        all_stacks = sorted(set(project_stacks) | set(text_stacks))

        entry_id = make_unique_id(slugify(description), used_ids)
        used_ids.add(entry_id)

        entries.append(
            LearningEntry(
                id=entry_id,
                category=classify_category(subject),
                description=description,
                context=subject,
                applicable_stacks=all_stacks,
                source_project=project_name,
                source_file="git-log",
            )
        )

    return entries


def analyze_git(
    project_dir: Path,
    project_name: str,
    project_stacks: list[str],
) -> tuple[list[FileChurn], list[LearningEntry]]:
    """Analyze git history to produce FileChurn metrics and fix learnings.

    Returns ``([], [])`` if *project_dir* is not a git repository or git is
    unavailable.
    """
    if not _is_git_repo(project_dir):
        return [], []

    ns_output = _run_git(project_dir, ["log", "--name-status", "--format=%H"])
    stat_output = _run_git(project_dir, ["log", "--numstat", "--format=%H"])
    subject_output = _run_git(project_dir, ["log", "--format=%s"])

    file_ops = _parse_name_status(ns_output)
    file_lines = _parse_numstat(stat_output)

    all_paths = set(file_ops.keys()) | set(file_lines.keys())
    churns: list[FileChurn] = []

    for path in sorted(all_paths):
        ops = file_ops.get(path, [])
        lines_added, lines_deleted = file_lines.get(path, (0, 0))

        churns.append(
            FileChurn(
                path=path,
                add_count=ops.count("A"),
                modify_count=ops.count("M"),
                delete_count=ops.count("D"),
                revert_count=_detect_reverts(ops),
                net_changes=lines_added - lines_deleted,
            )
        )

    learnings = _extract_fix_learnings(subject_output, project_name, project_stacks)
    return churns, learnings
