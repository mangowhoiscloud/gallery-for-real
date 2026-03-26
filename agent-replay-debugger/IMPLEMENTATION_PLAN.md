# Implementation Plan
Generated: 2026-03-24T19:00:00+09:00
Total_Items: 19
Completed: 2
Test_Items: 19 (target: ≥70% of implementation items)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2]
  - group_2: [Item 3, Item 4, Item 5, Item 6, Item 7, Item 8, Item 9]
  - group_3: [Item 10, Item 11]
  - group_4: [Item 12, Item 13, Item 14, Item 15]
  - group_5: [Item 16, Item 18]
  - group_6: [Item 17, Item 19]
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5 → group_6
```

## Item 1: Data Models
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-4, CLARITY_LOG.md#Round-6
- description: Define all dataclasses in `src/agent_replay/models.py`: CostEntry, PhaseEntry, GitCommit, SessionBlock, PlanItem, MetricsEntry, TimelineEvent, Iteration. Use Decimal for cost fields, datetime with timezone for timestamps, str for cost.log item field (per clarity Round 4). Iteration.status is "OK"|"FAIL"|"STUCK" (per clarity Round 6).
- acceptance: `from agent_replay.models import CostEntry, PhaseEntry, GitCommit, SessionBlock, PlanItem, MetricsEntry, TimelineEvent, Iteration` succeeds; all fields have correct type annotations; Decimal used for monetary values.
- tests: Unit tests verify dataclass instantiation, field types, and default values. Test that Decimal fields reject float assignment patterns.

## Item 2: Test Fixtures
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-1, CLARITY_LOG.md#Round-7
- description: Create realistic sample log fixtures in `tests/fixtures/` matching the actual harness-for-real log format. Include: `cost.log` (multi-line with various phases/iterations), `phase.log` (event-based format per clarity Round 1: `timestamp event=TYPE key=value...`), `metrics.log` (4-field format per clarity Round 7), `harness-state.json`, `progress.txt` (multiple session blocks with completion lines), `IMPLEMENTATION_PLAN.md` (with DONE/TODO items). Also include a `conftest.py` with a `sample_project` fixture that builds a tmp_path project directory with all these files.
- acceptance: `tests/fixtures/` contains all sample files; `conftest.py` provides `sample_project` fixture returning a Path to a fully populated temp directory with `.harness-logs/` subdirectory.
- tests: Fixture files are validated by being used in parser tests (Items 3-9). conftest.py fixture is tested implicitly.

## Item 3: cost.log Parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-4
- description: Implement `parse_cost_log(path: Path) -> list[CostEntry]` in `src/agent_replay/parsers.py`. Parse each line matching format `timestamp phase=X iter=N model=M in=N out=N cost=$X cumulative=$X item=N`. Item field is `\d*` (optional integer string, per clarity Round 4). Malformed lines are skipped with a warning to stderr. Empty/missing file returns empty list.
- acceptance: Parses the fixture cost.log correctly; malformed lines produce warnings but no crash; empty file returns []; Decimal values match exactly.
- tests: Test valid multi-line parsing, malformed line skipping, empty file, missing file, edge cases (item="" vs item="3"), Decimal precision.

## Item 4: phase.log Parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-1, CLARITY_LOG.md#Round-6
- description: Implement `parse_phase_log(path: Path) -> list[PhaseEntry]` in `src/agent_replay/parsers.py`. Parse event-based format: `timestamp event=TYPE key=value...` (per clarity Round 1). Extract TRANSITION events to determine phase changes. Detect CIRCUIT_BREAKER events for STUCK status (per clarity Round 6). Malformed lines skipped with warning.
- acceptance: Parses fixture phase.log correctly; CIRCUIT_BREAKER events detected; malformed lines don't crash.
- tests: Test START/TRANSITION/CIRCUIT_BREAKER parsing, malformed lines, empty file, missing file.

## Item 5: progress.txt Parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-8
- description: Implement `parse_progress(path: Path) -> list[SessionBlock]` in `src/agent_replay/parsers.py`. Split on `=== Session ... ===` boundaries. Extract timestamp from header. SessionBlock.content holds full text of block. Extract `Completed: Item N - ...` lines into items_completed list.
- acceptance: Correctly splits multi-block progress.txt; extracts timestamps and completed items; handles missing file.
- tests: Test multi-block splitting, item extraction, single block, empty file, missing file.

## Item 6: metrics.log Parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-7
- description: Implement `parse_metrics_log(path: Path) -> list[MetricsEntry]` in `src/agent_replay/parsers.py`. Parse 4-field format from actual harness output. Malformed lines skipped with warning.
- acceptance: Parses fixture metrics.log correctly; malformed lines don't crash; missing file returns [].
- tests: Test valid parsing, malformed lines, empty file, missing file.

## Item 7: harness-state.json Parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-2
- description: Implement `parse_harness_state(path: Path) -> dict | None` in `src/agent_replay/parsers.py`. Load JSON with actual schema (uses `phase` not `current_phase`, per clarity Round 2). Return None if file missing or invalid JSON.
- acceptance: Loads fixture harness-state.json; returns None for missing/invalid; uses correct field names.
- tests: Test valid load, missing file, invalid JSON, unexpected fields.

## Item 8: IMPLEMENTATION_PLAN.md Parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/replay-debugger.md
- description: Implement `parse_plan(path: Path) -> list[PlanItem]` in `src/agent_replay/parsers.py`. Extract items with regex: `## Item N: title` headers and `- status:`, `- priority:` fields. Graceful handling of malformed/missing file.
- acceptance: Extracts all items from fixture IMPLEMENTATION_PLAN.md with correct number, title, status, priority.
- tests: Test multi-item extraction, partial items, empty file, missing file.

