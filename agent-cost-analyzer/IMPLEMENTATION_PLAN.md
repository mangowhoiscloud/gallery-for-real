# Implementation Plan
Generated: 2026-03-24T15:30:00+09:00
Total_Items: 14
Completed: 0
Test_Items: 14 (target: ≥70% of implementation items)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2]           # foundation — no dependencies
  - group_2: [Item 3, Item 4, Item 5, Item 6]  # parsers — depends on group_1
  - group_3: [Item 7, Item 8, Item 9]   # analyzers — depends on group_2
  - group_4: [Item 10, Item 11, Item 12, Item 13]  # comparison + reports — depends on group_3
  - group_5: [Item 14]                  # CLI — depends on group_4
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5
```

---

## Item 1: Project scaffolding and data models
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/cost-analyzer.md
- clarity_ref: CLARITY_LOG.md#Ambiguity-3, CLARITY_LOG.md#Ambiguity-16, CLARITY_LOG.md#Ambiguity-29
- description: Create the package directory structure (`src/agent_cost_analyzer/` with `parser/`, `analyzer/`, `report/`, `report/templates/` subdirectories and all `__init__.py` files). Define all dataclass models in `models.py`: `CostEntry` (timestamp, phase, iteration, model, input_tokens, output_tokens, cost as Decimal, cumulative as Decimal, item as Optional[int]), `PhaseEvent` (timestamp, event, metadata dict), `MetricEntry` (timestamp, metric, context, value, detail), `ProgressData` (project_type, init_time, sessions, completed_items, is_complete), `SessionError` (file, line_num, error_type, message, is_recovery), `CostBreakdown`, `TokenAnalysis`, `FailurePatterns`, `ComparisonResult`, and `AnalysisResult` (top-level container). Remove `pyyaml` from `pyproject.toml` dependencies per Clarity #29.
- acceptance:
  - `uv run python -c "from agent_cost_analyzer.models import CostEntry, PhaseEvent, MetricEntry, ProgressData, SessionError, AnalysisResult"` succeeds
  - `CostEntry.cost` and `CostEntry.cumulative` are `Decimal` type
  - `CostEntry.item` is `Optional[int]`
  - `pyyaml` is NOT in pyproject.toml dependencies
  - All `__init__.py` files exist for every subpackage
  - `uv run ruff check .` passes
- tests: Unit tests for dataclass construction, Decimal field handling, Optional[int] item field (None for non-build, int for build phases), and field validation

## Item 2: Test fixtures and conftest
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/cost-analyzer.md
- clarity_ref: CLARITY_LOG.md#Ambiguity-1 through CLARITY_LOG.md#Ambiguity-4
- description: Create `tests/conftest.py` with pytest fixtures that provide paths to sample log files. Create `tests/fixtures/` with realistic sample data based on word-counter reference data: `cost.log` (11 lines covering all phases, multiple items, stuck pattern on item 5), `cost_malformed.log` (mix of valid lines, blank lines, truncated lines, missing fields), `phase.log` (START, TRANSITION, PARALLEL_START, PARALLEL_DONE, CIRCUIT_BREAKER, COMPLETE events), `metrics.log` (error_count entries per build iteration), `progress.txt` (full lifecycle with init, sessions, completions, HARNESS_COMPLETE), and `session_build.jsonl` (sample JSONL with tool results including errors). All fixtures use `.harness-logs/` directory convention. Item field uses plain integers (not `Item_` prefix). Cumulative values in cost.log intentionally include a session-reset to test recalculation.
- acceptance:
  - `tests/fixtures/cost.log` has ≥10 lines covering phases socratic, plan, build, verify
  - `tests/fixtures/cost_malformed.log` has ≥5 lines including at least 2 malformed entries
  - `tests/fixtures/phase.log` includes CIRCUIT_BREAKER event
  - `tests/fixtures/metrics.log` has ≥5 entries
  - `tests/fixtures/progress.txt` includes HARNESS_COMPLETE marker
  - `tests/fixtures/session_build.jsonl` has ≥3 JSONL entries including one with error
  - `tests/conftest.py` provides `fixtures_dir`, `cost_log_path`, `phase_log_path`, `metrics_log_path`, `progress_path`, `session_log_path`, `malformed_cost_log_path` fixtures
  - `uv run pytest tests/conftest.py --collect-only` succeeds (fixtures are valid)
- tests: No separate test file needed — this item IS the test infrastructure

## Item 3: Cost log parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/cost-analyzer.md (section: Log Parser)
- clarity_ref: CLARITY_LOG.md#Ambiguity-2, CLARITY_LOG.md#Ambiguity-3, CLARITY_LOG.md#Ambiguity-4, CLARITY_LOG.md#Ambiguity-12, CLARITY_LOG.md#Ambiguity-13, CLARITY_LOG.md#Ambiguity-18, CLARITY_LOG.md#Ambiguity-28
- description: Implement `src/agent_cost_analyzer/parser/cost_log.py` with a `parse_cost_log(path: Path) -> list[CostEntry]` function. Parse each line matching the format `{timestamp} phase={phase} iter={iter} model={model} in={in} out={out} cost=${cost} cumulative=${cumul} item={item}`. Use regex for robust extraction. Handle: empty `item=` as `None`, plain integer item values, `$` prefix on cost/cumulative, timezone-aware timestamp parsing. Malformed lines are skipped with a warning via `logging.warning()`. If the file does not exist, raise `FileNotFoundError` with a clear message (cost.log is required per Clarity #13). Support optional date filtering: `after` (inclusive) and `before` (exclusive) parameters as `datetime.date`, comparing in UTC per Clarity #12.
- acceptance:
  - Parses word-counter-style cost.log (11 lines) → 11 `CostEntry` objects
  - `item` is `None` for socratic/plan/verify lines, `int` for build lines
  - `cost` and `cumulative` fields are `Decimal` instances
  - `in`/`out` fields are `int` (raw token counts)
  - Timestamp includes timezone info
  - Malformed lines are skipped (not raised), warning is logged
  - `FileNotFoundError` raised for missing file
  - Date filtering: `after=date(2026,3,19)` includes entries on that date, `before=date(2026,3,20)` excludes entries on that date
  - `uv run pytest tests/test_cost_log_parser.py` passes
  - `uv run ruff check .` passes
- tests: test_cost_log_parser.py — parse valid fixture, verify field types (Decimal, Optional[int], datetime), parse malformed fixture (count skipped lines), missing file error, date filter inclusivity/exclusivity, empty file returns empty list, line with empty item field → None

## Item 4: Phase log and metrics log parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/cost-analyzer.md (section: Failure Pattern Detection)
- clarity_ref: CLARITY_LOG.md#Ambiguity-6, CLARITY_LOG.md#Ambiguity-7, CLARITY_LOG.md#Ambiguity-8, CLARITY_LOG.md#Ambiguity-9
- description: Implement `src/agent_cost_analyzer/parser/phase_log.py` with `parse_phase_log(path: Path) -> list[PhaseEvent]` and `parse_metrics_log(path: Path) -> list[MetricEntry]`. Phase log format: `{timestamp} event={EVENT} [key=value ...]` where EVENT is one of START, TRANSITION, PARALLEL_START, PARALLEL_DONE, CIRCUIT_BREAKER, COMPLETE, ABORT. Extra key=value pairs after the event go into a metadata dict. The CIRCUIT_BREAKER line has free-text after the event name (e.g., `Stuck 3 iterations, phase=build, model=sonnet`) — store the full text as `metadata["message"]` and also parse embedded key=value pairs. Metrics log format: `{timestamp} metric={metric} context={context} value={value} detail={detail}`. Both files are optional — return empty list if file doesn't exist (no error).
- acceptance:
  - Parses phase.log fixture → list of `PhaseEvent` with correct event types
  - CIRCUIT_BREAKER event has `metadata["message"]` containing the full description text
  - START event has `metadata["phase"]` and `metadata["version"]`
  - COMPLETE event has `metadata["total_iter"]` and `metadata["cost"]`
  - Parses metrics.log fixture → list of `MetricEntry` with `metric`, `context`, `value` (int), `detail` (int)
  - Missing file → empty list (no exception)
  - `uv run pytest tests/test_phase_log_parser.py` passes
  - `uv run ruff check .` passes
- tests: test_phase_log_parser.py — parse valid phase.log fixture (verify all event types), parse metrics.log fixture (verify field types), missing file returns empty list, malformed line skipped with warning, CIRCUIT_BREAKER metadata extraction

## Item 5: Progress text parser
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/cost-analyzer.md (section: Log Parser)
- clarity_ref: CLARITY_LOG.md#Ambiguity-15, CLARITY_LOG.md#Ambiguity-25
- description: Implement `src/agent_cost_analyzer/parser/progress.py` with `parse_progress(path: Path) -> ProgressData`. Extract structured data from progress.txt using regex: (1) `=== Harness initialized: (TIMESTAMP) ===` → init time, (2) `Project type: (.+)` → project type string, (3) `=== Session (TIMESTAMP) ===` → session markers, (4) `Completed: Item (\d+) - (.+)` → completed item events, (5) `HARNESS_COMPLETE` → completion flag. Unmatched lines are silently ignored. File is optional — return a default `ProgressData` with empty fields if file doesn't exist. Normalize project type for display: `python-uv` → "Python", `java-maven`/`java-gradle` → "Java", `typescript-npm`/`node-npm` → "TypeScript", unknown → pass-through.
- acceptance:
  - Parses progress.txt fixture → `ProgressData` with correct init time, project type, completed items list, is_complete flag
  - Project type normalization: `python-uv` → "Python"
  - Missing file → default ProgressData (no error)
  - HARNESS_COMPLETE present → `is_complete = True`
  - `uv run pytest tests/test_progress_parser.py` passes
  - `uv run ruff check .` passes
- tests: test_progress_parser.py — parse valid fixture, verify all extracted fields, missing file default, project type normalization mapping, file without HARNESS_COMPLETE → is_complete=False

## Item 6: Session log parser (JSONL)
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/cost-analyzer.md (section: Log Parser — logs/*.log)
- clarity_ref: CLARITY_LOG.md#Ambiguity-5, CLARITY_LOG.md#Ambiguity-19, CLARITY_LOG.md#Ambiguity-20
- description: Implement `src/agent_cost_analyzer/parser/build_log.py` with `parse_session_logs(logs_dir: Path) -> list[SessionError]`. Scan `logs_dir` for `*.log` files (excluding `cost.log`, `phase.log`, `metrics.log`). Parse each file as JSONL. Extract errors from: (a) entries with `type=user` containing tool results where `is_error=true`, (b) entries with stderr content from Bash tool results. For each error, create `SessionError` with the source filename, line number, error type classification, and message snippet. Handle `recovery_*.log` files by tagging errors with `is_recovery=True`. Parse filename with regex `(phase)_iter(\d+)_(timestamp).log` to extract phase/iteration metadata. Invalid JSON lines are skipped with warning. Missing directory → empty list.
- acceptance:
  - Parses session_build.jsonl fixture → extracts errors with correct fields
  - `recovery_*.log` files produce errors with `is_recovery=True`
  - Non-log files (cost.log, phase.log, metrics.log) are excluded from parsing
  - Invalid JSON lines are skipped (not raised)
  - Missing directory → empty list
  - `uv run pytest tests/test_build_log_parser.py` passes
  - `uv run ruff check .` passes
- tests: test_build_log_parser.py — parse fixture JSONL, verify error extraction, recovery file tagging, filename regex parsing, invalid JSON handling, excluded files list, missing directory

## Item 7: Cost breakdown analyzer
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3]
- spec: specs/cost-analyzer.md (section: Cost Breakdown)
- clarity_ref: CLARITY_LOG.md#Ambiguity-4, CLARITY_LOG.md#Ambiguity-18, CLARITY_LOG.md#Ambiguity-24
- description: Implement `src/agent_cost_analyzer/analyzer/cost.py` with `analyze_costs(entries: list[CostEntry]) -> CostBreakdown`. Compute: (1) **by_phase** — total cost per phase (socratic, plan, build, verify), (2) **by_model** — total cost per model name (accept any string, don't hardcode), (3) **by_item** — total cost per item number (build-phase entries only, where item is not None; skip non-sequential items per Clarity #24), (4) **timeline** — list of (timestamp, cumulative_cost) pairs where cumulative is recalculated by summing individual costs chronologically (IGNORE the cumulative field from log per Clarity #4), (5) **total_cost** — sum of all individual costs, (6) **total_iterations** — count of entries. All monetary values as `Decimal`. The `CostBreakdown` dataclass holds all these breakdowns.
- acceptance:
  - Using word-counter fixture: total_cost ≈ $3.0590 (sum of 11 individual costs)
  - by_phase: socratic=$0.6257, plan=$0.5914, build=sum of build entries, verify=$0.5186
  - by_model: opus=sum of opus entries, sonnet=sum of sonnet entries
  - by_item: {1: $0.1897, 2: $0.0769, 3: $0.3099, 4: $0.1550, 5: sum of item-5 entries}
  - timeline: 11 entries, final cumulative equals total_cost, monotonically increasing
  - Recalculated cumulative differs from log cumulative (due to session resets)
  - All returned values are `Decimal`
  - `uv run pytest tests/test_cost_analyzer.py` passes
  - `uv run ruff check .` passes
- tests: test_cost_analyzer.py — verify by_phase totals, by_model totals, by_item grouping (skipped item numbers OK), timeline recalculation, empty input returns zero breakdown, single entry edge case, Decimal type assertions

## Item 8: Token analyzer
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3]
- spec: specs/cost-analyzer.md (section: Token Analysis)
- clarity_ref: CLARITY_LOG.md#Ambiguity-8, CLARITY_LOG.md#Ambiguity-27, CLARITY_LOG.md#Ambiguity-28
- description: Implement `src/agent_cost_analyzer/analyzer/tokens.py` with `analyze_tokens(entries: list[CostEntry]) -> TokenAnalysis`. Compute: (1) **total_input/total_output** — sum of all in/out token counts, (2) **io_ratio** — total_output / total_input (float), (3) **by_phase** — per-phase token totals (input, output, count), (4) **by_model** — per-model token totals, (5) **escalations** — list of model escalation events detected when consecutive entries for the same item show model changing from a cheaper model to a more expensive one (e.g., sonnet → opus), (6) **anomalies** — per-phase anomaly detection using 3σ threshold: for each phase, compute mean and stddev of total tokens (in+out) per entry; flag entries where total > mean + 3*stddev. Report anomaly with phase, iteration, actual tokens, threshold. Requires ≥3 entries in a phase to compute meaningful stddev.
- acceptance:
  - Using word-counter fixture: total_input = sum of all `in` fields, total_output = sum of all `out` fields
  - io_ratio is a float > 0
  - by_phase has entries for socratic, plan, build, verify
  - escalations list is empty for word-counter data (no model switch on same item)
  - anomalies: build phase entry with item=5 iter=5 (35897 output tokens) may flag as anomaly depending on stddev
  - Empty input → zero totals, empty lists
  - `uv run pytest tests/test_token_analyzer.py` passes
  - `uv run ruff check .` passes
- tests: test_token_analyzer.py — verify totals, io_ratio, by_phase breakdown, by_model breakdown, escalation detection (craft test data with model switch), anomaly detection (craft data with one outlier), empty input, single-entry (no anomaly possible)

## Item 9: Failure pattern detector
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 4]
- spec: specs/cost-analyzer.md (section: Failure Pattern Detection)
- clarity_ref: CLARITY_LOG.md#Ambiguity-7, CLARITY_LOG.md#Ambiguity-8, CLARITY_LOG.md#Ambiguity-9, CLARITY_LOG.md#Ambiguity-19
- description: Implement `src/agent_cost_analyzer/analyzer/failures.py` with `detect_failures(cost_entries: list[CostEntry], phase_events: list[PhaseEvent], session_errors: list[SessionError] | None = None) -> FailurePatterns`. Detect: (1) **stuck_events** — Primary: extract CIRCUIT_BREAKER events from phase_events. Fallback (when phase_events is empty): detect 3+ consecutive cost_entries with the same item value. Each stuck event records item, start iteration, count of stuck iterations. (2) **circuit_breakers** — count and details from phase_events with event=CIRCUIT_BREAKER. (3) **build_failure_rate** — heuristic per Clarity #9: an iteration "fails" if the next iteration has the same item number. Calculate as failed_iterations / total_build_iterations. (4) **error_categories** — if session_errors provided, group by error_type and count. (5) **recovery_times** — for each stuck event, count iterations from first stuck to resolution (item changes or completes). Session errors are optional (None → skip error categorization).
- acceptance:
  - Using word-counter fixture: detects stuck on item 5 (iterations 5,6,7 = 3 consecutive)
  - CIRCUIT_BREAKER event extracted from phase.log
  - build_failure_rate: 3 failed iterations (iters 5,6,7 retry item 5) out of 8 build iterations
  - recovery_time for item 5: 4 iterations (iter 5 through iter 8)
  - Empty inputs → empty FailurePatterns
  - Works with phase_events=[] (fallback stuck detection from cost_entries)
  - `uv run pytest tests/test_failure_detector.py` passes
  - `uv run ruff check .` passes
- tests: test_failure_detector.py — stuck detection via phase_events, stuck detection fallback via cost_entries, build failure rate calculation, no failures case, recovery time calculation, session errors grouping, empty inputs

## Item 10: Comparison analyzer
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 7, Item 8, Item 9]
- spec: specs/cost-analyzer.md (section: Comparison Analysis)
- clarity_ref: CLARITY_LOG.md#Ambiguity-25, CLARITY_LOG.md#Ambiguity-30
- description: Implement `src/agent_cost_analyzer/analyzer/comparison.py` with `compare_projects(results: list[tuple[str, AnalysisResult]]) -> ComparisonResult`. Takes a list of (project_name, analysis_result) pairs. Requires ≥2 projects (raise ValueError if fewer). Compute: (1) **summary_table** — per-project row with total_cost, total_iterations, duration_minutes, model_split (% opus vs sonnet), stuck_count. (2) **efficiency_ranking** — projects ranked by cost-per-iteration. (3) **stack_comparison** — group by project_type from ProgressData (Python, Java, TypeScript, etc.) and show averages. (4) **cost_comparison** — side-by-side cost breakdowns. All monetary values as Decimal.
- acceptance:
  - 2 projects → valid ComparisonResult with 2 rows in summary_table
  - 1 project → raises ValueError
  - efficiency_ranking sorted by cost_per_iteration ascending
  - stack_comparison groups projects by normalized type
  - `uv run pytest tests/test_comparison_analyzer.py` passes
  - `uv run ruff check .` passes
- tests: test_comparison_analyzer.py — compare 2 mock projects, verify summary table fields, efficiency ranking order, stack grouping, <2 projects error, projects with same stack grouped together

## Item 11: JSON report generator
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 7, Item 8, Item 9]
- spec: specs/cost-analyzer.md (section: JSON Report)
- clarity_ref: CLARITY_LOG.md#Ambiguity-16, CLARITY_LOG.md#Ambiguity-21
- description: Implement `src/agent_cost_analyzer/report/json_report.py` with `generate_json_report(result: AnalysisResult, output_dir: Path) -> Path`. Write `report.json` to output_dir. Use a custom `json.JSONEncoder` subclass that converts `Decimal` → `float` and `datetime` → ISO string. The JSON structure mirrors the AnalysisResult dataclass hierarchy per Clarity #21: `project`, `summary`, `cost_breakdown`, `token_analysis`, `failure_patterns`, `timeline`. Create output_dir if it doesn't exist. Also provide `generate_comparison_json(result: ComparisonResult, output_dir: Path) -> Path` writing `comparison.json`.
- acceptance:
  - Generates valid JSON file at `output_dir/report.json`
  - All Decimal values serialized as float (not string)
  - All datetime values serialized as ISO strings
  - JSON is loadable with `json.loads()` and has top-level keys: project, summary, cost_breakdown, token_analysis, failure_patterns, timeline
  - Output directory created if missing
  - `uv run pytest tests/test_json_report.py` passes
  - `uv run ruff check .` passes
- tests: test_json_report.py — generate report from mock AnalysisResult, verify JSON structure, Decimal→float conversion, datetime serialization, output dir creation, comparison JSON generation

## Item 12: Markdown report generator
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 7, Item 8, Item 9]
- spec: specs/cost-analyzer.md (section: Markdown Report)
- clarity_ref: CLARITY_LOG.md#Ambiguity-22
- description: Implement `src/agent_cost_analyzer/report/markdown.py` with `generate_markdown_report(result: AnalysisResult, output_dir: Path) -> Path`. Write `report.md` to output_dir. Sections per Clarity #22: (1) Project Summary (total cost, duration, model split), (2) Cost by Phase table, (3) Cost by Item table (top 10 items by cost), (4) Failure Patterns (stuck events, circuit breakers), (5) Key Metrics (input/output ratio, escalation count, anomaly count). Keep total output under 5000 characters for PR comment friendliness. Use GitHub-flavored Markdown tables. Also provide `generate_comparison_markdown(result: ComparisonResult, output_dir: Path) -> Path`.
- acceptance:
  - Generates `output_dir/report.md` with all 5 sections
  - Contains at least one GFM table (pipes + alignment)
  - Total file size < 5000 characters for typical single-project analysis
  - Monetary values formatted as `$X.XXXX`
  - `uv run pytest tests/test_markdown_report.py` passes
  - `uv run ruff check .` passes
- tests: test_markdown_report.py — generate report from mock data, verify section headers present, verify table format, verify character limit for typical data, verify monetary formatting, comparison markdown generation

## Item 13: HTML dashboard generator
- status: DONE
- priority: P0
- complexity: L
- depends_on: [Item 7, Item 8, Item 9]
- spec: specs/cost-analyzer.md (section: HTML Dashboard)
- clarity_ref: CLARITY_LOG.md#Ambiguity-17
- description: Implement `src/agent_cost_analyzer/report/html.py` with `generate_html_report(result: AnalysisResult, output_dir: Path) -> Path`. Write `report.html` to output_dir. Create Jinja2 template at `src/agent_cost_analyzer/report/templates/dashboard.html`. The HTML file must be self-contained: all CSS inline in `<style>`, all custom JS inline in `<script>`, only external reference is Chart.js CDN (`https://cdn.jsdelivr.net/npm/chart.js`). Dashboard includes: (1) summary cards (total cost, avg iteration cost, model distribution, total iterations), (2) cumulative cost line chart, (3) cost by phase pie chart, (4) cost by item bar chart, (5) failure pattern timeline (stuck events highlighted), (6) token usage chart. Pass analysis data as JSON embedded in a `<script>` tag for Chart.js consumption. Use the custom JSON encoder from Item 11 for Decimal handling. Also provide `generate_comparison_html(result: ComparisonResult, output_dir: Path) -> Path`.
- acceptance:
  - Generates valid HTML file at `output_dir/report.html`
  - Contains exactly one external `<script src=` pointing to Chart.js CDN
  - Contains `<style>` tag with CSS (no external CSS files)
  - Contains summary cards with total cost and iteration count
  - Contains Chart.js chart initialization for cumulative line chart, phase pie chart, item bar chart
  - Data is embedded as JSON in a `<script>` tag
  - File opens in a browser without errors (no broken references)
  - `uv run pytest tests/test_html_report.py` passes
  - `uv run ruff check .` passes
