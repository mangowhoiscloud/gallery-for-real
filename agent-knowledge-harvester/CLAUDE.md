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
- Source in src/agent_harvest/, tests in tests/
- Use dataclasses for data models (not Pydantic)
- Use argparse for CLI
- pyyaml for YAML rule output (allow_unicode=True for Korean content)
- No LLM/API dependencies — pure rule-based extraction with regex and heuristics
- All file operations use pathlib.Path
- Tests use tmp_path fixture with synthetic fixtures in tests/fixtures/
- Include realistic LEARNINGS.md, CLARITY_LOG.md, progress.txt fixtures from real harness runs
- Parse git log via subprocess.run (not GitPython) — minimize dependencies
- Stack detection: check for pyproject.toml, pom.xml, package.json, Cargo.toml, go.mod
- Category classification: keyword-based heuristic (not ML)
- Confidence scoring: count occurrences across projects (3+ = high, 2 = medium, 1 = low)
- Output YAML files must be valid and round-trip safe (yaml.safe_load → yaml.safe_dump)
- Handle missing files gracefully — skip and continue (never crash)

## Backpressure
All must pass before committing:
1. `uv run ruff check .`
2. `uv run pytest`
3. No `@pytest.mark.skip`
