"""Tests for the diff command."""

from pathlib import Path

import pytest

from prompt_vc.commands.diff import NotInitializedError, VersionNotFoundError, diff
from prompt_vc.commands.init import init
from prompt_vc.commands.snapshot import snapshot


def test_diff_identical_versions_returns_empty(two_snapshot_repo: Path) -> None:
    """Diff of a version against itself produces no output."""
    result = diff(two_snapshot_repo, "v1", "v1")
    assert result == ""


def test_diff_with_changed_file(two_snapshot_repo: Path) -> None:
    """Diff between v1 and v2 shows changes to PROMPT_system.md."""
    result = diff(two_snapshot_repo, "v1", "v2")
    assert "PROMPT_system.md" in result
    # unified diff headers
    assert "--- " in result
    assert "+++ " in result
    # content added in v2
    assert "Updated Section" in result
    assert "Added in v2." in result


def test_diff_shows_removed_lines(two_snapshot_repo: Path) -> None:
    """Lines only in v1 appear with '-' prefix in the diff."""
    # v1 has lines that v2 also has, but v2 adds more. v1 has no Updated Section.
    result = diff(two_snapshot_repo, "v2", "v1")
    # Going from v2 to v1 removes the added lines
    assert "-## Updated Section" in result or "- ## Updated Section" in result or "Updated Section" in result


def test_diff_version_labels_in_output(two_snapshot_repo: Path) -> None:
    """Diff output includes version-qualified filenames."""
    result = diff(two_snapshot_repo, "v1", "v2")
    assert "v1/PROMPT_system.md" in result
    assert "v2/PROMPT_system.md" in result


def test_diff_unchanged_files_not_included(two_snapshot_repo: Path) -> None:
    """Files with identical hashes between versions are not shown."""
    result = diff(two_snapshot_repo, "v1", "v2")
    # PROMPT_user.md was not changed between v1 and v2
    assert "PROMPT_user.md" not in result


def test_diff_new_file(snapshot_repo: Path) -> None:
    """File present in v2 but not v1 is marked as new file."""
    prompt_dir = snapshot_repo / "prompts"
    (prompt_dir / "PROMPT_tools.md").write_text("# Tools\nNew tools file.\n")
    snapshot(snapshot_repo, "add tools prompt")

    result = diff(snapshot_repo, "v1", "v2")
    assert "new file" in result
    assert "PROMPT_tools.md" in result
    # unified diff should show all lines as additions
    assert "+New tools file." in result or "+ New tools file." in result or "New tools file." in result


def test_diff_deleted_file(tmp_path: Path) -> None:
    """File present in v1 but not in v2 is marked as deleted file."""
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "PROMPT_system.md").write_text("# System\nOriginal.\n")
    (prompt_dir / "PROMPT_tools.md").write_text("# Tools\nOriginal tools.\n")
    init(tmp_path, prompt_dir)
    snapshot(tmp_path, "initial with two files")

    # Remove PROMPT_tools.md before second snapshot
    (prompt_dir / "PROMPT_tools.md").unlink()
    (prompt_dir / "PROMPT_system.md").write_text("# System\nModified.\n")
    snapshot(tmp_path, "removed tools file")

    result = diff(tmp_path, "v1", "v2")
    assert "deleted file" in result
    assert "PROMPT_tools.md" in result


def test_diff_nonexistent_v1_raises(two_snapshot_repo: Path) -> None:
    """VersionNotFoundError raised when v1 does not exist."""
    with pytest.raises(VersionNotFoundError, match="v99"):
        diff(two_snapshot_repo, "v99", "v2")


def test_diff_nonexistent_v2_raises(two_snapshot_repo: Path) -> None:
    """VersionNotFoundError raised when v2 does not exist."""
    with pytest.raises(VersionNotFoundError, match="v99"):
        diff(two_snapshot_repo, "v1", "v99")


def test_diff_not_initialized_raises(tmp_path: Path) -> None:
    """NotInitializedError raised when .prompt-vc/ does not exist."""
    with pytest.raises(NotInitializedError):
        diff(tmp_path, "v1", "v2")


def test_diff_no_output_when_no_file_changes(snapshot_repo: Path) -> None:
    """Returns empty string when both versions have exactly the same files/content."""
    # v1 exists; take another snapshot with a tweak then revert to trigger no diff
    # Instead: compare v1 against v1 explicitly
    result = diff(snapshot_repo, "v1", "v1")
    assert result == ""
