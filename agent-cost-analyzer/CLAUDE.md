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
- Source in src/agent_cost_analyzer/, tests in tests/
- Use dataclasses for data models
- Use argparse for CLI
- Include sample harness log fixtures in tests/fixtures/ (real format from gallery projects)
- Jinja2 for HTML dashboard template with inline Chart.js (CDN link)
- HTML report must be a single self-contained file (no external assets except CDN)
- Parse cost.log line format: `{timestamp} phase={phase} iter={iter} model={model} in={in} out={out} cost=${cost} cumulative=${cumul} item={item}`
- Handle missing/malformed log lines gracefully (skip + warn)
- All monetary values as Decimal, not float

## Backpressure
All must pass before committing:
1. `uv run ruff check .`
2. `uv run pytest`
3. No `@pytest.mark.skip`
