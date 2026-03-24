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
- Source in src/prompt_vc/, tests in tests/
- Use dataclasses for data models
- Use argparse for CLI
- YAML for all metadata/config (pyyaml)
- SHA256 for file/version hashing (hashlib, no external deps)
- .prompt-vc/ directory as local storage (git-inspired but NOT git)
- Snapshot files are copies, not symlinks
- Version IDs: auto-incrementing "v1", "v2", "v3"
- All file operations use pathlib.Path
- Tests use tmp_path fixture for isolated filesystem operations
- Include sample PROMPT_*.md fixtures in tests/fixtures/

## Backpressure
All must pass before committing:
1. `uv run ruff check .`
2. `uv run pytest`
3. No `@pytest.mark.skip`
