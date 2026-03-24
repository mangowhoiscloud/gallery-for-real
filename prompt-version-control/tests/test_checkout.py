"""Tests for the checkout command."""

from pathlib import Path

import pytest

from prompt_vc.commands.checkout import (
    NotInitializedError,
    UnsavedChangesError,
    VersionNotFoundError,
    checkout,
)
from prompt_vc.storage import read_index


def test_checkout_clean_restores_files(two_snapshot_repo: Path) -> None:
    """Checking out v1 from v2 (no working changes) restores v1 files."""
    repo = two_snapshot_repo
    prompt_dir = repo / "prompts"

    # Currently at v2 — PROMPT_system.md has extra content
    v2_content = (prompt_dir / "PROMPT_system.md").read_text()
    assert "Updated Section" in v2_content

    # Sync working dir to v2 snapshot (no unsaved changes)
    checkout(repo, "v1")

    v1_content = (prompt_dir / "PROMPT_system.md").read_text()
    assert "Updated Section" not in v1_content


def test_checkout_updates_current_version(two_snapshot_repo: Path) -> None:
    """Checkout updates current_version in index.yaml."""
    repo = two_snapshot_repo
    assert read_index(repo).current_version == "v2"

    checkout(repo, "v1")

    assert read_index(repo).current_version == "v1"


def test_checkout_same_version_is_noop(snapshot_repo: Path) -> None:
    """Checking out the current version (no changes) does not error."""
    repo = snapshot_repo
    prompt_dir = repo / "prompts"
    original_content = (prompt_dir / "PROMPT_system.md").read_text()

    checkout(repo, "v1")

    assert (prompt_dir / "PROMPT_system.md").read_text() == original_content
    assert read_index(repo).current_version == "v1"


def test_checkout_dirty_blocked_without_force(two_snapshot_repo: Path) -> None:
    """Unsaved working changes block checkout without --force."""
    repo = two_snapshot_repo
    prompt_dir = repo / "prompts"

    # Introduce an unsaved change not in any snapshot
    (prompt_dir / "PROMPT_system.md").write_text("totally different content")

    with pytest.raises(UnsavedChangesError):
        checkout(repo, "v1")


def test_checkout_dirty_allowed_with_force(two_snapshot_repo: Path) -> None:
    """--force overwrites unsaved working changes."""
    repo = two_snapshot_repo
    prompt_dir = repo / "prompts"

    (prompt_dir / "PROMPT_system.md").write_text("totally different content")

    checkout(repo, "v1", force=True)

    v1_content = (prompt_dir / "PROMPT_system.md").read_text()
    assert "Updated Section" not in v1_content
    assert v1_content != "totally different content"


def test_checkout_nonexistent_version_raises(snapshot_repo: Path) -> None:
    """Checking out a non-existent version raises VersionNotFoundError."""
    with pytest.raises(VersionNotFoundError, match="v99"):
        checkout(snapshot_repo, "v99")


def test_checkout_not_initialized_raises(tmp_path: Path) -> None:
    """Checking out in an uninitialised directory raises NotInitializedError."""
    with pytest.raises(NotInitializedError):
        checkout(tmp_path, "v1")


def test_checkout_removes_files_not_in_target(two_snapshot_repo: Path) -> None:
    """Files present in working dir but absent from target snapshot are removed."""
    repo = two_snapshot_repo
    prompt_dir = repo / "prompts"

    # Add a file to the snapshot store manually isn't tested here; instead,
    # verify the inverse: v1 had only system+user, v2 also had system+user.
    # We add an extra prompt file to the working dir that was never snapshotted.
    extra = prompt_dir / "PROMPT_extra.md"
    extra.write_text("extra prompt not in any snapshot")

    # Working dir now differs from v2 snapshot (extra file) — use force
    checkout(repo, "v1", force=True)

    # The extra file should be gone (it matched file_pattern but wasn't in v1)
    assert not extra.exists()


def test_checkout_no_current_version_no_unsaved_check(initialized_repo: Path) -> None:
    """If there is no current_version (empty repo), unsaved-change check is skipped."""
    repo = initialized_repo
    # Manually create a snapshot so there's a version to check out, but
    # first confirm current_version is None after just init
    from prompt_vc.commands.snapshot import snapshot

    snapshot(repo, "first")

    # Reset current_version to None to simulate edge case
    index = read_index(repo)
    index.current_version = None
    from prompt_vc.storage import write_index

    write_index(repo, index)

    # Should not raise UnsavedChangesError since current_version is None
    checkout(repo, "v1")
    assert read_index(repo).current_version == "v1"


def test_checkout_force_updates_current_version(two_snapshot_repo: Path) -> None:
    """--force checkout still updates current_version."""
    repo = two_snapshot_repo
    prompt_dir = repo / "prompts"
    (prompt_dir / "PROMPT_system.md").write_text("dirty")

    checkout(repo, "v1", force=True)

    assert read_index(repo).current_version == "v1"


def test_checkout_file_content_matches_snapshot(two_snapshot_repo: Path) -> None:
    """After checkout, file content exactly matches the snapshot's stored file."""
    repo = two_snapshot_repo
    snap_file = repo / ".prompt-vc" / "snapshots" / "v1" / "PROMPT_system.md"
    expected = snap_file.read_text()

    checkout(repo, "v1")

    actual = (repo / "prompts" / "PROMPT_system.md").read_text()
    assert actual == expected
