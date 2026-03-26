from __future__ import annotations

from pathlib import Path

from agent_harvest.learnings_parser import parse_learnings
from agent_harvest.models import LearningEntry

FIXTURE_DIR = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_learnings(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "LEARNINGS.md"
    p.write_text(content, encoding="utf-8")
    return p


MINIMAL_ENTRY = """\
# LEARNINGS

### Learning: Use word boundaries
- Context: Building a classifier
- Discovery: Without boundaries, partial matches occur.
- Rule: Add word boundaries to all keyword patterns.
"""

THREE_ENTRY_DOC = """\
# LEARNINGS

### Learning: Use word boundaries
- Context: Building a classifier
- Discovery: Without boundaries, partial matches occur.
- Rule: Add word boundaries to all keyword patterns.

### Learning: pytest fixture scope
- Context: Writing integration tests
- Discovery: Session-scoped fixtures outlive function-scoped ones.
- Rule: Use function scope for stateful fixtures.

### Learning: uv run ensures isolation
- Context: Running ruff via CI
- Discovery: Bare ruff may pick up a system version.
- Rule: Always prefix tool invocations with uv run.
"""


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_parse_learnings_count(tmp_path: Path) -> None:
    """3 entries produce exactly 3 LearningEntry objects."""
    fp = _make_learnings(tmp_path, THREE_ENTRY_DOC)
    entries = parse_learnings(fp, "my-project", ["python"])
    assert len(entries) == 3


def test_parse_learnings_returns_learning_entry_type(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "proj", [])
    assert all(isinstance(e, LearningEntry) for e in entries)


def test_parse_learnings_description_is_title(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].description == "Use word boundaries"


def test_parse_learnings_context_combines_context_and_discovery(tmp_path: Path) -> None:
    """context field = Context + Discovery combined."""
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "proj", [])
    ctx = entries[0].context
    assert "Building a classifier" in ctx
    assert "partial matches" in ctx


def test_parse_learnings_source_file_is_learnings_md(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].source_file == "LEARNINGS.md"


def test_parse_learnings_source_project(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "my-awesome-project", [])
    assert entries[0].source_project == "my-awesome-project"


def test_parse_learnings_fixture_file() -> None:
    """Parses the realistic fixture and produces 6 entries."""
    fp = FIXTURE_DIR / "LEARNINGS.md"
    entries = parse_learnings(fp, "agent-knowledge-harvester", ["python"])
    assert len(entries) == 6


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def test_parse_learnings_id_is_slug(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, MINIMAL_ENTRY)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].id == "use-word-boundaries"


def test_parse_learnings_ids_are_unique(tmp_path: Path) -> None:
    doc = """\
### Learning: Same Title
- Rule: Rule one.

### Learning: Same Title
- Rule: Rule two.
"""
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    ids = [e.id for e in entries]
    assert len(set(ids)) == 2


def test_parse_learnings_duplicate_id_appends_counter(tmp_path: Path) -> None:
    doc = """\
### Learning: Same Title
- Rule: Rule one.

### Learning: Same Title
- Rule: Rule two.
"""
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].id == "same-title"
    assert entries[1].id == "same-title-2"


def test_parse_learnings_id_max_length(tmp_path: Path) -> None:
    long_title = "A" * 80
    doc = f"### Learning: {long_title}\n- Rule: Something.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert len(entries[0].id) <= 60


# ---------------------------------------------------------------------------
# Category classification
# ---------------------------------------------------------------------------

def test_parse_learnings_category_error_recovery(tmp_path: Path) -> None:
    doc = "### Learning: Handle exception with retry fallback\n- Rule: Always retry on error.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].category == "error-recovery"


def test_parse_learnings_category_testing(tmp_path: Path) -> None:
    doc = "### Learning: Use pytest fixtures for isolation\n- Rule: Create fixture per test.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].category == "testing"


def test_parse_learnings_category_performance(tmp_path: Path) -> None:
    doc = "### Learning: Cache expensive query results\n- Rule: Cache with TTL.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].category == "performance"


def test_parse_learnings_category_default_pattern(tmp_path: Path) -> None:
    doc = "### Learning: Organize code by domain layer\n- Rule: Put interfaces in domain.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].category == "pattern"


def test_parse_learnings_fixture_categories_classified(tmp_path: Path) -> None:
    """Each fixture entry gets a non-empty category."""
    fp = FIXTURE_DIR / "LEARNINGS.md"
    entries = parse_learnings(fp, "proj", [])
    valid_categories = {
        "error-recovery", "library-quirk", "pattern",
        "performance", "testing", "compatibility",
    }
    for e in entries:
        assert e.category in valid_categories, f"Bad category for {e.description!r}: {e.category}"


# ---------------------------------------------------------------------------
# Stack detection
# ---------------------------------------------------------------------------

