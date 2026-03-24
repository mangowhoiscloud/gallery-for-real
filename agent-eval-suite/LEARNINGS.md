# Learnings

### Learning: pytest exits 5 on empty collection
- Context: Item 1 scaffolding — running pytest on empty tests/ directory
- Discovery: pytest returns exit code 5 (not 0) when no tests are collected. The plan said "exits 0 (no tests collected is OK)" which is aspirational, not literal.
- Rule: Always include at least one test file (even a trivial import check) so pytest collects ≥1 item and exits 0. Backpressure requires exit 0.

### Learning: TestData class name triggers pytest collection warning
- Context: Item 2 data models — TestData is an intermediate parser type
- Discovery: Any class named Test* imported into a test file causes pytest to attempt collection. Dataclasses have __init__, so pytest emits PytestCollectionWarning and skips it. Tests still pass — warning is benign.
- Rule: Avoid naming non-test classes with Test* prefix when they'll be imported in test files. Use ParsedTestData, TestOutput, or similar to sidestep the warning.

### Learning: SVG attribute order affects regex test introspection
- Context: Item 14 — radar chart SVG helper
- Discovery: Test regex `<polygon[^>]*fill-opacity="0.2"[^>]*points="([^"]+)"` requires `fill-opacity` to appear before `points` in the tag. The initial implementation had `points` first, causing zero regex matches.
- Rule: When writing SVG generators that tests will introspect via regex, place discriminating/filtering attributes (e.g., `fill-opacity`) before positional/value attributes (e.g., `points`) in the element tag.

### Learning: SVG legend elements inflate <rect> count tests
- Context: Item 14 — stacked bar chart legend
- Discovery: Using `<rect>` for legend swatches added N extra rects to the count, breaking `test_bar_rect_count_matches_phase_segments` (expected 5, got 8 for 3 phases + 3 legend rects).
- Rule: For SVG helpers where tests count `<rect>` elements to verify data, use a different shape (e.g., `<circle>`) for decorative legend elements to keep data counts clean.

### Learning: Guard tests for unimplemented modules must be updated when module ships
- Context: Item 15 ClaudeBackend — test_cli.py had two tests with `pytest.raises(ImportError)` guarding against the not-yet-existing backends/claude.py
- Discovery: These tests became false failures the session the module was implemented. The full suite showed 2 failures that were not about the new code being wrong.
- Rule: After implementing any module previously guarded with `pytest.raises((ImportError, ModuleNotFoundError))`, grep test files for those guards and update them to assert the now-correct behavior.
