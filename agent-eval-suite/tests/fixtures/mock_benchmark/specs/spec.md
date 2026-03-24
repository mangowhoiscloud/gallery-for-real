# Mock Benchmark Specification

This is a minimal benchmark used for testing the agent-eval runner itself.

## Requirements

1. Implement a trivial function that returns "hello world".
2. Write tests for it.
3. Lint and typecheck must pass.

## Acceptance Criteria

- `uv run pytest` passes with at least 1 test.
- `uv run ruff check .` passes with no errors.
