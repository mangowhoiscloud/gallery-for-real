"""Tests for progress_parser.parse_progress()."""

from __future__ import annotations

from pathlib import Path

from agent_harvest.progress_parser import _parse_session_fields, parse_progress


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "progress.txt"

_THREE_SESSION_CONTENT = """\
=== Harness initialized: 2026-01-01T00:00:00Z ===

=== Session 2026-01-01T10:00:00Z ===
Completed: Item 1 - Models
Changes: Created models.py with 3 dataclasses.
Why: Foundation for all downstream parsers.
Discovered: pytest tmp_path fixture resets between tests — never reuse paths across test functions.
Difficulty: S as estimated.

=== Session 2026-01-01T11:00:00Z ===
Completed: Item 2 - Parser
Changes: Created parser.py.
Why: Used re.split with capturing group to interleave titles and bodies cleanly.

=== Session 2026-01-01T12:00:00Z ===
Completed: Item 3 - Writer
Changes: Created writer.py.
Why: pyyaml allow_unicode=True required to preserve Korean text without escaping.
Discovered: pyyaml safe_dump strips trailing newlines from multi-line strings unless the string ends with a newline.
Difficulty: S as estimated.
"""


# ---------------------------------------------------------------------------
# _parse_session_fields unit tests
# ---------------------------------------------------------------------------


def test_parse_session_fields_basic() -> None:
    body = "Completed: Item 1\nWhy: Because.\nDiscovered: Something new.\nDifficulty: S"
    fields = _parse_session_fields(body)
    assert fields["Completed"] == "Item 1"
    assert fields["Why"] == "Because."
    assert fields["Discovered"] == "Something new."
    assert fields["Difficulty"] == "S"


def test_parse_session_fields_multiline_value() -> None:
    body = "Discovered: First line\n  continuation line\nDifficulty: M"
    fields = _parse_session_fields(body)
    assert "First line" in fields["Discovered"]
    assert "continuation line" in fields["Discovered"]


def test_parse_session_fields_missing_field_returns_empty() -> None:
    body = "Completed: Item 1\nDifficulty: S"
    fields = _parse_session_fields(body)
    assert "Discovered" not in fields
    assert "Why" not in fields


def test_parse_session_fields_empty_body() -> None:
    fields = _parse_session_fields("")
    assert fields == {}


def test_parse_session_fields_blank_lines_ignored() -> None:
    body = "\nCompleted: Item 1\n\nWhy: Because.\n\nDiscovered: Found it.\n"
    fields = _parse_session_fields(body)
    assert fields["Discovered"] == "Found it."


# ---------------------------------------------------------------------------
# parse_progress — basic functionality
# ---------------------------------------------------------------------------


