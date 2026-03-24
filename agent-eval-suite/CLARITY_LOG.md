# Clarity Log — agent-eval-suite

## Round 1

### Orientation Summary

**Spec: specs/eval-runner.md**
- Defines a CLI benchmarking tool (`agent-eval`) that runs identical coding specs against multiple AI agents and compares results quantitatively.
- Four CLI commands: `run`, `compare`, `suite`, `report`
- Benchmark structure with `benchmark.yaml` metadata
- Agent backend abstraction (ABC Strategy pattern): ClaudeBackend + MockBackend
- RunResult dataclass with correctness/efficiency/cost/quality metrics
- Result parsing from harness output files (IMPLEMENTATION_PLAN.md, progress.txt, cost.log, test output, logs/)
- Report generation: HTML (with charts), Markdown, JSON
- Dependencies: Python 3.11+, pyyaml, jinja2, subprocess for agent invocation

**Cross-references validated:**
- Reviewed actual `loop.sh` harness code (v2) in parent project
- Reviewed real `cost.log`, `progress.txt`, `IMPLEMENTATION_PLAN.md` from word-counter example
- Reviewed `.harness-config` for this project

---

### Socratic Q&A

```
Round: 1
Spec: eval-runner.md
Category: MISSING_ERROR_HANDLING
Severity: CRITICAL
Q: What is the exact format of `cost.log` that the parser must handle? The spec says "cost.log (하네스 생성) → tokens, cost" but gives no format details.
A: From the actual harness output (examples/word-counter/.harness-logs/cost.log), the format is a space-delimited line per iteration:
   `TIMESTAMP phase=PHASE iter=N model=MODEL in=INPUT_TOKENS out=OUTPUT_TOKENS cost=$COST cumulative=$CUMULATIVE item=ITEM_NUMBER`
   Example: `2026-03-19T20:26:10+09:00 phase=socratic iter=1 model=opus in=48 out=8333 cost=$0.6257 cumulative=$0.6257 item=`
   The file lives at `.harness-logs/cost.log`, not `cost.log` in the project root.
Confidence: 0.95
Remaining_Ambiguity: Token counts are in thousands (k) or raw units — confirmed raw from harness code (grep of input_tokens from JSON).
Resolution: Parser must handle the key=value format above. Extract `in`, `out`, `cost`, `cumulative` fields. Sum `in` and `out` across all lines for total_tokens_in/out. Use final `cumulative` value (or last `cost=$X` after dollar sign) for estimated_cost. File path: `.harness-logs/cost.log`.
---
```

```
Round: 1
Spec: eval-runner.md
Category: MISSING_ERROR_HANDLING
Severity: CRITICAL
Q: What is the exact format of `progress.txt` that the parser must handle for extracting phase_times and iterations?
A: From the actual harness output (examples/word-counter/progress.txt), the format is:
   - Header: `=== Harness initialized: TIMESTAMP ===`
   - Per-session blocks: `=== Session TIMESTAMP ===` followed by `Completed: Item N - Name` and narrative text
   - Final block: `Status: ALL N ITEMS COMPLETE — PHASE_1_COMPLETE`
   - Completion marker: `HARNESS_COMPLETE` section with verification report
   However, progress.txt does NOT directly contain phase_times. Phase timing data is in cost.log (timestamps per phase/iteration) and `.harness-logs/phase.log` (event timestamps).
Confidence: 0.90
Remaining_Ambiguity: The spec claims progress.txt → phase_times, but the actual data source is cost.log timestamps grouped by phase. iterations can be derived from counting lines in cost.log or from the max `iter` value per phase.
Resolution: Compute phase_times by grouping cost.log entries by `phase` field, using timestamp differences (first entry to last entry per phase). Compute total_iterations from the count of cost.log lines. Extract per-phase iteration counts from max `iter` value per phase in cost.log. progress.txt is used for qualitative data (session summaries) but not for timing metrics.
---
```

