# CLARITY_LOG

## Round 1

### Spec Analyzed
- `specs/prompt-vcs.md` — Prompt Version Control CLI tool
- `CLAUDE.md` — Stack-specific project constraints

---

### Ambiguities

```
Round: 1
Spec: prompt-vcs.md
Category: CONTRADICTION
Severity: CRITICAL
Q: The core concepts section says Version has a "해시 기반 ID" (hash-based ID), but CLAUDE.md says "Version IDs: auto-incrementing 'v1', 'v2', 'v3'". Which is the actual version identifier?
A: The metadata.yaml example resolves this: versions use auto-incrementing IDs ("v1", "v2", "v3") as the primary identifier, with a separate `hash` field for content integrity. The "해시 기반 ID" description in the overview is misleading — the hash is a content fingerprint, not the version identifier. CLAUDE.md is authoritative since it was written as implementation constraints.
Confidence: 0.95
Remaining_Ambiguity: None — CLAUDE.md explicitly states auto-incrementing.
Resolution: Version IDs are auto-incrementing ("v1", "v2", ...). Each version also stores a SHA256 content hash for integrity, but the hash is NOT the ID.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: CONTRADICTION
Severity: CRITICAL
Q: Binding files are named `.json` (e.g., `v3_run1.json`) but the example content uses YAML syntax. CLAUDE.md mandates "YAML for all metadata/config". What format should binding files use?
A: CLAUDE.md is authoritative: "YAML for all metadata/config (pyyaml)". The `.json` filenames in the spec are an oversight. The `bind` command's `--result` flag takes an external JSON file as input (the harness output), but the stored binding should be YAML.
Confidence: 0.90
Remaining_Ambiguity: The naming convention for stored binding files — should they be `.yaml` instead of `.json`?
Resolution: Stored binding files use YAML format with `.yaml` extension (e.g., `v3_run1.yaml`). The `--result` flag accepts external JSON files as input, which get parsed and stored as YAML bindings.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The `bind` command takes `--result results/run_20260320.json` but the schema of this external result file is never defined. What fields are required? What format?
A: The binding example shows the output metrics: success, test_pass_rate, total_tests, total_iterations, total_time_seconds, estimated_cost, items_completed, stuck_count. The input file likely comes from a test harness and contains at minimum these fields. Since the flag name is `--result` and the example path suggests a run output, the tool should accept a JSON file with at least a `metrics` object.
Confidence: 0.70
Remaining_Ambiguity: Are all metric fields mandatory? Can the result file have additional fields that get preserved?
Resolution: The `--result` file must be valid JSON. Required top-level fields: `benchmark` (str), `agent` (str). Required `metrics` fields: `success` (bool), `test_pass_rate` (float). All other metrics fields shown in the spec are optional. Additional fields in the input are preserved in the binding. The tool adds `version` and `timestamp` automatically.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: Where is `.prompt-vc/` created relative to `--dir`? Commands like `log`, `diff`, `compare`, `trend` don't take `--dir` — how do they find `.prompt-vc/`?
A: By analogy with `.git/`, `.prompt-vc/` should be created in the current working directory when `init` is run. The `--dir` flag specifies where the source prompt files live, not where `.prompt-vc/` goes. Commands without `--dir` discover `.prompt-vc/` in cwd.
Confidence: 0.90
Remaining_Ambiguity: Should the tool search parent directories (like git does)?
Resolution: `.prompt-vc/` is always created in and discovered from cwd. No parent directory traversal — keep it simple. The `--dir` flag on `init`/`snapshot`/`checkout` specifies the source/target directory for prompt files, stored in `config.yaml` so subsequent commands know where to find prompts.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What constitutes a "Prompt Set"? How does the tool know which files to snapshot? Is it a glob pattern? Everything in `--dir`?
A: The spec mentions "PROMPT_*.md" as example files and config.yaml stores "추적 대상 파일 패턴" (tracking target file patterns). The `init --dir` command should record the directory and a default glob pattern.
Confidence: 0.85
Remaining_Ambiguity: Should the default pattern be `PROMPT_*.md` or `*.md` or everything in the dir?
Resolution: Default file pattern is `PROMPT_*.md` (matching the spec examples). Stored in `config.yaml` as `file_pattern`. Users can change this in config.yaml. The `snapshot` command captures all files matching the pattern in the configured directory.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What should `compare` do when versions have multiple bindings (e.g., v3 has v3_run1 and v3_run2)? What if versions were run on different benchmarks?
A: The spec shows the compare output filtered by benchmark ("Benchmark: word-counter"). With multiple runs, the tool needs a strategy for selecting which run to compare.
Confidence: 0.75
Remaining_Ambiguity: Aggregation strategy for multiple runs.
Resolution: `compare` groups bindings by benchmark. If a version has multiple runs for the same benchmark, use the latest run. If versions share no common benchmarks, report an error. `compare` can optionally take `--benchmark <name>` to filter explicitly.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What happens on `checkout` if the working directory has un-snapshotted changes? Should there be a safety check or `--force` flag?
A: By analogy with git, overwriting uncommitted work silently is dangerous. However, this is a simpler tool than git, so a lightweight safety model is appropriate.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: `checkout` checks if current files differ from the latest snapshot. If they do, abort with a warning: "Unsaved changes detected. Run `snapshot` first or use `--force` to discard." The `--force` flag skips the safety check.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: There is no concept of "current version" or HEAD. After `checkout v2`, what is the parent of the next `snapshot`?
A: Without tracking current state, the parent chain breaks after checkout. The tool needs to know which version is currently checked out to set the correct parent on the next snapshot.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: `config.yaml` (or `index.yaml`) stores a `current_version` field that tracks the active version. After `checkout v2`, `current_version` is set to "v2". The next `snapshot` creates a new version with `parent: "v2"`. After `snapshot` creating v4, `current_version` becomes "v4". `init` sets `current_version` to null (no version yet).
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What is the schema and purpose of `index.yaml`?
A: Given the storage structure, index.yaml likely serves as the version registry — a quick lookup of all versions without scanning the snapshots/ directory.
Confidence: 0.85
Remaining_Ambiguity: Exact fields.
Resolution: `index.yaml` contains: `current_version` (str or null), `versions` (list of {version, hash, message, timestamp, parent}). This is a denormalized index for fast lookups by `log` and other commands. It is the source of truth for version ordering and the next version number.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What is the schema of `config.yaml`?
A: config.yaml is mentioned as storing settings including file patterns. Based on the tool's needs, it must store at minimum the prompt directory and file pattern.
Confidence: 0.85
Remaining_Ambiguity: None significant.
Resolution: `config.yaml` schema: `prompt_dir` (str, the --dir path from init), `file_pattern` (str, default "PROMPT_*.md"). Keep it minimal — index.yaml handles version state.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: EDGE_CASE
Severity: MAJOR
Q: What is the `parent` of v1 (the first version)?
A: v1 has no predecessor. The field should be null/omitted.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: For v1, `parent` is `null` in YAML (rendered as `parent: null` or omitted entirely). Use `null` explicitly for clarity.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: How is the SHA256 hash computed? Per-file hashes are shown, but there's also a top-level `hash` for the entire version. Hash of what?
A: The top-level hash should represent the entire prompt set at that version. A natural approach is to hash the sorted concatenation of individual file hashes.
Confidence: 0.85
Remaining_Ambiguity: Exact algorithm.
Resolution: Per-file hash: SHA256 of file contents. Version-level hash: SHA256 of the sorted concatenation of "filename:filehash" strings joined by newlines. This ensures the version hash changes if any file changes, and is deterministic regardless of file processing order. Hashes are stored as full 64-char hex strings (the spec's "a1b2c3d4" was just an abbreviated example).
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: The `trend` command mentions "ASCII 차트 (터미널) 또는 HTML 차트". When is each format used?
A: The report module has separate files for terminal.py, html.py, and markdown.py, suggesting output format is selectable.
Confidence: 0.80
Remaining_Ambiguity: Flag name.
Resolution: Default output is terminal (ASCII table/chart). `--format html` produces HTML output. `--format markdown` produces Markdown. This applies to `compare` and `trend` commands. `diff` and `log` are terminal-only for v1.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: MISSING_ERROR_HANDLING
Severity: MINOR
Q: What happens when `snapshot` is called with no changes since the last snapshot?
A: Creating identical snapshots wastes space and adds noise to the log. The tool should detect this.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: If all files match the latest snapshot's hashes, abort with message: "No changes detected since {version}. Snapshot not created." No `--force` override needed for this case — if files haven't changed, there's nothing to snapshot.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: EDGE_CASE
Severity: MINOR
Q: How are binding run IDs (e.g., "run1", "run2") generated?
A: The naming pattern `v3_run1.yaml` needs a generation scheme. It should be auto-incremented per version.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Run IDs are auto-incremented per version by scanning existing binding files. First bind for v3 creates `v3_run1.yaml`, second creates `v3_run2.yaml`, etc. The run number is determined by counting existing bindings for that version + 1.
---
```

