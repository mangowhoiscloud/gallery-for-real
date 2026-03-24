"""Shared pytest fixtures for prompt-version-control tests."""

from pathlib import Path

import pytest

from prompt_vc.commands.init import init
from prompt_vc.commands.snapshot import snapshot

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the tests/fixtures/ directory."""
    return FIXTURES_DIR


@pytest.fixture
def initialized_repo(tmp_path: Path) -> Path:
    """An initialized repo with sample PROMPT_*.md files.

    Layout:
        tmp_path/                  ← repo root (returned)
        tmp_path/prompts/          ← prompt_dir (stored in config.yaml)
        tmp_path/prompts/PROMPT_system.md
        tmp_path/prompts/PROMPT_user.md
        tmp_path/.prompt-vc/       ← store created by init
    """
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "PROMPT_system.md").write_text(
        (FIXTURES_DIR / "PROMPT_system.md").read_text()
    )
    (prompt_dir / "PROMPT_user.md").write_text(
        (FIXTURES_DIR / "PROMPT_user.md").read_text()
    )
    init(tmp_path, prompt_dir)
    return tmp_path


@pytest.fixture
def snapshot_repo(initialized_repo: Path) -> Path:
    """An initialized repo with exactly one snapshot (v1).

    Returns the repo root.
    """
    snapshot(initialized_repo, "initial snapshot")
    return initialized_repo


@pytest.fixture
def two_snapshot_repo(snapshot_repo: Path) -> Path:
    """A repo with two different snapshots (v1 and v2).

    v2 is created by appending a line to PROMPT_system.md.
    Returns the repo root.
    """
    prompt_dir = snapshot_repo / "prompts"
    original = (prompt_dir / "PROMPT_system.md").read_text()
    (prompt_dir / "PROMPT_system.md").write_text(original + "\n## Updated Section\n\nAdded in v2.\n")
    snapshot(snapshot_repo, "second snapshot")
    return snapshot_repo
