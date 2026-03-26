"""Tests verifying fixture files and the sample_project conftest fixture.

These tests ensure:
- All required fixture files exist and are non-empty
- Each fixture file has the expected format (validated by content inspection)
- The sample_project fixture creates the correct directory structure
- Each test gets an isolated copy of the fixtures
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REQUIRED_FIXTURE_FILES = (
    "cost.log",
    "phase.log",
    "metrics.log",
    "harness-state.json",
    "progress.txt",
    "IMPLEMENTATION_PLAN.md",
)


# ---------------------------------------------------------------------------
# Static fixture file tests
# ---------------------------------------------------------------------------


class TestFixtureFiles:
    def test_fixtures_directory_exists(self) -> None:
        assert FIXTURES_DIR.is_dir()

    @pytest.mark.parametrize("filename", REQUIRED_FIXTURE_FILES)
    def test_fixture_file_exists(self, filename: str) -> None:
        assert (FIXTURES_DIR / filename).exists(), f"Missing fixture: {filename}"

    @pytest.mark.parametrize("filename", REQUIRED_FIXTURE_FILES)
    def test_fixture_file_not_empty(self, filename: str) -> None:
        path = FIXTURES_DIR / filename
        assert path.stat().st_size > 0, f"Empty fixture: {filename}"

    def test_cost_log_has_valid_lines(self) -> None:
        content = (FIXTURES_DIR / "cost.log").read_text()
        valid = [
            line
            for line in content.splitlines()
            if "phase=" in line and "iter=" in line and "cost=$" in line
        ]
        assert len(valid) >= 5, "cost.log should have at least 5 valid entries"

    def test_cost_log_covers_multiple_phases(self) -> None:
        content = (FIXTURES_DIR / "cost.log").read_text()
        assert "phase=socratic" in content
        assert "phase=plan" in content
        assert "phase=build" in content

    def test_cost_log_has_multiple_build_iterations(self) -> None:
        content = (FIXTURES_DIR / "cost.log").read_text()
        build_lines = [ln for ln in content.splitlines() if "phase=build" in ln]
        assert len(build_lines) >= 2, "Need multiple build iterations for grouping tests"

    def test_cost_log_has_item_field(self) -> None:
        content = (FIXTURES_DIR / "cost.log").read_text()
        # Both item= (empty) and item=N (digit) formats should appear
        assert "item=" in content

    def test_cost_log_has_malformed_line(self) -> None:
        """Parser robustness: at least one line without expected fields."""
        content = (FIXTURES_DIR / "cost.log").read_text()
        malformed = [
            line
            for line in content.splitlines()
            if line.strip()
            and "phase=" not in line
            and "event=" not in line
            and "metric=" not in line
        ]
        assert len(malformed) >= 1, "cost.log needs a malformed line for robustness testing"

    def test_phase_log_has_event_lines(self) -> None:
        content = (FIXTURES_DIR / "phase.log").read_text()
        valid = [ln for ln in content.splitlines() if "event=" in ln]
        assert len(valid) >= 5

    def test_phase_log_has_start_event(self) -> None:
        content = (FIXTURES_DIR / "phase.log").read_text()
        assert "event=START" in content

    def test_phase_log_has_transition_events(self) -> None:
        content = (FIXTURES_DIR / "phase.log").read_text()
        transitions = [ln for ln in content.splitlines() if "event=TRANSITION" in ln]
        assert len(transitions) >= 2, "Need at least 2 TRANSITION events (socratic→plan, plan→build)"

    def test_phase_log_has_circuit_breaker_event(self) -> None:
        """STUCK status derivation requires a CIRCUIT_BREAKER event in fixtures."""
        content = (FIXTURES_DIR / "phase.log").read_text()
        assert "event=CIRCUIT_BREAKER" in content

    def test_phase_log_has_malformed_line(self) -> None:
        content = (FIXTURES_DIR / "phase.log").read_text()
        malformed = [
            line
            for line in content.splitlines()
            if line.strip() and "event=" not in line
        ]
        assert len(malformed) >= 1, "phase.log needs a malformed line for robustness testing"

    def test_phase_log_timestamps_are_iso8601(self) -> None:
        content = (FIXTURES_DIR / "phase.log").read_text()
        for line in content.splitlines():
            if "event=" in line:
                timestamp = line.split()[0]
                # Basic ISO 8601 check: contains T and timezone info
                assert "T" in timestamp, f"Expected ISO 8601 timestamp, got: {timestamp}"

    def test_metrics_log_valid_lines_have_four_fields(self) -> None:
        content = (FIXTURES_DIR / "metrics.log").read_text()
        valid_lines = [ln for ln in content.splitlines() if "metric=" in ln]
        assert len(valid_lines) >= 2
        for line in valid_lines:
            assert "metric=" in line
            assert "context=" in line
            assert "value=" in line
            assert "detail=" in line

    def test_metrics_log_has_malformed_line(self) -> None:
        content = (FIXTURES_DIR / "metrics.log").read_text()
        malformed = [
            line
            for line in content.splitlines()
            if line.strip() and "metric=" not in line
        ]
        assert len(malformed) >= 1

    def test_harness_state_json_is_valid_json(self) -> None:
        text = (FIXTURES_DIR / "harness-state.json").read_text()
        data = json.loads(text)
        assert isinstance(data, dict)

    def test_harness_state_has_all_required_fields(self) -> None:
        data = json.loads((FIXTURES_DIR / "harness-state.json").read_text())
        required = {"phase", "iteration", "total_iteration", "timestamp", "stuck_count",
                    "current_item", "item_fail_count"}
        assert required.issubset(data.keys()), f"Missing fields: {required - data.keys()}"

    def test_harness_state_uses_phase_not_current_phase(self) -> None:
        """Clarity Round 2: field is 'phase' not 'current_phase'."""
        data = json.loads((FIXTURES_DIR / "harness-state.json").read_text())
        assert "phase" in data
        assert "current_phase" not in data

    def test_harness_state_field_types(self) -> None:
        data = json.loads((FIXTURES_DIR / "harness-state.json").read_text())
        assert isinstance(data["phase"], str)
        assert isinstance(data["iteration"], int)
        assert isinstance(data["total_iteration"], int)
        assert isinstance(data["stuck_count"], int)
        assert isinstance(data["item_fail_count"], int)

    def test_progress_txt_has_harness_init_header(self) -> None:
        content = (FIXTURES_DIR / "progress.txt").read_text()
        assert "=== Harness initialized:" in content

    def test_progress_txt_has_session_blocks(self) -> None:
        content = (FIXTURES_DIR / "progress.txt").read_text()
        sessions = re.findall(r"=== Session \S+ ===", content)
        assert len(sessions) >= 2, "Need at least 2 session blocks"

    def test_progress_txt_has_completed_items(self) -> None:
        content = (FIXTURES_DIR / "progress.txt").read_text()
        completed = re.findall(r"^Completed: Item \d+", content, re.MULTILINE)
        assert len(completed) >= 2

    def test_progress_txt_session_timestamps_are_iso8601(self) -> None:
        content = (FIXTURES_DIR / "progress.txt").read_text()
        for match in re.finditer(r"=== Session (\S+) ===", content):
            ts = match.group(1)
            assert "T" in ts, f"Expected ISO 8601 timestamp in session header, got: {ts}"

    def test_implementation_plan_has_items(self) -> None:
        content = (FIXTURES_DIR / "IMPLEMENTATION_PLAN.md").read_text()
        items = re.findall(r"^## Item \d+:", content, re.MULTILINE)
        assert len(items) >= 4

    def test_implementation_plan_has_done_items(self) -> None:
        content = (FIXTURES_DIR / "IMPLEMENTATION_PLAN.md").read_text()
        assert "status: DONE" in content

    def test_implementation_plan_has_todo_items(self) -> None:
        content = (FIXTURES_DIR / "IMPLEMENTATION_PLAN.md").read_text()
        assert "status: TODO" in content

    def test_implementation_plan_has_priority_fields(self) -> None:
        content = (FIXTURES_DIR / "IMPLEMENTATION_PLAN.md").read_text()
        assert "priority: P0" in content
        assert "priority: P1" in content


# ---------------------------------------------------------------------------
# sample_project fixture tests
# ---------------------------------------------------------------------------


class TestSampleProjectFixture:
    def test_returns_path(self, sample_project: Path) -> None:
        assert isinstance(sample_project, Path)

    def test_project_dir_exists(self, sample_project: Path) -> None:
        assert sample_project.is_dir()

    def test_harness_logs_subdir_exists(self, sample_project: Path) -> None:
        assert (sample_project / ".harness-logs").is_dir()

    def test_cost_log_in_harness_dir(self, sample_project: Path) -> None:
        assert (sample_project / ".harness-logs" / "cost.log").exists()

    def test_phase_log_in_harness_dir(self, sample_project: Path) -> None:
        assert (sample_project / ".harness-logs" / "phase.log").exists()

    def test_metrics_log_in_harness_dir(self, sample_project: Path) -> None:
        assert (sample_project / ".harness-logs" / "metrics.log").exists()

    def test_harness_state_in_harness_dir(self, sample_project: Path) -> None:
        assert (sample_project / ".harness-logs" / "harness-state.json").exists()

    def test_progress_txt_at_project_root(self, sample_project: Path) -> None:
        assert (sample_project / "progress.txt").exists()

    def test_implementation_plan_at_project_root(self, sample_project: Path) -> None:
        assert (sample_project / "IMPLEMENTATION_PLAN.md").exists()

    def test_cost_log_content_matches_source(self, sample_project: Path) -> None:
        project_content = (sample_project / ".harness-logs" / "cost.log").read_text()
        fixture_content = (FIXTURES_DIR / "cost.log").read_text()
        assert project_content == fixture_content

    def test_harness_state_json_is_valid(self, sample_project: Path) -> None:
        data = json.loads(
            (sample_project / ".harness-logs" / "harness-state.json").read_text()
        )
        assert isinstance(data, dict)
        assert "phase" in data

    def test_each_test_gets_isolated_copy(self, sample_project: Path) -> None:
        """Modifying the temp copy should not affect the source fixture."""
        cost_log = sample_project / ".harness-logs" / "cost.log"
        original_content = (FIXTURES_DIR / "cost.log").read_text()
        cost_log.write_text("modified content for isolation test")
        # Source fixture should be unchanged
        assert (FIXTURES_DIR / "cost.log").read_text() == original_content

    def test_harness_logs_contains_exactly_four_files(self, sample_project: Path) -> None:
        harness_dir = sample_project / ".harness-logs"
        files = list(harness_dir.iterdir())
        names = {f.name for f in files}
        assert names == {"cost.log", "phase.log", "metrics.log", "harness-state.json"}

    def test_project_root_has_two_text_files(self, sample_project: Path) -> None:
        root_files = {f.name for f in sample_project.iterdir() if f.is_file()}
        assert "progress.txt" in root_files
        assert "IMPLEMENTATION_PLAN.md" in root_files
