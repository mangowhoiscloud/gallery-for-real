# Implementation Plan
Generated: 2026-03-24T15:10:00+09:00
Total_Items: 14
Completed: 0
Test_Items: 7 (target: ≥70% of implementation items)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3]       # models, hashing, storage — no mutual deps
  - group_2: [Item 4, Item 5]               # init + snapshot — depend on group_1
  - group_3: [Item 6, Item 7, Item 8]       # log, diff, checkout — depend on group_2
  - group_4: [Item 9, Item 10]              # bind + compare — depend on group_2
  - group_5: [Item 11]                      # trend — depends on group_4
  - group_6: [Item 12]                      # CLI wiring — depends on all commands
  - group_7: [Item 13, Item 14]             # output formats + fixtures — depend on group_6
Build_Order: group_1 → group_2 → group_3 + group_4 → group_5 → group_6 → group_7
```

## Item 1: Data models (dataclasses)
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1
- description: Define dataclasses for VersionMeta (version, hash, message, timestamp, files dict, parent), BindingMeta (version, benchmark, agent, timestamp, metrics dict), IndexData (current_version, versions list), and ConfigData (prompt_dir, file_pattern). All fields typed. Place in `src/prompt_vc/models.py`.
- acceptance: Import all models, instantiate each with valid data, verify field access and types. Verify VersionMeta.parent can be None. Verify ConfigData defaults (file_pattern="PROMPT_*.md").
- tests: tests/test_models.py — construct each model, assert fields, test default values, test optional fields (parent=None).

## Item 2: SHA256 hashing utilities
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (SHA256 computation)
- description: Implement `hash_file(path) -> str` (SHA256 of file contents) and `hash_version(files: dict[str, str]) -> str` (SHA256 of sorted "filename:hash\n" pairs). Place in `src/prompt_vc/hashing.py`. Use only hashlib, no external deps.
- acceptance: hash_file returns consistent SHA256 hex for known content. hash_version returns deterministic hash for same file set regardless of insertion order.
- tests: tests/test_hashing.py — test with known content/expected hashes, test ordering independence, test empty file, test unicode content.

## Item 3: Storage layer (YAML I/O + directory operations)
- status: DONE
- priority: P0
- complexity: M
- depends_on: []
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1
- description: Implement storage utilities in `src/prompt_vc/storage.py`: read/write YAML files, ensure `.prompt-vc/` structure exists, read/write config.yaml and index.yaml, discover prompt files by glob pattern, copy files to snapshot directory. All operations use pathlib.Path.
- acceptance: Can create `.prompt-vc/` directory tree, write and read back config.yaml and index.yaml with correct schema, discover PROMPT_*.md files, copy files preserving content.
- tests: tests/test_storage.py — use tmp_path to create/read config, index, discover files, copy snapshots. Verify YAML round-trip fidelity.

## Item 4: `init` command
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 3]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (.prompt-vc/ location)
- description: Implement `init(dir: Path)` in `src/prompt_vc/commands/init.py`. Creates `.prompt-vc/` in current working directory, writes default config.yaml (prompt_dir from --dir, file_pattern="PROMPT_*.md"), writes empty index.yaml (current_version=null, versions=[]). Creates snapshots/ and bindings/ subdirs. Error if already initialized.
- acceptance: Running init creates correct directory structure. Running init twice errors. Config and index files are valid YAML with correct defaults.
- tests: tests/test_init.py — init fresh dir, verify structure; init twice, verify error; verify config/index content.

## Item 5: `snapshot` command
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3, Item 4]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (version ID, no-changes, hash scheme)
- description: Implement `snapshot(dir: Path, message: str)` in `src/prompt_vc/commands/snapshot.py`. Discovers prompt files, computes per-file and version hashes, compares against latest version hash (if any) to detect no-change, creates v<N+1> snapshot directory, copies files, writes metadata.yaml, updates index.yaml (appends version, sets current_version). Abort with message if no changes detected.
- acceptance: First snapshot creates v1 with parent=null. Second snapshot creates v2 with parent=v1. Duplicate content aborts. Metadata contains correct hashes. Index reflects new version.
- tests: tests/test_snapshot.py — first snapshot, sequential snapshots, no-change detection, hash correctness, metadata fields validation.

## Item 6: `log` command
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 3]
- spec: specs/prompt-vcs.md
- description: Implement `log()` in `src/prompt_vc/commands/log.py`. Reads index.yaml, prints version list with version ID, message, timestamp, and hash (truncated). Mark current version with asterisk. Output to stdout.
- acceptance: Lists all versions in reverse chronological order. Current version marked. Empty repo shows "No versions yet."
- tests: tests/test_log.py — empty log, single version, multiple versions, current version marking.

## Item 7: `diff` command
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3]
- spec: specs/prompt-vcs.md
- description: Implement `diff(v1: str, v2: str)` in `src/prompt_vc/commands/diff.py`. Loads snapshot files for both versions, produces unified diff per file. Handles files added/removed between versions. Uses difflib.unified_diff. Errors on non-existent versions.
- acceptance: Shows unified diff for changed files. Shows "new file" for additions, "deleted file" for removals. Non-existent version returns error with helpful message.
- tests: tests/test_diff.py — diff identical versions, diff with changes, diff with added/removed files, non-existent version error.

## Item 8: `checkout` command
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 2, Item 3]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (checkout safety, --force)
- description: Implement `checkout(version: str, dir: Path, force: bool)` in `src/prompt_vc/commands/checkout.py`. Compares current working files against current version's snapshot to detect unsaved changes. If changes exist and no --force, warn and abort. Otherwise, copy snapshot files to working directory and update current_version in config.yaml. Error on non-existent version.
- acceptance: Checkout restores files correctly. Unsaved changes blocked without --force. --force overwrites. current_version updated. Non-existent version errors.
- tests: tests/test_checkout.py — clean checkout, dirty checkout blocked, dirty checkout with force, non-existent version, current_version updated.

## Item 9: `bind` command
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 1, Item 3]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (binding schema, run ID auto-increment)
- description: Implement `bind(version: str, result_file: Path)` in `src/prompt_vc/commands/bind.py`. Reads JSON result file, validates required fields (benchmark, agent, success, test_pass_rate), auto-generates run ID by scanning existing bindings for this version, writes binding YAML to `.prompt-vc/bindings/v<N>_run<M>.yaml`. Error on non-existent version or invalid JSON.
- acceptance: Creates correctly named binding file. Run IDs auto-increment. Required fields validated. Optional metrics preserved. Invalid input errors gracefully.
- tests: tests/test_bind.py — bind valid result, auto-increment run ID, missing required field, non-existent version, multiple bindings per version.

## Item 10: `compare` command
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 9]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (multiple runs, common benchmarks)
- description: Implement `compare(v1: str, v2: str, benchmark: str | None)` in `src/prompt_vc/commands/compare.py`. Loads bindings for both versions, uses latest run per benchmark, finds common benchmarks (or filters by --benchmark), builds side-by-side comparison table with deltas. Error if no common benchmarks.
- acceptance: Shows metric comparison with deltas (+ or -). Filters by benchmark if specified. Fails if no common benchmarks. Uses latest run when multiple exist.
- tests: tests/test_compare.py — compare with common benchmarks, no common benchmarks error, --benchmark filter, latest run selection, delta calculation.

## Item 11: `trend` command
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 3, Item 9]
- spec: specs/prompt-vcs.md
- description: Implement `trend()` in `src/prompt_vc/commands/trend.py`. Loads all versions and their bindings, builds time-series data per metric across versions. Outputs table showing metric progression. Groups by benchmark if multiple exist.
- acceptance: Shows metric values across versions in chronological order. Handles versions with no bindings (skip or show "—"). Groups by benchmark.
- tests: tests/test_trend.py — trend with multiple versions and bindings, versions without bindings, single version, empty repo.

## Item 12: CLI entry point (argparse wiring)
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 4, Item 5, Item 6, Item 7, Item 8, Item 9, Item 10, Item 11]
- spec: specs/prompt-vcs.md
- description: Implement `main()` in `src/prompt_vc/cli.py` using argparse with subcommands: init, snapshot, log, diff, checkout, bind, compare, trend. Wire each subcommand to its handler. Handle --dir, --message, --force, --result, --benchmark, --format flags. Include `__init__.py` for package. Exit codes: 0 success, 1 error.
- acceptance: `prompt-vc init --dir .` calls init. `prompt-vc snapshot --message "test"` calls snapshot. All flags parsed correctly. Unknown commands show help. Errors exit with code 1.
- tests: tests/test_cli.py — parse each subcommand with args, verify handler dispatch, verify error handling and exit codes.

## Item 13: Output format support (terminal, HTML, markdown)
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 10, Item 11]
- spec: specs/prompt-vcs.md
- clarity_ref: CLARITY_LOG.md#Round-1 (output format selection)
- description: Implement formatters in `src/prompt_vc/formatters.py`: terminal (default, plain text tables), HTML (jinja2 template), markdown. Used by compare and trend commands via --format flag. Terminal is default.
- acceptance: compare --format html produces valid HTML. compare --format markdown produces valid markdown table. Default output is plain text. Jinja2 templates render without error.
- tests: tests/test_formatters.py — each format for compare output, each format for trend output, verify HTML structure, verify markdown table syntax.

## Item 14: Test fixtures (sample PROMPT_*.md files)
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/prompt-vcs.md
- description: Create `tests/fixtures/` with sample prompt files: PROMPT_system.md, PROMPT_user.md, PROMPT_tools.md. Also create a sample result JSON file (valid_result.json) and an invalid one (invalid_result.json). Create `tests/conftest.py` with shared fixtures for initialized repos, snapshot repos, etc. using tmp_path.
- acceptance: Fixture files exist with meaningful content. conftest.py provides reusable fixtures. All fixture-dependent tests can import and use them.
- tests: N/A (this IS test infrastructure)

PHASE_1_COMPLETE
