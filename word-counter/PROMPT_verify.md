# Phase 3: Final Verification

You are a release engineer. Validate the entire project before declaring it complete.

## Process

### 1. State Check
- Read IMPLEMENTATION_PLAN.md — every item must have status: DONE
- If ANY item is TODO or IN_PROGRESS, do NOT proceed. Add a note and exit.

### 2. Full Test Suite
Run the complete test suite. Every test must pass. If any fail:
- Diagnose the root cause
- Fix it
- Re-run and confirm green
- Commit the fix

### 3. Static Analysis
Run typecheck and lint on the entire codebase. Fix any issues.

### 4. Multi-Agent Verification
Launch 3 verification subagents (use Opus for deep reasoning):

#### Subagent 1: Validator (Spec Compliance)
```
For each file in specs/:
  - Read the spec's requirements
  - Read CLARITY_LOG.md for resolved decisions
  - Search the implementation for each acceptance criterion
  - Report: PASS/FAIL per criterion with evidence
```

#### Subagent 2: Coordinator (Integration & Consistency)
```
Analyze the entire codebase for:
  - Cross-module integration: do all modules connect correctly?
  - Orphaned files: any source files not imported/used?
  - Dependency coherence: are all imports valid?
  - API consistency: do interfaces match between modules?
  - Error handling: are all error paths covered?
```

#### Subagent 3: Packer (Deployment Readiness)
```
Check:
  - All dependencies declared in package.json/pyproject.toml/Cargo.toml
  - Build produces a runnable artifact
  - No hardcoded paths, secrets, or dev-only configurations
  - README or entry point is clear
  - The project can be cloned and run from scratch
  - API usage matches docs: for key external libraries, run `chub get <id>` and verify
    that the implementation uses current API signatures (not deprecated/hallucinated ones)
```

### 5. Review LEARNINGS.md
Read LEARNINGS.md and verify that all runtime learnings were properly applied:
- Check if any learning contradicts the final implementation
- Verify API annotations match actual usage
- Compile a final "Architecture Decisions" summary for AGENTS.md

### 6. Aggregate Results
Collect reports from all 3 subagents. For each FAIL:
- Create a new item in IMPLEMENTATION_PLAN.md with status: TODO, priority: P0, complexity: S or M
- The harness will loop back to Phase 2 to fix these

### 7. Decision Gate
**IF** all 3 subagents report ALL PASS:
```
Append to progress.txt:
---
HARNESS_COMPLETE
Verification Report:
  Validator: ALL PASS (<N> criteria checked)
  Coordinator: ALL PASS (<N> modules checked)
  Packer: ALL PASS (<N> checks)
  Learnings_Applied: <N> of <M>
Timestamp: <ISO timestamp>
---
```

```bash
git add -A
git commit -m "verify: all checks passed, harness complete"
git tag -a "v$(date +%Y%m%d-%H%M)" -m "Ralphton submission"
```

**IF** any subagent reports FAIL:
```
Append to progress.txt:
---
VERIFICATION_FAILED
Failures: <count>
New items added to IMPLEMENTATION_PLAN.md
Looping back to build phase.
---
```

```bash
git add -A
git commit -m "verify: <N> failures found, items added to plan"
```

Do NOT write HARNESS_COMPLETE. The harness will return to Phase 2.

## Important
- Be thorough but not pedantic. Focus on functional correctness, not style preferences.
- The goal is a working, demonstrable product for Ralphton judges.
- If a spec requirement is genuinely out of scope (marked SPEC_GAP_CRITICAL in CLARITY_LOG.md), skip it.