## Item 9: Git Log Parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-5
- description: Implement `parse_git_log(project_dir: Path) -> list[GitCommit]` in `src/agent_replay/parsers.py`. Run `subprocess.run(["git", "log", "--format=%H %aI %s", ...])` and parse output. Match commits to iterations by timestamp range (per clarity Round 5). Return empty list if not a git repo or git not available.
- acceptance: Parses git log output into GitCommit objects; handles non-git directory gracefully; timestamps are timezone-aware.
- tests: Test with mock subprocess output (monkeypatch subprocess.run), non-git directory, empty log.

## Item 10: Timeline Builder
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 4, Item 5, Item 6, Item 7, Item 8, Item 9]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-3, CLARITY_LOG.md#Round-6, CLARITY_LOG.md#Round-13, CLARITY_LOG.md#Round-14
- description: Implement `build_timeline(project_dir: Path) -> list[Iteration]` in `src/agent_replay/timeline.py`. Call all parsers, merge events chronologically, group by (phase, iter) from cost.log (per clarity Round 3), assign global iteration numbers chronologically. Compute per-iteration: cost_total, tokens_in, tokens_out, duration (last-first event, per clarity Round 13), status (STUCK from CIRCUIT_BREAKER, FAIL from zero commits, OK otherwise, per clarity Round 6). Handle empty session (0 iterations from cost.log, per clarity Round 14).
- acceptance: Produces correctly numbered iterations from fixture data; cost totals match; status assignment correct; empty session returns [].
- tests: Test full timeline build from fixtures, iteration grouping, status assignment (OK/FAIL/STUCK), duration calculation, empty session.

## Item 11: CLI Entrypoint and Validation
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 10]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-14, CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-16
- description: Implement `main()` in `src/agent_replay/cli.py` with argparse. Arguments: `project-dir` (positional), `--summary`, `--iteration N` (global number, per clarity Round 15), `--failures` (includes FAIL+STUCK, per clarity Round 16), `--export PATH`. Validate project directory has `.harness-logs/`; exit code 1 with "Not a harness project" if missing. Dispatch to appropriate handler based on flags.
- acceptance: `agent-replay --help` shows all options; invalid directory produces error with exit code 1; flags are mutually exclusive where appropriate.
- tests: Test argument parsing, directory validation, missing .harness-logs/ error, help output.

## Item 12: Summary Mode
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 10, Item 11]
- spec: specs/replay-debugger.md
- description: Implement `print_summary(iterations: list[Iteration], state: dict | None, plan_items: list[PlanItem]) -> None` in `src/agent_replay/summary.py`. Use rich to display: total iterations, total cost, total tokens, per-phase breakdown, items completed, current state. Format costs with `$X.XX`. Display plan progress (DONE/TODO counts).
- acceptance: `agent-replay <dir> --summary` prints formatted summary with correct totals; output uses rich formatting.
- tests: Test summary output capture (capsys), verify totals match, empty session message.

