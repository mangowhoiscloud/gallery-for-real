"""Tests for git_analyzer module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agent_harvest.git_analyzer import (
    _detect_reverts,
    _parse_name_status,
    _parse_numstat,
    analyze_git,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Bare git repo with test identity configured."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(["init"], r)
    _git(["config", "user.email", "test@example.com"], r)
    _git(["config", "user.name", "Test"], r)
    return r


def commit(repo: Path, message: str, ops: list[tuple[str, str | None]]) -> None:
    """Create a commit with the given file operations.

    ops: list of (path, content) where content=None means delete the file.
    """
    for path, content in ops:
        full = repo / path
        if content is None:
            full.unlink()
        else:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content)
    _git(["add", "-A"], repo)
    _git(["commit", "-m", message], repo)


# ---------------------------------------------------------------------------
# Non-git directory
# ---------------------------------------------------------------------------


def test_non_git_dir_returns_empty_lists(tmp_path: Path) -> None:
    churns, learnings = analyze_git(tmp_path, "proj", [])
    assert churns == []
    assert learnings == []


def test_nonexistent_dir_returns_empty_lists(tmp_path: Path) -> None:
    churns, learnings = analyze_git(tmp_path / "missing", "proj", [])
    assert churns == []
    assert learnings == []


# ---------------------------------------------------------------------------
# Empty repo (git init, no commits)
# ---------------------------------------------------------------------------


def test_empty_repo_returns_empty_lists(repo: Path) -> None:
    churns, learnings = analyze_git(repo, "proj", [])
    assert churns == []
    assert learnings == []


# ---------------------------------------------------------------------------
# Return shape
# ---------------------------------------------------------------------------


def test_returns_tuple_of_two_lists(repo: Path) -> None:
    commit(repo, "feat: add file", [("a.py", "x")])
    result = analyze_git(repo, "proj", [])
    assert isinstance(result, tuple)
    assert len(result) == 2
    churns, learnings = result
    assert isinstance(churns, list)
    assert isinstance(learnings, list)


# ---------------------------------------------------------------------------
# FileChurn: add_count
# ---------------------------------------------------------------------------


def test_add_count_single_add(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "hello\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.add_count == 1


def test_add_count_two_when_revert_pattern(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "chore: remove", [("a.py", None)])
    commit(repo, "fix: restore", [("a.py", "v2\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.add_count == 2


def test_multiple_files_tracked_separately(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "a\n"), ("b.py", "b\n")])
    churns, _ = analyze_git(repo, "proj", [])
    paths = {c.path for c in churns}
    assert "a.py" in paths
    assert "b.py" in paths


# ---------------------------------------------------------------------------
# FileChurn: modify_count
# ---------------------------------------------------------------------------


def test_modify_count_single_modify(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "feat: modify", [("a.py", "v2\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.modify_count == 1


def test_modify_count_multiple_modifications(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "fix: mod1", [("a.py", "v2\n")])
    commit(repo, "fix: mod2", [("a.py", "v3\n")])
    commit(repo, "fix: mod3", [("a.py", "v4\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.modify_count == 3


# ---------------------------------------------------------------------------
# FileChurn: delete_count
# ---------------------------------------------------------------------------


def test_delete_count_single_delete(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "hello\n")])
    commit(repo, "chore: delete", [("a.py", None)])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.delete_count == 1


def test_delete_count_zero_for_never_deleted(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "hello\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.delete_count == 0


# ---------------------------------------------------------------------------
# FileChurn: rename counted as modify
# ---------------------------------------------------------------------------


def test_rename_counted_as_modify_on_new_path(repo: Path) -> None:
    commit(repo, "feat: add", [("old.py", "content\n")])
    subprocess.run(
        ["git", "mv", "old.py", "new.py"], cwd=repo, check=True, capture_output=True
    )
    _git(["commit", "-m", "refactor: rename"], repo)
    churns, _ = analyze_git(repo, "proj", [])
    new_churn = next((c for c in churns if c.path == "new.py"), None)
    assert new_churn is not None
    assert new_churn.modify_count == 1
    assert new_churn.add_count == 0


# ---------------------------------------------------------------------------
# FileChurn: revert detection (integration)
# ---------------------------------------------------------------------------


def test_revert_count_for_a_d_a_pattern(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "chore: remove", [("a.py", None)])
    commit(repo, "fix: restore", [("a.py", "v2\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.revert_count == 1


def test_revert_count_zero_for_add_modify(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "fix: modify", [("a.py", "v2\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.revert_count == 0


def test_revert_count_zero_for_add_then_delete(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "v1\n")])
    commit(repo, "chore: remove", [("a.py", None)])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.revert_count == 0


# ---------------------------------------------------------------------------
# _detect_reverts unit tests
# ---------------------------------------------------------------------------


def test_detect_reverts_simple_a_d_a() -> None:
    # git log order (newest first): A D A → reversed chrono: A D A → 1 match
    assert _detect_reverts(["A", "D", "A"]) == 1


def test_detect_reverts_no_pattern_add_modify() -> None:
    assert _detect_reverts(["M", "M", "A"]) == 0


def test_detect_reverts_a_d_only_no_match() -> None:
    # Only A then D in chrono — missing final A
    assert _detect_reverts(["D", "A"]) == 0


def test_detect_reverts_empty_ops() -> None:
    assert _detect_reverts([]) == 0


def test_detect_reverts_single_op() -> None:
    assert _detect_reverts(["A"]) == 0


def test_detect_reverts_two_consecutive_patterns() -> None:
    # chrono: A D A D A D A → 2 patterns
    # git log order is same reversed: A D A D A D A (palindrome)
    assert _detect_reverts(["A", "D", "A", "D", "A", "D", "A"]) == 2


def test_detect_reverts_ignores_modify_ops() -> None:
    # chrono (after filtering A/D): A D A — still 1 revert even with M interleaved
    # ops in git order with M: M A D A M = newest first
    # reversed: M A D A M → filter A/D: A D A → 1 match
    ops = ["M", "A", "D", "A", "M"]
    assert _detect_reverts(ops) == 1


# ---------------------------------------------------------------------------
# net_changes from numstat
# ---------------------------------------------------------------------------


def test_net_changes_from_initial_add(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "line1\nline2\nline3\nline4\nline5\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    assert churn.net_changes == 5


def test_net_changes_accumulates_across_commits(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "line1\nline2\nline3\n")])
    # Append 2 more lines — purely additive diff (+2, -0)
    commit(repo, "fix: add lines", [("a.py", "line1\nline2\nline3\nline4\nline5\n")])
    churns, _ = analyze_git(repo, "proj", [])
    churn = next(c for c in churns if c.path == "a.py")
    # commit1: +3, -0; commit2: +2, -0 → total net = 5
    assert churn.net_changes == 5


# ---------------------------------------------------------------------------
# fix: commit extraction
# ---------------------------------------------------------------------------


def test_fix_commit_produces_one_learning(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle missing files", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert len(learnings) == 1


def test_fix_commit_category_is_error_recovery(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle missing files", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings[0].category == "error-recovery"


def test_fix_commit_source_file_is_git_log(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle error", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings[0].source_file == "git-log"


def test_fix_commit_source_project_propagated(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle error", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "my-project", [])
    assert learnings[0].source_project == "my-project"


def test_fix_commit_description_strips_fix_prefix(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle missing files gracefully", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings[0].description == "handle missing files gracefully"


def test_fix_commit_context_is_full_subject(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle missing files gracefully", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings[0].context == "fix: handle missing files gracefully"


def test_non_fix_commits_produce_no_learnings(repo: Path) -> None:
    commit(repo, "feat: add", [("a.py", "x\n")])
    commit(repo, "chore: cleanup", [("a.py", "y\n")])
    commit(repo, "docs: update readme", [("b.py", "z\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings == []


def test_multiple_fix_commits_produce_multiple_learnings(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle eof error", [("a.py", "y\n")])
    commit(repo, "fix: retry on timeout", [("a.py", "z\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert len(learnings) == 2


def test_fix_commit_only_prefix_no_description_skipped(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix:", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", [])
    assert learnings == []


def test_fix_learnings_have_unique_ids(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle error", [("a.py", "y\n")])
    commit(repo, "fix: handle error", [("a.py", "z\n")])  # duplicate subject
    _, learnings = analyze_git(repo, "proj", [])
    assert len(learnings) == 2
    assert len({e.id for e in learnings}) == 2


def test_fix_commit_stacks_include_project_stacks(repo: Path) -> None:
    commit(repo, "feat: init", [("a.py", "x\n")])
    commit(repo, "fix: handle import error", [("a.py", "y\n")])
    _, learnings = analyze_git(repo, "proj", ["python", "go"])
    assert "python" in learnings[0].applicable_stacks
    assert "go" in learnings[0].applicable_stacks


# ---------------------------------------------------------------------------
# _parse_name_status unit tests
# ---------------------------------------------------------------------------


def test_parse_name_status_add_operation() -> None:
    output = "abc123\n\nA\tsrc/foo.py\n"
    result = _parse_name_status(output)
    assert result == {"src/foo.py": ["A"]}


def test_parse_name_status_modify_operation() -> None:
    output = "abc123\n\nM\tsrc/foo.py\n"
    result = _parse_name_status(output)
    assert result == {"src/foo.py": ["M"]}


def test_parse_name_status_delete_operation() -> None:
    output = "abc123\n\nD\tsrc/foo.py\n"
    result = _parse_name_status(output)
    assert result == {"src/foo.py": ["D"]}


def test_parse_name_status_rename_becomes_modify_on_new_path() -> None:
    output = "abc123\n\nR100\told.py\tnew.py\n"
    result = _parse_name_status(output)
    assert result.get("new.py") == ["M"]
    assert "old.py" not in result


def test_parse_name_status_multiple_ops_same_file_preserves_order() -> None:
    # Two commits: first (newest) modifies, second (older) adds
    output = "hash1\n\nM\tfoo.py\n\nhash2\n\nA\tfoo.py\n"
    result = _parse_name_status(output)
    assert result["foo.py"] == ["M", "A"]  # newest-first order preserved


def test_parse_name_status_empty_output() -> None:
    assert _parse_name_status("") == {}


# ---------------------------------------------------------------------------
# _parse_numstat unit tests
# ---------------------------------------------------------------------------


def test_parse_numstat_basic_add_delete() -> None:
    output = "abc123\n\n10\t5\tsrc/foo.py\n"
    result = _parse_numstat(output)
    assert result == {"src/foo.py": (10, 5)}


def test_parse_numstat_accumulates_across_commits() -> None:
    output = "hash1\n\n3\t1\tfoo.py\n\nhash2\n\n2\t0\tfoo.py\n"
    result = _parse_numstat(output)
    assert result["foo.py"] == (5, 1)


def test_parse_numstat_skips_binary_files() -> None:
    output = "abc123\n\n-\t-\tbinary.bin\n"
    result = _parse_numstat(output)
    assert result == {}


def test_parse_numstat_empty_output() -> None:
    assert _parse_numstat("") == {}
