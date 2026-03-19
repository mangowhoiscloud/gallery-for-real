# LEARNINGS — runtime discoveries for future iterations

### Learning: Install package before running tests
- Context: Running `uv run pytest` after writing the first module
- Discovery: The package is not installed by default; `ModuleNotFoundError` is thrown
- Rule: Always run `uv pip install -e .` once per fresh venv before `uv run pytest`

### Learning: Dev tools need explicit `uv add --dev`
- Context: Running ruff and mypy from `.harness-config` commands
- Discovery: pyproject.toml had no `[dependency-groups]` / `[tool.uv.dev-dependencies]`,
  so ruff and mypy were not present in the venv
- Rule: Run `uv add --dev pytest ruff mypy` at session start if tools are missing

### Learning: ruff E741 forbids single-letter `l` as a loop variable
- Context: Writing list comprehensions in test_cli.py using `l` as the iteration variable
- Discovery: ruff's E741 rule flags `l` (lowercase L) as ambiguous with `1` (one) and `I` (uppercase i)
- Rule: Use `ln` or another unambiguous name instead of `l` in list comprehensions and loops
