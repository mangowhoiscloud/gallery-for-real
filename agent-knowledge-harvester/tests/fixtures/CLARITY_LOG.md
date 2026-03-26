# CLARITY_LOG

## Round 1

### Specs Analyzed
- `specs/agent.md` — Full feature spec for the agent pipeline

### Ambiguities

```
Round: 1
Spec: agent.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: What format should the LEARNINGS.md file follow? The spec mentions extracting
learning entries but does not show the input format.
A: Inspection of real harness outputs shows a consistent structure: H3 headers
(`### Learning: [title]`) followed by three sub-bullet fields (`- Context:`,
`- Discovery:`, `- Rule:`). Multiple projects in the examples directory confirm
this pattern.
Confidence: 0.95
Remaining_Ambiguity: Minor variations in spacing and missing sub-bullets must be
handled gracefully.
Resolution: Parse LEARNINGS.md by splitting on `### Learning:` headers. Extract
Context, Discovery, and Rule from `- Context:`, `- Discovery:`, `- Rule:` prefixed
lines. Handle missing fields with empty strings. The `description` field maps to
the title, `context` combines Context + Discovery.
---
```

```
Round: 1
Spec: agent.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: CRITICAL
Q: How should the confidence score be computed when learnings appear in multiple
projects? The spec says "same learning repeated across 2+ projects = high
confidence" but does not define what constitutes the same learning.
A: Without semantic similarity (no LLM), matching must be keyword-based. Two
learnings are considered the same when they share the same category AND at least
one stack tag AND have a Jaccard similarity >= 0.4 on tokenized description words
after removing common stopwords.
Confidence: 0.75
Remaining_Ambiguity: The 0.4 threshold is a tunable heuristic. May need adjustment
after real-world testing across diverse projects.
Resolution: Use category + stack overlap as primary grouping filter, then apply
Jaccard similarity >= 0.4 on tokenized description words. Confidence levels: 3+
source projects = high, 2 = medium, 1 = low. Document threshold as configurable.
---
```

```
Round: 1
Spec: agent.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: The spec instructs using `git log --stat` to count file-level changes, but
--stat only shows line counts, not operation types (add vs modify vs delete).
How can add_count, modify_count, and delete_count be populated separately?
A: Two git commands are needed. First, `git log --name-status --format="%H"` to
get per-file operation codes (A=added, M=modified, D=deleted, R=renamed) per
commit. Second, `git log --numstat --format="%H"` for per-file line change counts.
Combine results per file.
Confidence: 0.95
Remaining_Ambiguity: None — the solution is unambiguous.
Resolution: Run `git log --name-status --format="%H"` for operation tracking and
`git log --numstat --format="%H"` for line counts. R (rename) counts as a modify
to avoid inflating add/delete counts. Non-git directories return empty results
gracefully.
---
```

## Round 2

```
Round: 2
Spec: agent.md
Category: EDGE_CASE
Severity: MINOR
Q: What output should --dry-run produce? The spec says parsing happens but no
files are written, but a completely silent dry run is unhelpful.
A: Standard CLI convention is to print a summary to stdout showing what would be
generated without actually writing anything. The user needs to see extraction
counts and file list.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: --dry-run performs all parsing and analysis but skips file I/O. Print
to stdout: total learnings extracted, total rules synthesized, list of output files
that would be created, category and stack distribution. Essentially print the
HarvestResult summary.
---
```

```
Round: 2
Spec: agent.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: Does --stack filter entire projects or individual rules? In gallery mode these
have different meanings and performance implications.
A: Filtering at the rule output level is simpler and consistent between single-
project and gallery modes. A Python project may still produce Docker or git rules
that are cross-stack useful.
Confidence: 0.85
Remaining_Ambiguity: None significant for v1 scope.
Resolution: --stack filters at rule output time after full synthesis. All projects
are analyzed, but only rules whose stacks list contains the specified stack are
included in output files. Consistent across both single-project and gallery modes.
---
```
