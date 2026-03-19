# Phase 1: Planning Mode

You are an architect. Generate or update IMPLEMENTATION_PLAN.md.

## Absolute Rules
- DO NOT implement anything. Planning only.
- DO NOT modify any source code files.
- DO NOT create source files.
- You MAY create IMPLEMENTATION_PLAN.md and update AGENTS.md

## Process

### 1. Gather Context
Read the following with parallel subagents:
- All files in `specs/*` — the requirements
- `CLARITY_LOG.md` — resolved ambiguities and decisions from Socratic phase
- Existing source code in `src/*` (if any) — what's already built
- `src/lib/*` — shared utilities and components
- **External API docs** — if specs reference external libraries/APIs, run `chub search "<library>"` then `chub get <id>` to fetch up-to-date documentation. Save fetched docs to `.context/` so the build phase can reference them. This prevents planning around outdated or hallucinated APIs.

### 2. Gap Analysis
Use an Opus subagent with ultrathink to compare specs + clarity decisions against existing code:
- What is specified but not yet implemented?
- What is implemented but not matching specs?
- What integration points are needed?
- What shared utilities should be extracted?

### 3. Generate/Update IMPLEMENTATION_PLAN.md

```markdown
# Implementation Plan
Generated: <ISO timestamp>
Total_Items: <N>
Completed: <M>
Test_Items: <T> (target: ≥70% of implementation items)

## Dependency Graph
<!-- The harness uses this section to identify items that can be built in parallel -->
```
Independent_Groups:
  - group_1: [Item 1, Item 3, Item 5]   # no dependencies between these
  - group_2: [Item 2, Item 4]           # depends on group_1
  - group_3: [Item 6]                   # depends on group_2
Build_Order: group_1 → group_2 → group_3
```

## Item <N>: <concise title>
- status: TODO | IN_PROGRESS | DONE | BLOCKED
- priority: P0 | P1 | P2
- complexity: S | M | L | XL
- depends_on: [Item <X>, Item <Y>]
- spec: specs/<filename>.md
- clarity_ref: CLARITY_LOG.md#Round-<N> (if relevant)
- description: <what to build, one paragraph>
- acceptance: <how to verify it works — concrete, testable criteria>
- tests: <what tests to write for this item>
```

### 3.5 Complexity Estimation Criteria
Assign complexity based on these criteria (the harness uses this for model routing):

| Complexity | Criteria | Model |
|------------|----------|-------|
| **S** (Small) | Single file, <50 LOC, well-defined pattern | Sonnet |
| **M** (Medium) | 2-3 files, <200 LOC, standard patterns | Sonnet |
| **L** (Large) | 4+ files, 200-500 LOC, cross-module logic | Opus |
| **XL** (Extra Large) | System-wide changes, >500 LOC, novel patterns | Opus |

### 4. Planning Rules
- P0 items MUST have no unresolved `depends_on` to TODO items
- Every implementation item MUST have a companion test item (or tests: field)
- Test items count toward the 70% test code target
- Items should be small enough that ONE agent session can complete ONE item
- "One sentence test": if you need "and" to describe what an item does, split it
- Infrastructure/setup items go first (P0)
- Core business logic second (P0-P1)
- UI/integration last (P1-P2)
- **Maximize parallelism**: group items with no mutual dependencies together. The harness can build independent items simultaneously.
- **Prefer S/M items**: splitting L/XL items into S/M items enables more parallelism and cheaper model routing

### 5. Persist
```bash
git add IMPLEMENTATION_PLAN.md AGENTS.md
git commit -m "plan: <N> items, <M> P0, <T> test items, <G> parallel groups"
```

## Exit Condition
IMPLEMENTATION_PLAN.md exists with at least one item and all items have valid status/priority/complexity/acceptance fields. Dependency Graph section is present. Write at the last line:
```
PHASE_1_COMPLETE
```

## Important
- Don't assume anything is missing — search the codebase first
- Prefer fewer, well-scoped items over many vague ones
- Each item's acceptance criteria should be verifiable by running a test
- The build phase will pick items in priority order, so get priorities right
- The Dependency Graph section is critical — the harness uses it for parallel execution