- tests: test_html_report.py — generate report from mock data, verify HTML structure (parse with basic string checks), verify single CDN reference, verify no external CSS/JS file references, verify data JSON embedded, verify chart canvas elements present, comparison HTML generation

## Item 14: CLI entry point
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 3, Item 4, Item 5, Item 6, Item 7, Item 8, Item 9, Item 10, Item 11, Item 12, Item 13]
- spec: specs/cost-analyzer.md (section: CLI Interface)
- clarity_ref: CLARITY_LOG.md#Ambiguity-11, CLARITY_LOG.md#Ambiguity-12, CLARITY_LOG.md#Ambiguity-14, CLARITY_LOG.md#Ambiguity-23
- description: Implement `src/agent_cost_analyzer/cli.py` with `main()` as the entry point (wired to `cost-analyze` in pyproject.toml). Use argparse with optional subcommands per Clarity #14: (1) default `analyze` — `--project PATH` (required), `--output DIR` (default: `./report`), `--after DATE`, `--before DATE`, `--format html,json,md` (default: all three). (2) `compare` — `--projects PATH,PATH,...` (comma-separated, ≥2), `--output DIR`, `--after DATE`, `--before DATE`, `--format`. (3) `watch` — stub that prints "watch mode is not yet implemented" and exits cleanly per Clarity #11. The analyze flow: locate `.harness-logs/` in project dir, parse all available logs, run all analyzers, generate requested report formats. The compare flow: run analyze on each project, then run comparison analyzer, generate comparison reports. Date format: `YYYY-MM-DD` per Clarity #12. Create output directory if it doesn't exist per Clarity #23. Exit code 0 on success, 1 on error (missing cost.log, invalid args).
- acceptance:
  - `cost-analyze --project ./path --output ./out` runs without error when cost.log exists
  - `cost-analyze compare --projects ./p1,./p2 --output ./out` works with 2+ valid projects
  - `cost-analyze watch --project ./path` prints "not yet implemented" and exits 0
  - `--after 2026-03-19 --before 2026-03-21` filters entries correctly
  - `--format json` generates only JSON report
  - Missing cost.log → exit code 1 with error message
  - Invalid date format → argparse error
  - Output directory created if missing
  - `uv run pytest tests/test_cli.py` passes
  - `uv run ruff check .` passes
- tests: test_cli.py — test argparse with various argument combinations, test default analyze flow with fixture project, test compare with 2 fixture projects, test watch stub, test date filter passing, test missing project error, test output dir creation, test format filter

---

## Summary

| Group | Items | Complexity | Parallel? |
|-------|-------|-----------|-----------|
| 1 (Foundation) | 1, 2 | S, S | Yes |
| 2 (Parsers) | 3, 4, 5, 6 | M, M, S, M | Yes |
| 3 (Analyzers) | 7, 8, 9 | M, M, M | Yes |
| 4 (Reports+Compare) | 10, 11, 12, 13 | M, S, S, L | Yes |
| 5 (CLI) | 14 | M | Solo |

Priority distribution: P0 = 9 items (1,2,3,4,7,8,9,13,14), P1 = 5 items (5,6,10,11,12)
Complexity distribution: S = 5, M = 8, L = 1, XL = 0

PHASE_1_COMPLETE
