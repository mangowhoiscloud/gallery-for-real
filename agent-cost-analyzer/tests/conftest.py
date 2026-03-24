"""Pytest fixtures providing paths to sample log files."""
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the tests/fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def cost_log_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample cost.log fixture."""
    return fixtures_dir / "cost.log"


@pytest.fixture
def malformed_cost_log_path(fixtures_dir: Path) -> Path:
    """Return the path to the malformed cost log fixture."""
    return fixtures_dir / "cost_malformed.log"


@pytest.fixture
def phase_log_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample phase.log fixture."""
    return fixtures_dir / "phase.log"


@pytest.fixture
def metrics_log_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample metrics.log fixture."""
    return fixtures_dir / "metrics.log"


@pytest.fixture
def progress_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample progress.txt fixture."""
    return fixtures_dir / "progress.txt"


@pytest.fixture
def session_log_path(fixtures_dir: Path) -> Path:
    """Return the path to the sample session JSONL fixture."""
    return fixtures_dir / "session_build.jsonl"