```
Round: 1
Spec: eval-runner.md
Category: MISSING_ERROR_HANDLING
Severity: CRITICAL
Q: What is the format of IMPLEMENTATION_PLAN.md for extracting items_completed and items_total?
A: From the actual harness output (examples/word-counter/IMPLEMENTATION_PLAN.md):
   - Items are delimited by `## Item N: Name` headers
   - Each item has `- status: DONE` or `- status: TODO` or `- status: IN_PROGRESS`
   - The file header contains `Total_Items: N` and `Completed: N`
Confidence: 0.95
Remaining_Ambiguity: None significant. Both header metadata and per-item status can be used; they should agree.
Resolution: items_total = count of `## Item` headers (or parse `Total_Items:` from header). items_completed = count of items with `- status: DONE`. Prefer per-item counting over header metadata for accuracy.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The spec says `logs/ 디렉토리 → stuck_count, circuit_breaker` but the harness uses `.harness-logs/` not `logs/`. What is the correct directory and how are stuck/circuit_breaker events detected?
A: From loop.sh, the log directory is `.harness-logs/` (variable `LOG_DIR`). It contains:
   - `phase.log`: events like `event=CIRCUIT_BREAKER Stuck N iterations, phase=X, model=Y`
   - `metrics.log`: entries like `metric=error_count context=PHASE value=N`
   - Per-iteration logs: `{phase}_iter{N}_{timestamp}.log`
   stuck_count in the harness is the consecutive-no-commit counter (resets on each commit). circuit_breaker_count = number of `event=CIRCUIT_BREAKER` entries in phase.log.
Confidence: 0.90
Remaining_Ambiguity: Spec says `stuck_count` in RunResult but harness resets stuck_count on each commit. For the eval result, we want total stuck events, not the final counter value.
Resolution: Parse `.harness-logs/phase.log` for `event=CIRCUIT_BREAKER` entries → circuit_breaker_count. For stuck_count, count lines in phase.log matching `event=PREDICT_FAILURE` or track from metrics.log `metric=item_failure`. If phase.log is unavailable, default both to 0.
---
```

```
Round: 1
Spec: eval-runner.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: The eval-config.yaml schema is never defined in the spec. The `suite` command requires `--config eval-config.yaml` but what fields does it contain?
A: The suite command needs to know which benchmarks to run and which agents to compare. Reasonable schema:
   ```yaml
   benchmarks:
     - path: benchmarks/word-counter
     - path: benchmarks/employee-crud
   agents:
     - name: claude
       model: opus
     - name: claude-sonnet
       model: sonnet
   output: results/
   timeout: 3600        # global default, overridable per benchmark
   ```
Confidence: 0.75
Remaining_Ambiguity: Whether agents have additional config (e.g., custom CLI flags, environment variables). Whether benchmarks can override timeout individually in the suite config.
Resolution: Define SuiteConfig dataclass in models.py: `benchmarks: list[BenchmarkRef]` (each with `path` and optional `timeout` override), `agents: list[AgentRef]` (each with `name` and optional `model`/`extra_args`), `output: str`, `timeout: int` (global default). Keep it simple — this is the MVP schema. Additional per-agent config can be added via `extra_args: dict` field.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: The benchmark directory tree shows `benchmark.yaml` at the root of `benchmarks/` alongside the benchmark subdirectories, but its content (`name: word-counter`) is clearly per-benchmark metadata. Where does each benchmark.yaml live?
A: The tree indentation is misleading. Each benchmark directory should contain its own `benchmark.yaml`. The correct structure is:
   ```
   benchmarks/
   ├── word-counter/
   │   ├── specs/
   │   ├── pyproject.toml
   │   ├── CLAUDE.md
   │   └── benchmark.yaml     # metadata for this benchmark
   └── employee-crud/
       ├── specs/
       ├── pom.xml
       ├── CLAUDE.md
       └── benchmark.yaml     # metadata for this benchmark
   ```
