# Implementation Plan
Generated: 2026-03-24T00:00:00+09:00
Total_Items: 17
Completed: 0
Test_Items: 14 (target: ≥70% of 17 = 12)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3]
  - group_2: [Item 4, Item 5, Item 6, Item 7, Item 8, Item 11, Item 12, Item 13]
  - group_3: [Item 9, Item 10, Item 14]
  - group_4: [Item 15, Item 16, Item 17]
Build_Order: group_1 → group_2 → group_3 → group_4
Intra_Group_Deps:
  - group_3: Item 10 depends on Item 9; Item 14 depends on Item 9
  - group_4: Item 16 depends on Item 10; Item 17 depends on Item 16
```

## Item 1: Project scaffolding
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/eval-runner.md
- description: Create the project skeleton — pyproject.toml with dependencies (pyyaml, jinja2, ruff, pytest, mypy as dev), src/agent_eval/ package with __init__.py, backends/ and report/ sub-packages with __init__.py files, report/templates/ directory, tests/ directory with __init__.py and empty conftest.py. Verify `uv sync`, `uv run pytest`, and `uv run ruff check .` all pass on the empty project.
- acceptance: `uv sync` succeeds; `uv run pytest` exits 0 (no tests collected is OK); `uv run ruff check .` exits 0; `from agent_eval import __version__` works in Python.
- tests: No dedicated tests — acceptance is verified by running the toolchain.

## Item 2: Data models
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q3: plan format, Q12: success definition, Q16: models vs metrics, Q21: error field)
- description: Implement models.py with all dataclasses. RunResult (21 fields: agent, benchmark, success, build_success, test_total, test_passed, test_pass_rate, total_iterations, total_time_seconds, phase_times dict[str,float], total_tokens_in, total_tokens_out, estimated_cost, items_completed, items_total, stuck_count, circuit_breaker_count, error str|None). BenchmarkConfig (name, language, complexity, expected_tests, expected_items, timeout). SuiteConfig (benchmarks list[BenchmarkRef], agents list[AgentRef], output, timeout). BenchmarkRef (path, timeout optional). AgentRef (name, model optional, extra_args optional dict). Parser intermediate types: CostLogData, PlanData, PhaseLogData, TestData. Add to_dict/from_dict on RunResult for JSON serialization.
- acceptance: All dataclasses instantiate with valid defaults; RunResult.to_dict() produces a JSON-serializable dict; RunResult.from_dict(result.to_dict()) round-trips correctly; success field computes correctly per clarity (build_success AND test_total > 0 AND test_passed == test_total).
- tests: tests/test_models.py — test dataclass creation, default values, to_dict/from_dict round-trip, edge cases (zero test_total avoids division by zero in test_pass_rate).

## Item 3: Test fixtures
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q1: cost.log format, Q2: progress.txt format, Q3: plan format, Q4: phase.log format, Q11: test output format)
- description: Create realistic fixture files in tests/fixtures/ based on actual harness output formats documented in CLARITY_LOG. Files: cost.log (5+ lines with key=value format, multiple phases), IMPLEMENTATION_PLAN.md (5 items — 3 DONE, 2 TODO), phase.log (2 CIRCUIT_BREAKER events, 1 PREDICT_FAILURE), progress.txt (2 session blocks), pytest_output.txt (pytest summary with passed/failed), maven_output.txt (surefire summary), benchmark.yaml (word-counter config), eval-config.yaml (2 benchmarks × 2 agents), .harness-config (shell variable format). Also create tests/fixtures/mock_benchmark/ directory tree with benchmark.yaml, .harness-config, specs/spec.md, IMPLEMENTATION_PLAN.md, progress.txt, .harness-logs/cost.log, .harness-logs/phase.log.
- acceptance: All fixture files exist and contain syntactically valid data matching the formats specified in CLARITY_LOG. mock_benchmark/ directory has complete structure for MockBackend testing.
- tests: No dedicated tests — fixtures are test infrastructure used by other items.

## Item 4: Cost log parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2, Item 3]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q1: cost.log format, Q2: phase_times from cost.log, Q20: phase_times dict shape)
- description: Implement parse_cost_log(path) in parser.py. Parse .harness-logs/cost.log with key=value format per line: "TIMESTAMP phase=PHASE iter=N model=MODEL in=INPUT out=OUTPUT cost=$COST cumulative=$CUMULATIVE item=ITEM". Extract and return CostLogData with: total_tokens_in (sum of in), total_tokens_out (sum of out), estimated_cost (parse final cumulative $ value), phase_times dict[str,float] (group by phase, compute elapsed from first to last timestamp per phase), total_iterations (count of lines), total_time_seconds (first timestamp to last timestamp). Handle missing file (return zeroed CostLogData), empty file, malformed lines (skip them).
- acceptance: Parses fixture cost.log and returns correct totals; handles missing file gracefully; phase_times keys match phase names in fixture; total_tokens_in/out match sum of fixture values.
- tests: tests/test_parser.py::TestCostLogParser — test with fixture cost.log, test missing file, test empty file, test malformed line skipping, test single-line file, test phase_times computation.

## Item 5: Implementation plan parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 2, Item 3]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q3: IMPLEMENTATION_PLAN.md format, Q15: items_total source)
- description: Implement parse_plan(path) in parser.py. Parse IMPLEMENTATION_PLAN.md by counting "## Item" headers for items_total and lines matching "- status: DONE" for items_completed. Return PlanData(items_completed, items_total). Handle missing file (return PlanData(0, 0)).
- acceptance: Parses fixture IMPLEMENTATION_PLAN.md and returns items_completed=3, items_total=5; handles missing file.
- tests: tests/test_parser.py::TestPlanParser — test with fixture, test missing file, test file with zero items, test all-DONE file.

## Item 6: Test output parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 2, Item 3]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q11: test output parsing strategy)
- description: Implement parse_test_output(output, framework) in parser.py. For framework="pytest": extract from summary line using regex for "N passed", "N failed", "N error". For framework="maven": extract from "Tests run: X, Failures: Y, Errors: Z, Skipped: W" line. Return TestData(test_total=passed+failed+errors, test_passed=passed, test_failed=failed+errors). Handle empty output (return TestData(0,0,0)), no summary line found.
- acceptance: Parses fixture pytest_output.txt and maven_output.txt correctly; framework detection works; handles edge cases (all passed, all failed, zero tests).
- tests: tests/test_parser.py::TestTestOutputParser — test pytest format, test maven format, test empty output, test no-summary output, test all-passed, test all-failed.

## Item 7: Phase log parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 2, Item 3]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q4: .harness-logs/ and event detection)
- description: Implement parse_phase_log(path) in parser.py. Parse .harness-logs/phase.log for lines containing "event=CIRCUIT_BREAKER" (count → circuit_breaker_count) and "event=PREDICT_FAILURE" (count → stuck_count). Return PhaseLogData. Handle missing file (return PhaseLogData(0, 0)).
- acceptance: Parses fixture phase.log and returns circuit_breaker_count=2, stuck_count=1; handles missing file.
- tests: tests/test_parser.py::TestPhaseLogParser — test with fixture, test missing file, test empty file, test file with no matching events.

## Item 8: Config loader
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 2, Item 3]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q5: eval-config.yaml schema, Q6: benchmark.yaml location)
- description: Implement config.py with three functions. load_benchmark_config(path) → BenchmarkConfig from benchmark.yaml (YAML). load_suite_config(path) → SuiteConfig from eval-config.yaml (YAML with benchmarks list, agents list, output, timeout). load_harness_config(path) → dict[str,str] parsing shell-style KEY="VALUE" lines from .harness-config. Validate required fields, raise ValueError on missing/malformed config.
- acceptance: Loads fixture benchmark.yaml into BenchmarkConfig with correct fields; loads fixture eval-config.yaml into SuiteConfig; loads fixture .harness-config into dict; raises on missing required fields.
- tests: tests/test_config.py — test load_benchmark_config, test load_suite_config, test load_harness_config, test missing file FileNotFoundError, test malformed YAML ValueError.

## Item 9: Metrics computation
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 4, Item 5, Item 6, Item 7]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q12: success definition, Q16: metrics vs models responsibility)
- description: Implement metrics.py with compute_run_result() that assembles a RunResult from parsed data (CostLogData, PlanData, PhaseLogData, TestData, build_success bool, agent name, benchmark name, optional error string). Computes derived fields: test_pass_rate = test_passed/test_total (0.0 if test_total==0), success = build_success AND test_total > 0 AND test_passed == test_total. Also implement normalize_scores(results) → dict mapping agent name to normalized 0-1 scores for 4 axes (correctness=test_pass_rate, speed=inverse of time, cost=inverse of cost, reliability=1-circuit_breaker/max). Also implement aggregate_results(results) for multi-run comparison summaries.
- acceptance: compute_run_result produces correct RunResult from fixture-derived parsed data; success logic matches clarity spec; normalize_scores returns values in [0,1]; aggregate_results groups by benchmark.
- tests: tests/test_metrics.py — test compute_run_result with normal data, test success=True case, test success=False cases (build fail, test fail, zero tests), test test_pass_rate division by zero, test normalize_scores, test aggregate_results grouping.

## Item 10: Backend ABC + MockBackend
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 9]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q14: MockBackend design — copies fixtures then parser extracts)
- description: Implement backends/base.py with AgentBackend ABC defining run(benchmark_dir, output_dir) → RunResult. Implement backends/mock.py with MockBackend(fixture_dir) that copies fixture harness output files (.harness-logs/cost.log, .harness-logs/phase.log, IMPLEMENTATION_PLAN.md, progress.txt) from fixture_dir into the output_dir working copy, then runs the full parsing pipeline (parse_cost_log, parse_plan, parse_phase_log) and metrics computation to return a RunResult. MockBackend simulates a build success and uses pre-canned test output from fixtures for test parsing.
- acceptance: MockBackend.run() returns a valid RunResult with non-zero fields parsed from fixture data; directory isolation works (output_dir contains copied files); full parse→metrics pipeline executes without error.
- tests: tests/test_backends.py — test MockBackend.run() end-to-end with fixture mock_benchmark dir, verify RunResult fields match expected fixture values, verify files exist in output dir after run.

## Item 11: JSON report generator
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 2]
- spec: specs/eval-runner.md
- description: Implement report/json_report.py with generate_json_report(results, output_path) that serializes a list of RunResult dicts to a JSON file. Include a summary section with per-benchmark aggregation. Also implement in report/__init__.py: discover_results(results_dir) that recursively finds **/result.json files and deserializes them into RunResult objects, plus a generate_report(results, output_path, format) dispatcher.
- acceptance: Generates valid JSON file; JSON round-trips back to list of RunResult; discover_results finds result.json files in nested dirs.
- tests: tests/test_report_json.py — test JSON generation, test JSON validity, test round-trip through RunResult, test discover_results with tmp dir structure.

## Item 12: Markdown report generator
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 2]
- spec: specs/eval-runner.md
- description: Implement report/markdown.py with generate_markdown_report(results, output_path). Render a comparison table (columns: agent, benchmark, success, test_pass_rate, time, cost, items_completed), a winner summary section (best agent per benchmark by test_pass_rate, then by cost), and detailed per-run metrics.
- acceptance: Generates valid Markdown with table syntax; table has correct column count; winner section identifies correct agent; handles single-agent case.
- tests: tests/test_report_markdown.py — test table generation, test winner logic, test single result, test multi-benchmark results.

## Item 13: HTML report — comparison table
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 2]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q13: inline SVG via Jinja2)
- description: Implement report/html.py with generate_html_report(results, output_path). Create a Jinja2 template at report/templates/report.html.j2 with a self-contained HTML page (inline CSS, no external dependencies). Render an agent comparison table with all RunResult metrics. Include placeholder blocks for charts (to be filled by Item 14). The template should be readable without charts.
- acceptance: Generates valid HTML file; comparison table rows match number of results; HTML is self-contained (no external CSS/JS links); template renders without errors when chart blocks are empty.
- tests: tests/test_report_html.py — test HTML generation, test table row count, test self-contained (no external links), test with empty results list.

## Item 14: HTML report — SVG charts
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 9, Item 13]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q13: inline SVG, no JS dependencies)
- description: Add SVG chart generation to report/html.py. Implement three chart helpers: _radar_chart_svg(normalized_scores) for the 4-axis radar (correctness, speed, cost, reliability) as SVG polygon, _stacked_bar_chart_svg(results) for phase_times distribution as stacked SVG rects, _heatmap_svg(results) for benchmark×agent pass/fail grid as colored SVG rects. Integrate these into the Jinja2 template by passing generated SVG strings as template variables. Use metrics.normalize_scores() for radar data.
- acceptance: HTML report includes embedded SVG elements; radar chart has polygon paths for each agent; bar chart has rect elements per phase; heatmap shows correct pass/fail colors; all SVGs render in a browser.
- tests: tests/test_report_html.py (extend) — test SVG presence in output, test radar polygon point count, test bar chart rect count matches phases, test heatmap cell count matches benchmark×agent grid.

## Item 15: ClaudeBackend
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 10]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q7: runs loop.sh via subprocess, Q8: directory isolation via copy, Q10: timeout via subprocess)
- description: Implement backends/claude.py with ClaudeBackend(model). The run() method: copies benchmark_dir to output_dir/{benchmark}/{agent}/ via shutil.copytree, sets environment variables (OPUS_MODEL/SONNET_MODEL from model param), executes "bash loop.sh" via subprocess.run() in the copied directory with timeout from benchmark config, re-runs TEST_CMD (from .harness-config) to get clean test output, then parses all output files (.harness-logs/cost.log, .harness-logs/phase.log, IMPLEMENTATION_PLAN.md) and test output through the parsing pipeline to produce RunResult. On timeout: kills process, sets error field, parses partial results. On crash: captures exit code in error field.
- acceptance: ClaudeBackend instantiates with model name; run() method handles timeout (subprocess.TimeoutExpired); run() method handles process failure (non-zero exit); test with mocked subprocess confirms correct command and env vars are passed.
- tests: tests/test_backends.py (extend) — test ClaudeBackend construction, test run() with mocked subprocess (patch subprocess.run), test timeout handling, test crash handling, verify loop.sh is called with correct working dir.

## Item 16: Runner orchestrator
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 10, Item 8]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q8: copy for isolation, Q9: output dir structure, Q19: sequential execution)
- description: Implement runner.py with three public functions. run_single(benchmark_dir, agent_backend, output_dir) → RunResult: copies benchmark to {output_dir}/{benchmark_name}/{agent_name}/, calls backend.run(), serializes RunResult to result.json in the run directory. run_compare(benchmark_dir, agents list, output_dir) → list[RunResult]: runs each agent sequentially against the same benchmark. run_suite(suite_config, backend_factory) → list[RunResult]: double loop — for each benchmark, for each agent, calls run_single sequentially. All functions handle errors per run (catch exceptions, set error in RunResult, continue to next).
- acceptance: run_single produces result.json in correct directory; run_compare returns N results for N agents; run_suite iterates all benchmark×agent combinations; directory structure matches {output}/{benchmark}/{agent}/result.json; errors in one run don't abort the suite.
- tests: tests/test_runner.py — test run_single with MockBackend (verify result.json written), test run_compare with 2 MockBackends, test run_suite with fixture eval-config, test error isolation (one failing backend doesn't stop others), test directory structure.

## Item 17: CLI entry point
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 16, Item 11, Item 12]
- spec: specs/eval-runner.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Q18: exit codes, Q22: compare delegates to runner)
- description: Implement cli.py with argparse main() and 4 subcommands. "run": --benchmark, --agent, --output args → loads benchmark config, instantiates backend, calls run_single. "compare": --benchmark, --agents (comma-sep), --output → constructs agent list, calls run_compare. "suite": --config, --output → loads suite config, calls run_suite. "report": --results, --format (html|json|markdown) → discovers results, calls generate_report. Exit codes: 0=success, 1=run failure, 2=config error. Wire up console entry point in pyproject.toml [project.scripts] agent-eval = "agent_eval.cli:main".
- acceptance: `agent-eval --help` shows 4 subcommands; each subcommand parses its args correctly; exit code 0 on successful run with MockBackend; exit code 2 on missing config; entry point is registered in pyproject.toml.
- tests: tests/test_cli.py — test argparse parsing for each subcommand, test exit codes, test integration with MockBackend for run subcommand, test report subcommand with pre-built results dir.

PHASE_1_COMPLETE