def test_parse_progress_returns_only_sessions_with_discovered(tmp_path: Path) -> None:
    """3 sessions, 2 have Discovered → 2 LearningEntry objects."""
    f = tmp_path / "progress.txt"
    f.write_text(_THREE_SESSION_CONTENT, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert len(entries) == 2


def test_parse_progress_skips_sessions_without_discovered(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Completed: Item 1
Why: No Discovered field here.
Difficulty: S
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_uses_discovered_as_description(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: pytest tmp_path resets between tests.
Why: Foundation.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert len(entries) == 1
    assert entries[0].description == "pytest tmp_path resets between tests."


def test_parse_progress_uses_why_as_context(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Why: This is the important reasoning behind the decision.
Discovered: pyyaml strips trailing newlines without explicit newline.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert len(entries) == 1
    assert entries[0].context == "This is the important reasoning behind the decision."


def test_parse_progress_context_empty_when_no_why(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Something discovered here.
Difficulty: S
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries[0].context == ""


def test_parse_progress_source_file_is_progress_txt(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Something useful was found.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "myproject", [])
    assert entries[0].source_file == "progress.txt"


def test_parse_progress_source_project_set_correctly(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Something useful.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "tistory-migrator", [])
    assert entries[0].source_project == "tistory-migrator"


# ---------------------------------------------------------------------------
# parse_progress — ID generation
# ---------------------------------------------------------------------------


def test_parse_progress_id_is_slug_of_discovered(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Python datetime fromisoformat timezone quirk.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries[0].id == "python-datetime-fromisoformat-timezone-quirk"


def test_parse_progress_ids_are_unique_on_collision(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Same discovery text.

=== Session 2026-01-01T11:00:00Z ===
Discovered: Same discovery text.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert len(entries) == 2
    assert entries[0].id != entries[1].id
    assert entries[1].id == "same-discovery-text-2"


# ---------------------------------------------------------------------------
# parse_progress — category classification
# ---------------------------------------------------------------------------


def test_parse_progress_category_error_recovery(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: requests library throws ConnectionError on transient failures, need retry logic.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries[0].category == "error-recovery"


def test_parse_progress_category_library_quirk(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: pyyaml API quirk — safe_dump strips trailing newlines from multi-line strings.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries[0].category == "library-quirk"


def test_parse_progress_category_defaults_to_pattern(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Always append trailing newline to multi-line YAML string fields.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries[0].category == "pattern"


# ---------------------------------------------------------------------------
# parse_progress — stack detection
# ---------------------------------------------------------------------------


def test_parse_progress_stack_from_project_stacks(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: Something without stack mention.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", ["rust"])
    assert "rust" in entries[0].applicable_stacks


def test_parse_progress_stack_extracted_from_text(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: pytest and ruff are the primary tools in this Python project.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert "python" in entries[0].applicable_stacks


def test_parse_progress_stacks_union_project_and_text(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: pytest and ruff are required for Korean content testing.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", ["java"])
    stacks = entries[0].applicable_stacks
    assert "java" in stacks
    assert "python" in stacks


def test_parse_progress_stacks_sorted(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: pytest and pyyaml used in this go project.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", ["go"])
    stacks = entries[0].applicable_stacks
    assert stacks == sorted(stacks)


# ---------------------------------------------------------------------------
# parse_progress — edge cases
# ---------------------------------------------------------------------------


def test_parse_progress_nonexistent_file_returns_empty() -> None:
    entries = parse_progress(Path("/nonexistent/progress.txt"), "proj", [])
    assert entries == []


def test_parse_progress_empty_file_returns_empty(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("", encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_whitespace_only_returns_empty(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("   \n\n  \n", encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_no_session_delimiters_returns_empty(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("No sessions here, just some text.\n", encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_header_only_no_sessions_returns_empty(tmp_path: Path) -> None:
    f = tmp_path / "progress.txt"
    f.write_text("=== Harness initialized: 2026-01-01T00:00:00Z ===\n", encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_discovered_empty_string_skipped(tmp_path: Path) -> None:
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Completed: Item 1
Discovered:
Why: Some reason.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert entries == []


def test_parse_progress_fixture_file_parses_correctly() -> None:
    """Integration smoke test using the checked-in fixture file."""
    entries = parse_progress(FIXTURE_PATH, "tistory-migrator", ["python"])
    # Fixture has 4 sessions, 3 have Discovered fields.
    assert len(entries) == 3
    for entry in entries:
        assert entry.source_file == "progress.txt"
        assert entry.source_project == "tistory-migrator"
        assert entry.description != ""
        assert entry.id != ""


def test_parse_progress_fixture_ids_are_unique() -> None:
    entries = parse_progress(FIXTURE_PATH, "tistory-migrator", ["python"])
    ids = [e.id for e in entries]
    assert len(ids) == len(set(ids))


def test_parse_progress_fixture_all_have_python_stack() -> None:
    entries = parse_progress(FIXTURE_PATH, "tistory-migrator", ["python"])
    for entry in entries:
        assert "python" in entry.applicable_stacks


def test_parse_progress_multiple_sessions_correct_count(tmp_path: Path) -> None:
    """Explicit check: 5 sessions, 3 with Discovered → 3 entries."""
    content = """\
=== Session 2026-01-01T10:00:00Z ===
Discovered: First discovery.

=== Session 2026-01-01T11:00:00Z ===
Why: No discovery here.

=== Session 2026-01-01T12:00:00Z ===
Discovered: Second discovery.

=== Session 2026-01-01T13:00:00Z ===
Changes: Just some changes.

=== Session 2026-01-01T14:00:00Z ===
Discovered: Third discovery.
"""
    f = tmp_path / "progress.txt"
    f.write_text(content, encoding="utf-8")
    entries = parse_progress(f, "proj", [])
    assert len(entries) == 3
    assert entries[0].description == "First discovery."
    assert entries[1].description == "Second discovery."
    assert entries[2].description == "Third discovery."