def test_parse_learnings_stacks_from_text(tmp_path: Path) -> None:
    doc = "### Learning: Use pytest for unit tests\n- Rule: Run pytest.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert "python" in entries[0].applicable_stacks


def test_parse_learnings_project_stacks_included(tmp_path: Path) -> None:
    """project_stacks appear in applicable_stacks even if not mentioned in text."""
    doc = "### Learning: Organize code layers\n- Rule: Keep it simple.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", ["go"])
    assert "go" in entries[0].applicable_stacks


def test_parse_learnings_stacks_are_union(tmp_path: Path) -> None:
    """applicable_stacks = union of text-detected + project_stacks."""
    doc = "### Learning: Use pytest for isolation\n- Rule: Fixture per test.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", ["java"])
    stacks = entries[0].applicable_stacks
    assert "python" in stacks
    assert "java" in stacks


def test_parse_learnings_stacks_sorted(tmp_path: Path) -> None:
    doc = "### Learning: Use pytest\n- Rule: Run tests.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", ["rust", "go"])
    stacks = entries[0].applicable_stacks
    assert stacks == sorted(stacks)


def test_parse_learnings_no_stacks_when_empty(tmp_path: Path) -> None:
    doc = "### Learning: General approach\n- Rule: Keep it simple.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    # No text stacks, no project stacks — could be empty
    assert isinstance(entries[0].applicable_stacks, list)


# ---------------------------------------------------------------------------
# Missing fields / graceful handling
# ---------------------------------------------------------------------------

def test_parse_learnings_missing_context_is_empty_string(tmp_path: Path) -> None:
    doc = "### Learning: Some Learning\n- Discovery: Found this.\n- Rule: Do it.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    # Context is missing; context field should just have the Discovery text
    assert "Found this" in entries[0].context


def test_parse_learnings_missing_discovery_is_empty_string(tmp_path: Path) -> None:
    doc = "### Learning: Some Learning\n- Context: Here is context.\n- Rule: Do it.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert "Here is context" in entries[0].context


def test_parse_learnings_missing_rule_no_error(tmp_path: Path) -> None:
    doc = "### Learning: Some Learning\n- Context: Here is context.\n- Discovery: Discovered thing.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert len(entries) == 1


def test_parse_learnings_all_fields_missing_no_error(tmp_path: Path) -> None:
    doc = "### Learning: Just a Title\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert len(entries) == 1
    assert entries[0].description == "Just a Title"
    assert entries[0].context == ""


def test_parse_learnings_only_rule_present(tmp_path: Path) -> None:
    doc = "### Learning: Minimal\n- Rule: Always do X.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].description == "Minimal"
    assert entries[0].context == ""


# ---------------------------------------------------------------------------
# Empty / nonexistent file
# ---------------------------------------------------------------------------

def test_parse_learnings_empty_file_returns_empty_list(tmp_path: Path) -> None:
    fp = tmp_path / "LEARNINGS.md"
    fp.write_text("", encoding="utf-8")
    entries = parse_learnings(fp, "proj", [])
    assert entries == []


def test_parse_learnings_whitespace_only_returns_empty_list(tmp_path: Path) -> None:
    fp = tmp_path / "LEARNINGS.md"
    fp.write_text("   \n\n  ", encoding="utf-8")
    entries = parse_learnings(fp, "proj", [])
    assert entries == []


def test_parse_learnings_nonexistent_file_returns_empty_list(tmp_path: Path) -> None:
    fp = tmp_path / "LEARNINGS.md"
    entries = parse_learnings(fp, "proj", [])
    assert entries == []


def test_parse_learnings_no_learning_headers_returns_empty_list(tmp_path: Path) -> None:
    doc = "# Just a heading\n\nSome content without learning entries.\n"
    fp = _make_learnings(tmp_path, doc)
    entries = parse_learnings(fp, "proj", [])
    assert entries == []


# ---------------------------------------------------------------------------
# Multiple entries: ordering and independence
# ---------------------------------------------------------------------------

def test_parse_learnings_order_preserved(tmp_path: Path) -> None:
    fp = _make_learnings(tmp_path, THREE_ENTRY_DOC)
    entries = parse_learnings(fp, "proj", [])
    assert entries[0].description == "Use word boundaries"
    assert entries[1].description == "pytest fixture scope"
    assert entries[2].description == "uv run ensures isolation"


def test_parse_learnings_entries_independent(tmp_path: Path) -> None:
    """Each entry's context only contains its own fields."""
    fp = _make_learnings(tmp_path, THREE_ENTRY_DOC)
    entries = parse_learnings(fp, "proj", [])
    # Entry 0 should not contain entry 1's content
    assert "Session-scoped fixtures" not in entries[0].context
    assert "partial matches" not in entries[1].context