```
Round: 1
Spec: prompt-vcs.md
Category: EDGE_CASE
Severity: MINOR
Q: What happens when `diff`, `checkout`, `bind`, or `compare` reference a non-existent version?
A: Standard error handling — these should fail gracefully.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: All commands that take version arguments validate against index.yaml. If a version doesn't exist, exit with error: "Version '{v}' not found. Run `prompt-vc log` to see available versions." Exit code 1.
---
```

---

### Cross-Spec Consistency Check

**Contradictions found:** 2
1. "해시 기반 ID" (spec overview) vs "auto-incrementing v1, v2, v3" (CLAUDE.md) — resolved in favor of CLAUDE.md.
2. `.json` binding filenames (spec) vs "YAML for all metadata/config" (CLAUDE.md) — resolved: stored bindings use YAML format.

**Integration points with no owner:** 1
1. `--result` input file schema — neither spec nor CLAUDE.md defines the expected format of the external result JSON file. Resolved with reasonable defaults above.

**Implicit dependencies verified:**
- `init` must run before any other command (creates `.prompt-vc/`)
- `snapshot` must run before `diff`, `checkout`, `log` (creates versions)
- `bind` must run before `compare`, `trend` (creates bindings)
- `index.yaml` is the central registry, read by most commands

**Architecture coexistence:** Single spec, no cross-spec conflicts. All commands share `.prompt-vc/` storage through `storage.py` module.

---

### Ambiguity Score

```
AMBIGUITY_SCORE: 0.06
Rounds_Completed: 1
Ambiguities_Found: 16
Ambiguities_Resolved: 15
Ambiguities_Remaining: 1
```

The single remaining ambiguity is low-severity: whether the `--result` file can contain arbitrary extra fields beyond the required ones. This is MINOR and resolved with "preserve additional fields."

### Convergence Data

```
CONVERGENCE_DATA:
  round: 1
  score: 0.06
  prev_score: 1.0
  delta: -0.94
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 1
  stagnation_count: 0
```

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.06
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
