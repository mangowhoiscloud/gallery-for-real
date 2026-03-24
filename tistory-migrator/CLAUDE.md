# Project Rules

## Build & Test
Commands are defined in `.harness-config`. Run `cat .harness-config` to see current settings.

## Conventions
- Read AGENTS.md for operational guide
- Read IMPLEMENTATION_PLAN.md for current task state
- Read progress.txt for recent session context
- Read CLARITY_LOG.md for resolved ambiguities from Socratic phase

## Rules
- ONE task per session. Pick the highest-priority TODO from IMPLEMENTATION_PLAN.md
- Search before assuming something isn't implemented
- Write tests alongside implementation. Target: 70% test code
- Capture the WHY in commit messages, not just the what
- Keep AGENTS.md under 60 lines. State goes in IMPLEMENTATION_PLAN.md
- Implement completely. No placeholders, no stubs, no TODOs in code
- If unrelated tests fail, fix them in this session

## Stack-Specific Rules
- Python 3.11+ with type hints on all functions
- uv as package manager (`uv run`, `uv build`, `uv run pytest`)
- Source in src/tistory_migrator/, tests in tests/
- Use dataclasses for data models, not Pydantic
- Use argparse for CLI (not click/typer) — keep dependencies minimal
- Requests for HTTP, BeautifulSoup + lxml for HTML parsing
- markdownify for HTML→Markdown conversion
- Test with pytest, mock external HTTP calls with unittest.mock
- All extractor strategies implement a common base interface
- Never make real HTTP calls in tests — mock everything
- Handle encoding properly (UTF-8 throughout, Korean content)
- Rate limiting: time.sleep between requests, configurable

## Backpressure
All must pass before committing:
1. `uv run ruff check .` — no lint errors
2. `uv run pytest` — all tests pass
3. No `@pytest.mark.skip` tests unless documented in IMPLEMENTATION_PLAN.md