Confidence: 0.90
Remaining_Ambiguity: None — the content format confirms this is per-benchmark data.
Resolution: benchmark.yaml lives INSIDE each benchmark subdirectory. BenchmarkConfig is loaded from `{benchmark_dir}/benchmark.yaml`.
---
```

```
Round: 1
Spec: eval-runner.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Does ClaudeBackend invoke `claude` CLI directly or run the full `loop.sh` harness? The spec says both "claude -p --model {model} 호출 (기존 loop.sh 활용)" which is contradictory.
A: The spec says "하네스(loop.sh)의 4페이즈 구조를 활용하여 실전 코딩 태스크 기반 평가 수행" (uses loop.sh's 4-phase structure for real coding task evaluation). The parenthetical "기존 loop.sh 활용" in the ClaudeBackend description confirms it leverages the existing loop.sh. Running `claude -p` directly would skip the harness's phase management, circuit breaker, cost tracking, etc.
Confidence: 0.85
Remaining_Ambiguity: Whether the backend invokes `bash loop.sh` directly or a wrapper. What arguments loop.sh needs (it takes an optional starting phase as $1).
Resolution: ClaudeBackend runs `bash loop.sh` (or `./loop.sh`) in the benchmark's working directory via subprocess. loop.sh already handles all phases, cost tracking, and output file generation. The backend waits for loop.sh to complete (or timeout), then parses the output files from `.harness-logs/`. Model selection can be passed via environment variables (OPUS_MODEL, SONNET_MODEL) read by loop.sh from `.harness-config`.
---
```

```
Round: 1
Spec: eval-runner.md
Category: UNSTATED_ASSUMPTION
Severity: MAJOR
Q: When running multiple agents against the same benchmark (compare/suite commands), how is working directory isolation handled? loop.sh modifies files in place.
A: Each agent run must operate on an isolated copy of the benchmark directory. Otherwise concurrent or sequential runs would clobber each other's files (IMPLEMENTATION_PLAN.md, progress.txt, source code, etc.).
Confidence: 0.95
Remaining_Ambiguity: Whether to use tempdir, output-dir-based copies, or git worktrees.
Resolution: Before each run, copy the entire benchmark directory to `{output_dir}/{benchmark_name}/{agent_name}/`. Run loop.sh inside this copy. All harness outputs (`.harness-logs/`, `progress.txt`, `IMPLEMENTATION_PLAN.md`, source code) remain in the copy for post-run parsing. This is simpler and more reliable than git worktrees since benchmarks may not be git repos.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What is the output directory structure? The spec shows `--output results/` but doesn't define what goes inside.
A: Need a predictable structure for the report command to discover and aggregate results.
Confidence: 0.80
Remaining_Ambiguity: Whether to organize as benchmark/agent or agent/benchmark.
Resolution: Structure: `{output_dir}/{benchmark_name}/{agent_name}/` containing:
  - The full benchmark working copy (with all harness outputs)
  - `result.json` — serialized RunResult for this run
  The report command scans `{output_dir}/**/result.json` to discover all runs. Benchmark-first nesting makes it easy to compare agents within a benchmark.
---
```

```
Round: 1
Spec: eval-runner.md
Category: MISSING_ERROR_HANDLING
Severity: MAJOR
Q: What happens when a run fails (timeout exceeded, agent crash, missing output files)?
A: The tool must be resilient to partial results. An agent may crash mid-build, timeout, or produce incomplete output.
Confidence: 0.85
Remaining_Ambiguity: Whether timeout is enforced by the eval runner (subprocess timeout) or delegated to loop.sh's budget mechanism.
Resolution: The eval runner enforces timeout via `subprocess.run(timeout=...)`. On timeout or crash:
  1. Kill the subprocess
  2. Parse whatever output files exist (partial results are better than nothing)
  3. Set `success=False` in RunResult
  4. Set missing numeric fields to 0, missing string fields to empty
  5. Log the failure reason in RunResult (add an optional `error: str | None` field)
  Timeout value comes from benchmark.yaml `timeout` field, overridable by suite config.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: How is test output parsed to extract test_total and test_passed? The spec mentions both `mvn test` and `pytest` but doesn't specify parsing strategy.
A: The test command varies by project type. `.harness-config` contains `TEST_CMD` which tells us the test framework. For Python projects: `uv run pytest`. For Java: `mvn test`.
Confidence: 0.85
Remaining_Ambiguity: Whether to re-run tests after loop.sh completes (for a clean count) or parse test output from loop.sh logs.
Resolution: After loop.sh completes, re-run the test command from the benchmark's `.harness-config` (or benchmark.yaml language-based default) in the working copy to get a clean test result. Parse output:
  - **pytest**: Summary line format `X passed` / `X failed` / `X error` (use regex on final summary line)
  - **maven/surefire**: `Tests run: X, Failures: Y, Errors: Z, Skipped: W` format
  test_total = passed + failed + errors. test_passed = passed count. test_pass_rate = test_passed / test_total (guard against division by zero → 0.0).
---
```

```
Round: 1
Spec: eval-runner.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: What does RunResult.success exactly mean? "빌드 + 테스트 전체 통과 여부"
A: "Build + all tests passing" = build_success AND all tests passed.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: `success = build_success and test_total > 0 and test_passed == test_total`
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: How are HTML report charts rendered? The spec mentions radar chart, stacked bar chart, and heatmap. The only dependencies are pyyaml and jinja2 — no chart library.
A: Without a Python chart library (matplotlib, plotly), charts must be rendered client-side in the HTML output or as inline SVG.
Confidence: 0.80
Remaining_Ambiguity: Whether to use a JS CDN library or generate SVG server-side with pure Python string templating.
Resolution: Use inline SVG generated via Jinja2 templates. This keeps the dependency list minimal and produces self-contained HTML files. The radar chart (4 axes: correctness, speed, cost, reliability), stacked bar chart (phase times), and heatmap (pass/fail grid) are all feasible with SVG path/rect/polygon elements computed in Python and rendered by Jinja2. No external JS or CDN required.
---
```

```
Round: 1
Spec: eval-runner.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: What does MockBackend actually do? "미리 준비된 결과를 반환" — how are mock results provided?
A: MockBackend is for testing the eval runner itself without real API calls. It should return pre-built RunResult objects from fixture data.
Confidence: 0.85
Remaining_Ambiguity: Whether fixtures are YAML, JSON, or Python objects.
Resolution: MockBackend accepts a `fixture_dir: Path` parameter. It reads `result.json` (or `result.yaml`) files from the fixture directory to construct RunResult objects. For tests, fixture data lives in `tests/fixtures/` with sample cost.log, progress.txt, IMPLEMENTATION_PLAN.md, and pre-computed result.json files. MockBackend can either (a) return pre-built RunResult directly, or (b) simulate a run by copying fixture files to the output dir and letting the parser extract results. Option (b) also tests the parser. Resolution: use option (b) — MockBackend copies fixture harness output files to the run directory, then the normal parsing pipeline extracts RunResult.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: Where does items_total come from — benchmark.yaml `expected_items` or IMPLEMENTATION_PLAN.md parsing?
A: The spec defines both `expected_items` in benchmark.yaml (reference value) and `items_total` in RunResult (actual count from the run). These serve different purposes.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: `items_total` is parsed from the actual IMPLEMENTATION_PLAN.md produced during the run (count of `## Item` headers). `expected_items` from benchmark.yaml is a reference value for comparison/scoring in reports but not stored in RunResult.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: What is the responsibility boundary between metrics.py and models.py?
A: models.py defines data classes. metrics.py computes derived values. The spec lists both modules.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: `models.py` defines: RunResult (dataclass), BenchmarkConfig (from benchmark.yaml), SuiteConfig (from eval-config.yaml), and any intermediate data classes. `metrics.py` contains functions that take parsed raw data (from parser.py) and compute derived RunResult fields: `test_pass_rate` from test_passed/test_total, `estimated_cost` from token counts × pricing, `success` from build + test results. Also contains aggregation functions for multi-run comparisons (averages, rankings).
---
```

```
Round: 1
Spec: eval-runner.md
Category: EDGE_CASE
Severity: MINOR
Q: How does the report command discover completed runs?
A: The `report` command takes `--results results/` but the discovery mechanism is unspecified.
Confidence: 0.85
Remaining_Ambiguity: None after establishing output directory structure.
Resolution: The report command recursively scans `{results_dir}/**/result.json`. Each result.json is a serialized RunResult. The directory structure `{benchmark}/{agent}/result.json` provides grouping. Results are loaded into a list, grouped by benchmark name for comparison tables.
---
```

```
Round: 1
Spec: eval-runner.md
Category: EDGE_CASE
Severity: MINOR
Q: What are the CLI exit codes?
A: Not specified in the spec.
Confidence: 0.80
Remaining_Ambiguity: None — standard convention applies.
Resolution: Exit 0 = all runs succeeded (or report generated successfully). Exit 1 = one or more runs failed (success=False). Exit 2 = configuration error (missing benchmark, invalid config, etc.). For `report` command: exit 0 if report generated, exit 1 if no results found, exit 2 if invalid arguments.
---
```

```
Round: 1
Spec: eval-runner.md
Category: EDGE_CASE
Severity: MINOR
Q: Are suite benchmarks executed concurrently or sequentially?
A: Not specified. Each run invokes a subprocess (loop.sh) which itself may take hours.
Confidence: 0.80
Remaining_Ambiguity: Whether parallel execution is safe (resource contention, API rate limits).
Resolution: Sequential execution by default. Each benchmark×agent pair runs one at a time. This avoids API rate limit issues and resource contention. A future `--parallel N` flag can be added but is out of scope for MVP. The runner orchestrates runs in a double loop: for each benchmark, for each agent, run sequentially.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: What does `phase_times: dict` contain and how is it computed?
A: The spec says "페이즈별 소요 시간" (per-phase elapsed time) but doesn't define the dict shape.
Confidence: 0.85
Remaining_Ambiguity: None after analyzing cost.log format.
Resolution: `phase_times: dict[str, float]` maps phase name to elapsed seconds. Computed from cost.log: for each unique `phase` value, take the timestamp of the first entry minus the timestamp of the last entry for that phase. Example: `{"socratic": 180.0, "plan": 270.0, "build": 1200.0, "verify": 300.0}`. If a phase has only one entry, use 0.0 or estimate from the gap to the next phase's first entry.
---
```

```
Round: 1
Spec: eval-runner.md
Category: EDGE_CASE
Severity: MINOR
Q: Is benchmark.yaml `expected_tests` used for scoring or just informational?
A: The spec defines it as a reference value with the comment "참고값" (reference value).
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: `expected_tests` is informational only. It appears in reports for comparison (e.g., "Agent produced 85 tests vs 100 expected") but does NOT affect pass/fail determination or scoring.
---
```

```
Round: 1
Spec: eval-runner.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: RunResult has no `error` field, but runs can fail in various ways (timeout, crash, parse failure). How do we capture failure context?
A: The current RunResult spec has `success: bool` but no error message field. Failure context is important for debugging and reports.
Confidence: 0.80
Remaining_Ambiguity: Whether to extend RunResult or log errors separately.
Resolution: Add an optional field `error: str | None = None` to RunResult. Set to None on success, or a brief error description on failure (e.g., "Timeout after 3600s", "Agent process crashed with exit code 1", "Build command failed"). This is a minor spec extension that improves usability without changing the core design.
---
```

```
Round: 1
Spec: eval-runner.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: The `compare` command overlaps with `suite` — is `compare` just syntactic sugar for a single-benchmark suite?
A: `compare` takes `--benchmark` (singular) and `--agents` (comma-separated). `suite` takes `--config` (YAML with multiple benchmarks and agents). They differ in input method but produce the same output structure.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: `compare` is a convenience shortcut. Internally, it constructs a SuiteConfig with one benchmark and the specified agents, then delegates to the same runner logic used by `suite`. The output format is identical.
---
```

---

### Cross-Spec Consistency Check

Only one spec file exists (`eval-runner.md`), so cross-spec contradiction analysis is limited to internal consistency:

1. **logs/ vs .harness-logs/**: Spec says `logs/ 디렉토리` but the actual harness uses `.harness-logs/`. **Resolution**: Use `.harness-logs/` — matches the real harness. *(Resolved in Round 1, Q4)*

2. **progress.txt as source of phase_times**: Spec says `progress.txt → phase_times, iterations` but progress.txt contains session narratives, not structured timing data. cost.log is the actual source. **Resolution**: Use cost.log for timing data. *(Resolved in Round 1, Q2)*

3. **benchmark.yaml tree placement**: Shown at benchmarks/ root but content is per-benchmark. **Resolution**: Per-benchmark directory. *(Resolved in Round 1, Q6)*

4. **ClaudeBackend: "claude -p" vs "loop.sh 활용"**: Spec simultaneously says to call `claude -p --model {model}` and to leverage loop.sh. **Resolution**: Run loop.sh, which internally calls claude. *(Resolved in Round 1, Q7)*

5. **RunResult has no error field**: Runs can fail, but there's no field to capture why. **Resolution**: Add optional `error: str | None` field. *(Resolved in Round 1, Q21)*

**No unresolvable contradictions found.** All inconsistencies are spec imprecisions resolvable with evidence from the harness implementation.

---

### Ambiguity Score

```
AMBIGUITY_SCORE: 0.00
Rounds_Completed: 1
Ambiguities_Found: 22
Ambiguities_Resolved: 22
Ambiguities_Remaining: 0
```

All 22 ambiguities were resolved with confidence >= 0.75, backed by evidence from the actual harness code and real output files.

### Convergence Data

```
CONVERGENCE_DATA:
  round: 1
  score: 0.00
  prev_score: 1.0
  delta: -1.00
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 0
  stagnation_count: 0
```

---

## Resolution Summary

| # | Category | Severity | Resolution |
|---|----------|----------|------------|
| 1 | MISSING_ERROR_HANDLING | CRITICAL | cost.log: key=value format at `.harness-logs/cost.log`, parse `in`/`out`/`cost`/`cumulative` fields |
| 2 | MISSING_ERROR_HANDLING | CRITICAL | phase_times from cost.log timestamps grouped by phase, NOT from progress.txt |
| 3 | MISSING_ERROR_HANDLING | CRITICAL | IMPLEMENTATION_PLAN.md: count `## Item` headers for total, `status: DONE` for completed |
| 4 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MAJOR | Use `.harness-logs/` not `logs/`. Parse phase.log for circuit_breaker events |
| 5 | INTEGRATION_GAP | MAJOR | eval-config.yaml: benchmarks list + agents list + output + timeout |
| 6 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MAJOR | benchmark.yaml lives inside each benchmark subdirectory |
| 7 | INTEGRATION_GAP | MAJOR | ClaudeBackend runs `bash loop.sh` via subprocess, not `claude` directly |
| 8 | UNSTATED_ASSUMPTION | MAJOR | Copy benchmark dir to `{output}/{benchmark}/{agent}/` for isolation |
| 9 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MAJOR | Output structure: `{output}/{benchmark}/{agent}/result.json` |
| 10 | MISSING_ERROR_HANDLING | MAJOR | Timeout via subprocess, partial results on failure, success=False |
| 11 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MAJOR | Re-run TEST_CMD after loop.sh; parse pytest/maven summary lines |
| 12 | UNDEFINED_TERM | MINOR | success = build_success AND test_total > 0 AND test_passed == test_total |
| 13 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MINOR | Inline SVG via Jinja2 for charts (no extra dependencies) |
| 14 | UNSTATED_ASSUMPTION | MINOR | MockBackend copies fixture harness outputs, then parser extracts RunResult |
| 15 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MINOR | items_total from IMPLEMENTATION_PLAN.md, expected_items is reference only |
| 16 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MINOR | models.py = data classes, metrics.py = computation + aggregation |
| 17 | EDGE_CASE | MINOR | Report scans `{results}/**/result.json` recursively |
| 18 | EDGE_CASE | MINOR | Exit codes: 0=success, 1=run failure, 2=config error |
| 19 | EDGE_CASE | MINOR | Sequential execution by default, parallel is future enhancement |
| 20 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MINOR | phase_times: dict[str, float] from cost.log timestamp grouping |
| 21 | UNSTATED_ASSUMPTION | MINOR | Add `error: str \| None = None` to RunResult for failure context |
| 22 | AMBIGUOUS_ACCEPTANCE_CRITERIA | MINOR | `compare` delegates to same runner logic as `suite` with one benchmark |

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.00
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
