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
- uv as package manager
- Source in src/agent_replay/, tests in tests/
- Use dataclasses for data models (not Pydantic)
- Use argparse for CLI
- Textual for TUI (terminal user interface) — NOT curses or blessed
- rich for formatted text output in --summary mode
- Decimal for all monetary/cost values (not float)
- Handle malformed/missing log lines gracefully — never crash on bad input
- All file operations use pathlib.Path
- Tests use tmp_path fixture with synthetic log fixtures in tests/fixtures/
- Include realistic sample fixtures matching harness-for-real log format
- TUI tests: use Textual's pilot testing framework (app.run_test)
- Parse git log via subprocess.run (not GitPython) — minimize dependencies
- Timestamps: parse ISO 8601 with timezone awareness (datetime.fromisoformat)

## Backpressure
All must pass before committing:
1. `uv run ruff check .`
2. `uv run pytest`
3. No `@pytest.mark.skip`
