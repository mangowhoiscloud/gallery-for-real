# Operational Guide

## How to Run
```bash
# Build
uv build

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Typecheck
uv run mypy . 2>/dev/null || true
```

## Project Type
python-uv (package manager: uv)

## Architecture Decisions
- **Tokenizer**: Single regex `[^\W_']+(?:'[^\W_']+)*` handles all word-definition rules (Unicode, apostrophes, hyphens, underscores) without conditional logic
- **Counter**: `collections.Counter` with sort key `(-count, word)` for desc-count + alpha-tiebreak in one pass
- **Formatter**: Adaptive column widths computed from data; `+` separators match spec example exactly
- **CLI**: `argparse` with custom `_positive_int` type; `had_valid_input` flag for exit-code control; stdin read only when piped (not TTY)
- **Pipeline**: tokenize → count_words → format_table — each module is independently testable with no circular deps
- **Zero runtime deps**: stdlib-only (re, collections, dataclasses, argparse, sys)

## Patterns to Follow
- Single source of truth: no adapters, no migrations
- Test-first: write test → implement → verify
- Atomic commits: one logical change per commit

## Anti-Patterns
- Don't duplicate utilities — check shared code first
- Don't modify test assertions to make tests pass
- Don't leave console.log/print debugging statements
