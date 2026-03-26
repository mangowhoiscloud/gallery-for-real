"""Pytest configuration and shared fixtures for agent_replay tests."""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Return Path to a fully populated harness project directory.

    Creates a temporary directory mirroring a real harness project:

        <tmp_path>/
            .harness-logs/
                cost.log
                phase.log
                metrics.log
                harness-state.json
            progress.txt
            IMPLEMENTATION_PLAN.md

    Each test gets its own isolated copy that can be modified freely.
    """
    harness_dir = tmp_path / ".harness-logs"
    harness_dir.mkdir()

    for log_file in ("cost.log", "phase.log", "metrics.log", "harness-state.json"):
        shutil.copy2(FIXTURES_DIR / log_file, harness_dir / log_file)

    for proj_file in ("progress.txt", "IMPLEMENTATION_PLAN.md"):
        shutil.copy2(FIXTURES_DIR / proj_file, tmp_path / proj_file)

    return tmp_path
