# LEARNINGS

### Learning: Use word boundaries in regex patterns
- Context: Building keyword classifier for category detection
- Discovery: Without `\b` word boundaries, "fix" matches "fixture" and "prefix", causing false positives. Always use exact `\b...\b` and add inflected forms explicitly.
- Rule: Add `\b` boundaries on both sides of keywords in category classifiers to prevent substring false-positives.

### Learning: pytest fixture scope affects teardown order
- Context: Writing integration tests with tmp_path and shared database fixtures
- Discovery: Session-scoped fixtures outlive function-scoped ones, so database connections can remain open after individual tests finish. This caused flaky teardown errors in CI.
- Rule: Use function scope for stateful fixtures (db connections, file handles) unless you explicitly need sharing across tests.

### Learning: uv run preserves virtual environment isolation
- Context: Running ruff check and pytest via uv during CI setup
- Discovery: `uv run ruff check .` automatically uses the project's venv without explicit activation. Running bare `ruff` may pick up a system-installed version with different config.
- Rule: Always prefix Python tool invocations with `uv run` in harness scripts to ensure consistent toolchain versions.

### Learning: dataclass field defaults must use field() for mutable types
- Context: Defining LearningEntry and HarvestResult dataclasses
- Discovery: Using `list()` or `{}` directly as a default value in a dataclass field causes all instances to share the same mutable object. Python raises a ValueError at class definition time.
- Rule: Use `field(default_factory=list)` or `field(default_factory=dict)` for mutable default values in dataclasses.

### Learning: ruff flags unused imports in test files
- Context: Writing test_utils.py with standard pytest imports
- Discovery: Imported `pytest` by reflex in a test file that only used tmp_path (which requires no explicit import). Ruff's F401 rule flags this even in test files.
- Rule: Only import pytest explicitly when using pytest.raises, pytest.mark, or other pytest symbols. tmp_path is injected without an explicit import.

### Learning: git log --stat insufficient for operation type detection
- Context: Implementing git log analyzer for FileChurn computation
- Discovery: `git log --stat` shows lines added/deleted per file but cannot distinguish between file creation (A), modification (M), and deletion (D). Need `--name-status` for operation tracking.
- Rule: Use `git log --name-status` for per-file operation codes (A/M/D/R) and `git log --numstat` for line counts. Never rely on --stat alone for revert detection.
