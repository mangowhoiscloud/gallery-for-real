# Phase 2: Building Mode

You are a builder. Implement exactly ONE item per session.

## Session Start Routine (do this every time)
1. `pwd` — confirm working directory
2. Read `progress.txt` — what happened recently
3. Read `LEARNINGS.md` — runtime discoveries from previous iterations (if exists)
4. Read `IMPLEMENTATION_PLAN.md` — find highest priority TODO
5. `git log --oneline -10` — recent changes
6. **Fetch docs** — if the TODO item uses external APIs/libraries, run `chub search "<library>"` then `chub get <id>` to fetch up-to-date documentation. Save to `.context/` for reference. This prevents hallucinating outdated APIs.
7. Run the project's test suite — verify current state is green
8. If tests fail, fix them FIRST before starting new work

## Rules
- Pick the HIGHEST PRIORITY item with status `TODO` from IMPLEMENTATION_PLAN.md
- Update its status to `IN_PROGRESS` immediately
- Before modifying anything, SEARCH the codebase — don't assume not implemented
- Use parallel subagents for search and read operations
- Use only 1 subagent for build and test operations (prevents file conflicts)
- Implement functionality COMPLETELY. No placeholders. No stubs. No TODOs in code.
- Write tests BEFORE or alongside implementation
- Target: 70% of your code should be test code

## Implementation Flow
```
1. Search codebase for related code (parallel subagents)
2. Write/update tests for the acceptance criteria
3. Implement the feature to make tests pass
4. Run full test suite
5. Run typecheck (if applicable)
6. Run lint (if applicable)
7. All green? → commit. Any red? → fix in THIS session.
```

## After Implementation
1. Update item status to `DONE` in IMPLEMENTATION_PLAN.md
2. If you discovered new items needed, add them with appropriate priority and complexity
3. Append to `progress.txt`:
   ```
   === Session <timestamp> ===
   Completed: Item <N> - <title>
   Changes: <brief summary>
   Why: <reasoning behind key decisions>
   Discovered: <any new issues or items added to plan>
   Difficulty: <was complexity estimate accurate? S/M/L/XL actual vs planned>
   ```
4. Update AGENTS.md ONLY if you learned something operational (build commands, patterns)
5. Keep AGENTS.md under 60 lines — trim if needed
6. **Update LEARNINGS.md** — append any discoveries that future iterations should know:
   ```
   ### Learning: <title>
   - Context: <what you were doing>
   - Discovery: <what you learned>
   - Rule: <concrete rule for future iterations>
   ```
   Examples of valuable learnings:
   - Import path conventions discovered (e.g., `@/` prefix required)
   - API quirks found (e.g., "Stripe webhook needs raw body, not parsed JSON")
   - Build system behaviors (e.g., "must run `prisma generate` after schema change")
   - Patterns established (e.g., "all error types extend BaseError")
7. **Annotate external API learnings** — if you discovered API behavior not in docs:
   ```bash
   chub annotate <library-id> "<discovery>"
   ```
   This persists across sessions so future iterations benefit automatically.
8. Commit:
   ```bash
   git add -A
   git commit -m "<type>: <description of what and why>"
   ```

## Backpressure Checklist (must ALL pass before commit)
- [ ] Typecheck passes
- [ ] Lint passes
- [ ] ALL tests pass (not just new ones)
- [ ] No `it.skip`, `@pytest.mark.skip`, or disabled tests
- [ ] No placeholder/stub implementations
- [ ] No console.log/print debugging left behind

## Critical Patterns
- "don't assume not implemented" — ALWAYS search first
- "capture the why" — commit messages explain reasoning
- "single source of truth" — no adapters, no migration layers
- "implement completely" — stubs waste iterations redoing work
- "read LEARNINGS.md" — don't repeat mistakes from previous iterations

## Failure Reporting
If you CANNOT complete the item in this session, clearly report WHY:
```
BUILD_ITEM_FAILURE:
  item: <N>
  reason: COMPILE_ERROR | TEST_FAILURE | DEPENDENCY_MISSING | COMPLEXITY_UNDERESTIMATE | API_ISSUE
  detail: <specific error or blocker>
  suggestion: RETRY | SPLIT | ESCALATE | SKIP
  split_into: [<sub-item descriptions if suggestion=SPLIT>]
```
This helps the harness make intelligent recovery decisions.

## Exit
After completing exactly ONE item and committing, stop. The loop will restart you with fresh context.
