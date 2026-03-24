"""Tests for the log command."""

from pathlib import Path

import pytest

from prompt_vc.commands.log import NotInitializedError, log


def test_log_not_initialized(tmp_path: Path) -> None:
    """log raises NotInitializedError when .prompt-vc/ doesn't exist."""
    with pytest.raises(NotInitializedError, match="prompt-vc init"):
        log(tmp_path)


def test_log_empty_repo(initialized_repo: Path) -> None:
    """log returns 'No versions yet.' for a repo with no snapshots."""
    result = log(initialized_repo)
    assert result == "No versions yet."


def test_log_single_version(snapshot_repo: Path) -> None:
    """log shows v1 marked as current (asterisk) for a single-snapshot repo."""
    result = log(snapshot_repo)
    assert result.startswith("*")
    assert "v1" in result
    assert "initial snapshot" in result


def test_log_single_version_contains_hash(snapshot_repo: Path) -> None:
    """log includes an 8-character hash prefix for each version."""
    result = log(snapshot_repo)
    # Hash is 8 hex chars — appears somewhere in the line
    import re
    assert re.search(r"[0-9a-f]{8}", result)


def test_log_single_version_contains_timestamp(snapshot_repo: Path) -> None:
    """log includes the ISO timestamp for each version."""
    result = log(snapshot_repo)
    # ISO 8601 with timezone — contains at minimum a 'T' separator
    assert "T" in result


def test_log_multiple_versions_order(two_snapshot_repo: Path) -> None:
    """log lists versions in reverse chronological order (newest first)."""
    result = log(two_snapshot_repo)
    lines = result.strip().splitlines()
    assert len(lines) == 2
    # newest (v2) is first
    assert "v2" in lines[0]
    assert "v1" in lines[1]


def test_log_current_version_marked(two_snapshot_repo: Path) -> None:
    """log marks the current version with '*', others with ' '."""
    result = log(two_snapshot_repo)
    lines = result.strip().splitlines()
    # v2 is current after two snapshots
    assert lines[0].startswith("*"), f"Expected '*' prefix on v2 line: {lines[0]!r}"
    assert lines[1].startswith(" "), f"Expected ' ' prefix on v1 line: {lines[1]!r}"


def test_log_multiple_versions_messages(two_snapshot_repo: Path) -> None:
    """log includes the commit message for each version."""
    result = log(two_snapshot_repo)
    assert "initial snapshot" in result
    assert "second snapshot" in result


def test_log_format_fields(snapshot_repo: Path) -> None:
    """Each log line contains version, timestamp, short hash, and message."""
    result = log(snapshot_repo)
    line = result.strip()
    # Should have the marker, version ID, timestamp fragment, hash, and message
    assert "v1" in line
    assert "initial snapshot" in line
    # Two-space separation between fields
    assert "  " in line