## Item 13: Iteration and Failures CLI Modes
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 10, Item 11]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-15, CLARITY_LOG.md#Round-16
- description: Implement `--iteration N` mode: display detailed view of global iteration N (error if not found, per clarity Round 15). Implement `--failures` mode: filter and display only FAIL and STUCK iterations (per clarity Round 16). Both use rich for formatting.
- acceptance: `--iteration 1` shows detail for iteration 1; `--iteration 999` errors; `--failures` shows only FAIL/STUCK iterations.
- tests: Test iteration lookup (found/not-found), failures filter (mixed statuses), empty failures list.

## Item 14: JSON Export
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 10, Item 11]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-9
- description: Implement `export_json(iterations: list[Iteration], output_path: Path) -> None` in `src/agent_replay/export.py`. Schema mirrors data model (per clarity Round 9). Serialize Decimal as strings, datetime as ISO 8601 strings. Write pretty-printed JSON.
- acceptance: `agent-replay <dir> --export report.json` creates valid JSON; Decimals are strings; timestamps are ISO 8601; file is pretty-printed.
- tests: Test JSON output structure, Decimal serialization, timestamp format, file creation.

## Item 15: TUI App Shell
- status: DONE
- priority: P1
- complexity: L
- depends_on: [Item 10, Item 11]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-10
- description: Implement the main Textual app in `src/agent_replay/tui/app.py`. Define layout with Header (project name, total iterations, total cost, total time), Left Panel (iteration list placeholder), Right Panel (detail placeholder), Footer (keybindings: q=quit, j/k=up/down, 1-4=tab switch, /=search). Flat chronological iteration list style (per clarity Round 10). Wire up to `cli.py` as default mode (no flags).
- acceptance: `agent-replay <dir>` launches TUI; header shows correct stats; footer shows keybindings; q quits; layout has left/right panels.
- tests: Use Textual pilot testing to verify app launches, header content, quit keybinding, layout structure.

## Item 16: TUI Iteration List Widget
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 15]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-10
- description: Implement the left panel iteration list in `src/agent_replay/tui/iteration_list.py`. Display each iteration as a row: number, phase label, cost, pass/fail/stuck icon. Keyboard navigation: j/k or up/down arrows to move, Enter to select. Highlight selected row. Emit selection event to update detail panel.
- acceptance: Iteration list shows all iterations with correct data; keyboard navigation works; selection changes highlighted row and triggers detail update.
- tests: Pilot tests for keyboard navigation, selection events, correct rendering of iteration rows.

## Item 17: TUI Detail Panel with Tabs
- status: DONE
- priority: P1
- complexity: L
- depends_on: [Item 15, Item 16]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-5, CLARITY_LOG.md#Round-7
- description: Implement the right panel in `src/agent_replay/tui/detail_panel.py` with 4 tabs. Tab 1 (Overview): phase, model, tokens in/out, cost, duration, metrics, items completed. Tab 2 (Progress): progress.txt session block for the iteration's time range. Tab 3 (Git Diff): git commits matched by timestamp range (per clarity Round 5), show `git show --stat` output. Tab 4 (Cost Chart): placeholder, implemented in Item 18. Switch tabs with number keys 1-4.
- acceptance: Selecting an iteration updates all tabs; tab switching with 1-4 keys works; overview shows correct data; git tab shows commit stats.
- tests: Pilot tests for tab switching, content updates on selection change, correct data display per tab.

## Item 18: TUI Cost Chart Tab
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 15]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-11
- description: Implement Tab 4 content: cumulative cost chart across all iterations. Use Textual Sparkline widget or rich-based ASCII bar chart (per clarity Round 11). X-axis: iteration numbers, Y-axis: cumulative cost. Highlight current iteration position.
- acceptance: Cost chart renders in Tab 4; shows cumulative cost progression; current iteration is highlighted.
- tests: Test chart rendering with sample data, empty data, single iteration.

## Item 19: TUI Search
- status: DONE
- priority: P2
- complexity: M
- depends_on: [Item 15, Item 16, Item 17]
- spec: specs/replay-debugger.md
- clarity_ref: CLARITY_LOG.md#Round-12
- description: Implement search with `/` key trigger. Search scope is progress.txt content only (per clarity Round 12). Show search input bar at bottom. On Enter, find first matching iteration and jump to it in the iteration list. Support repeated search (next match).
- acceptance: `/` opens search bar; typing a keyword and pressing Enter jumps to matching iteration; repeated search cycles through matches.
- tests: Pilot tests for search bar activation, keyword matching, jump-to-iteration, no-match handling.

PHASE_1_COMPLETE
