# Implementation Plan
Generated: 2026-03-24T19:00:00+09:00
Total_Items: 15
Completed: 1
Test_Items: 15 (target: ≥70% of implementation items)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3, Item 4]   # foundation — no dependencies
  - group_2: [Item 5, Item 6, Item 7, Item 8]   # parsers — depend on group_1
  - group_3: [Item 9, Item 10]                   # synthesis — depend on group_2
  - group_4: [Item 11, Item 12, Item 13]         # output — depend on group_3
  - group_5: [Item 14, Item 15]                  # CLI + integration — depend on group_4
Build_Order: group_1 → group_2 → group_3 → group_4 → group_5
```

## File Structure
```
src/agent_harvest/
├── __init__.py           # existing (empty)
├── models.py             # Item 1
├── utils.py              # Item 2
├── stack.py              # Item 3
├── category.py           # Item 4
├── learnings_parser.py   # Item 5
├── clarity_parser.py     # Item 6
├── progress_parser.py    # Item 7
├── git_analyzer.py       # Item 8
├── synthesizer.py        # Items 9, 10
├── rule_writer.py        # Item 11
├── skill_writer.py       # Item 12
├── report_writer.py      # Item 13
└── cli.py                # Item 14

tests/
├── conftest.py
├── fixtures/
│   ├── LEARNINGS.md
│   ├── CLARITY_LOG.md
│   └── progress.txt
├── test_models.py
├── test_utils.py
├── test_stack.py
├── test_category.py
├── test_learnings_parser.py
├── test_clarity_parser.py
├── test_progress_parser.py
├── test_git_analyzer.py
├── test_synthesizer.py
├── test_rule_writer.py
├── test_skill_writer.py
├── test_report_writer.py
├── test_cli.py
└── test_integration.py
```

---

## Item 1: Data models
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/knowledge-harvester.md
- description: Create all 5 dataclasses in models.py — LearningEntry, ClarityEntry, FileChurn, HarvestRule, HarvestResult — with full type hints. All fields match the spec exactly. Include a factory method on HarvestResult for empty initialization.
- acceptance: All 5 dataclasses instantiate with correct fields and types. Dataclass equality and repr work. HarvestResult.categories and .stacks default to empty dicts. FileChurn fields default to 0.
- tests: test_models.py — test instantiation of each dataclass with valid data, test default values, test that fields have correct types via isinstance checks, test dataclass equality.

## Item 2: Slugify utility
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (ID generation)
- description: Create utils.py with a slugify(text, max_length=60) function. Lowercase, replace non-alphanumeric chars with hyphens, collapse multiple hyphens, strip leading/trailing hyphens, truncate to max_length. Also create a make_unique_id(slug, existing_ids) function that appends -2, -3, etc. on collision.
- acceptance: slugify("Python DateTime Parsing!") → "python-datetime-parsing". slugify("a" * 100, 60) produces a 60-char slug. make_unique_id("foo", {"foo"}) → "foo-2". make_unique_id("foo", {"foo", "foo-2"}) → "foo-3".
- tests: test_utils.py — test basic slugification, unicode handling, max_length truncation, collapse multiple hyphens, strip edge hyphens, collision resolution with make_unique_id.

## Item 3: Stack detection
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (stack tags, stack mapping)
- description: Create stack.py with two functions. detect_project_stacks(project_dir) checks for marker files (pyproject.toml→python, pom.xml→java/spring, package.json→nodejs/nextjs/react, Cargo.toml→rust, go.mod→go). For pom.xml, check content for spring-boot. For package.json, check deps for next/react. extract_text_stacks(text) scans text for ~30-50 known library/extension names mapped to stack tags.
- acceptance: detect_project_stacks on a dir with pyproject.toml returns ["python"]. extract_text_stacks("use pytest and ruff") returns ["python"]. A dir with package.json containing "next" dep returns ["nodejs", "nextjs"].
- tests: test_stack.py — test each marker file detection with tmp_path, test spring detection from pom.xml content, test next/react from package.json, test text extraction for python/java/nodejs/rust/go libraries, test empty dir returns empty list.

## Item 4: Category classification
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (category keywords)
- description: Create category.py with classify_category(text) function. Uses keyword-based heuristic matching against 6 categories (error-recovery, library-quirk, pattern, performance, testing, compatibility). Priority order on overlap: error-recovery > library-quirk > compatibility > pattern > performance > testing. Default to "pattern" if no match.
- acceptance: classify_category("error handling with retry fallback") → "error-recovery". classify_category("import version API quirk") → "library-quirk". classify_category("no keywords here") → "pattern".
- tests: test_category.py — test each category with representative text, test priority ordering when multiple categories match, test default to "pattern", test case-insensitivity.

## Item 5: LEARNINGS.md parser
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3, Item 4]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (LEARNINGS.md format)
- description: Create learnings_parser.py with parse_learnings(file_path, project_name, project_stacks) → list[LearningEntry]. Split on `### Learning:` headers. Extract `- Context:`, `- Discovery:`, `- Rule:` sub-bullets. Generate id via slugify(title). Classify category from full text. Extract text stacks and union with project stacks. Handle missing fields gracefully (empty string). Create realistic fixture in tests/fixtures/LEARNINGS.md.
- acceptance: Parsing a LEARNINGS.md with 3 learning entries produces 3 LearningEntry objects. Missing sub-bullets produce empty strings, not errors. IDs are unique slugs. Categories are classified. source_file is "LEARNINGS.md".
- tests: test_learnings_parser.py — test parsing well-formed LEARNINGS.md (3+ entries), test missing Context/Discovery/Rule fields, test empty file, test nonexistent file returns empty list, test id slugification, test category assignment, test stack extraction.

## Item 6: CLARITY_LOG.md parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (decision field mapping)
- description: Create clarity_parser.py with parse_clarity_log(file_path) → list[ClarityEntry]. Parse code-fenced ambiguity blocks. Extract Round, Q, A, Resolution fields. Resolution maps to ClarityEntry.decision. Handle multi-line values. Create realistic fixture in tests/fixtures/CLARITY_LOG.md.
- acceptance: Parsing a CLARITY_LOG with 5 ambiguity blocks produces 5 ClarityEntry objects. Round numbers are correct ints. Multi-line Q/A/Resolution values are captured fully. Missing file returns empty list.
- tests: test_clarity_parser.py — test parsing multi-block CLARITY_LOG, test multi-line field values, test multiple rounds, test empty file, test nonexistent file.

## Item 7: progress.txt parser
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2, Item 3, Item 4]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (progress.txt parsing)
- description: Create progress_parser.py with parse_progress(file_path, project_name, project_stacks) → list[LearningEntry]. Split on `=== Session` delimiters. Extract `Discovered:` and `Why:` fields from each session block. Create LearningEntry from Discovered fields. Skip sessions without labeled fields. source_file is "progress.txt". Create fixture in tests/fixtures/progress.txt.
- acceptance: Parsing a progress.txt with 3 sessions (2 with Discovered fields) produces 2 LearningEntry objects. Sessions without Discovered are skipped. source_file is "progress.txt".
- tests: test_progress_parser.py — test parsing multi-session progress.txt, test sessions without Discovered field are skipped, test Why field used as context, test empty file, test nonexistent file.

## Item 8: Git log analyzer
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3, Item 4]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (name-status vs stat, FileChurn, fix patterns)
- description: Create git_analyzer.py with analyze_git(project_dir, project_name, project_stacks) → tuple[list[FileChurn], list[LearningEntry]]. Run `git log --name-status --format="%H"` for operation tracking (A/M/D/R counts per file). Run `git log --numstat --format="%H"` for line counts. Detect revert pattern (A→D→A). Extract `fix:` commit messages as LearningEntry with category="error-recovery". Handle non-git dirs gracefully.
- acceptance: On a git repo with known commits, FileChurn objects have correct add/modify/delete/revert counts. fix: commit messages produce LearningEntry objects. Non-git dir returns ([], []).
- tests: test_git_analyzer.py — use tmp_path with git init + scripted commits to test FileChurn counting, revert detection, fix: extraction, net_changes calculation, non-git dir handling, rename (R) counted as modify.

## Item 9: Single-project pattern synthesizer
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 5, Item 6, Item 7, Item 8]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (synthesis algorithm)
- description: Create synthesizer.py with synthesize_single(learnings, clarity_entries, file_churns, project_name) → tuple[list[HarvestRule], HarvestResult]. In single-project mode, each LearningEntry maps 1:1 to a HarvestRule with confidence="low". Build HarvestResult summary with counts and category/stack distributions. File churns feed into unstable_files list (top 20% by modify_count OR revert_count > 0 OR modify_count >= 5).
- acceptance: 5 LearningEntry objects produce 5 HarvestRule objects. HarvestResult.total_learnings = 5, total_rules = 5. Unstable files are correctly filtered. Rule IDs are unique slugs.
- tests: test_synthesizer.py — test 1:1 mapping, test HarvestResult summary computation, test unstable file filtering (top 20%, revert > 0, modify >= 5), test empty inputs produce empty results.

## Item 10: Cross-project matcher
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 9]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (Jaccard matching, confidence scoring)
- description: Add synthesize_cross(project_results) → tuple[list[HarvestRule], HarvestResult] to synthesizer.py. Takes list of per-project (rules, result) tuples. Match rules across projects: same category AND at least one shared stack AND Jaccard similarity >= 0.4 on tokenized description words (ignoring stopwords). Merge matching rules: combine source_projects, pick longest rule text, set confidence based on source count (3+ = high, 2 = medium, 1 = low).
- acceptance: Two rules from different projects with same category, shared stack, and Jaccard >= 0.4 merge into one rule with confidence="medium" and both source_projects listed. Three matching rules produce confidence="high". Non-matching rules remain separate with confidence="low".
- tests: test_synthesizer.py (append) — test cross-project merging with matching rules, test non-matching rules stay separate, test confidence escalation (1→low, 2→medium, 3+→high), test Jaccard threshold boundary (0.39 = no match, 0.4 = match), test merged rule picks longest rule text.

## Item 11: Rule writer (YAML/JSON)
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 9]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (--format json)
- description: Create rule_writer.py with write_rules(rules, output_dir, format="yaml"). Write each HarvestRule as a separate file in output_dir/rules/. YAML format uses pyyaml with allow_unicode=True. JSON format uses json.dumps with indent=2. Filename is rule.id + extension. Respects --min-confidence and --stack filters (passed as params).
- acceptance: 3 rules produce 3 YAML files in rules/ subdirectory. YAML files are valid (round-trip safe via safe_load). JSON format produces .json files. Korean text in rules is preserved (not escaped). Filters correctly exclude rules below min-confidence or outside stack.
- tests: test_rule_writer.py — test YAML output with tmp_path, test JSON output, test round-trip safety (safe_load → safe_dump), test Korean content preservation, test confidence filtering, test stack filtering.

## Item 12: Skills markdown writer
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 9]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (skills format)
- description: Create skill_writer.py with write_skills(rules, output_dir). Group rules by primary stack. Write one markdown file per stack in output_dir/skills/ (e.g., python-common.md). Format: `# [Stack] Common Rules` header, `## Source` with source project list, bulleted rule list. Only include high and medium confidence rules.
- acceptance: Rules from 2 stacks produce 2 skill files. Low-confidence rules are excluded. Markdown contains correct headers and bullet formatting. Empty stack group produces no file.
- tests: test_skill_writer.py — test grouped output by stack, test low-confidence exclusion, test markdown structure, test empty rules produce no files.

## Item 13: Report writer (instability + spec-guide + summary)
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 9]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (instability threshold, spec-guide, summary.json)
- description: Create report_writer.py with three functions. write_instability_report(file_churns, output_dir) writes instability-report.md — sorted by modify_count descending, shows all FileChurn data in a table. write_spec_guide(clarity_entries, output_dir) writes spec-guide.md — lists all resolved questions as "When writing specs, specify..." guidelines, grouped by category in cross-project mode. write_summary(result, output_dir) writes summary.json — direct HarvestResult serialization with indent=2.
- acceptance: instability-report.md contains a markdown table of unstable files sorted by modify_count. spec-guide.md lists guideline items. summary.json is valid JSON matching HarvestResult fields. All three files created in output_dir.
- tests: test_report_writer.py — test instability report markdown table format and sort order, test spec-guide guideline extraction, test summary.json validity and field presence, test empty inputs produce valid but minimal output.

## Item 14: CLI entry point
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 11, Item 12, Item 13]
- spec: specs/knowledge-harvester.md
- clarity_ref: CLARITY_LOG.md#Round-1 (--dry-run, --stack, --min-confidence, --format, project detection)
- description: Create cli.py with main() function using argparse. Supports: positional project-dir, --gallery, --output (default: harvest-output/), --stack, --min-confidence, --format (yaml|json), --dry-run. Gallery mode: discover projects as immediate subdirs with .git/ or marker files (exclude hidden dirs). Orchestrate: detect stacks → parse all sources → analyze git → synthesize → write output. --dry-run prints HarvestResult summary to stdout without writing files. Error handling per spec (missing dir → exit 1, missing sources → skip, no results → message + exit 0).
- acceptance: `agent-harvest <dir>` produces harvest-output/ with rules/, skills/, reports. `--gallery <dir>` discovers and analyzes multiple projects. `--dry-run` prints summary without writing. `--stack python` filters output. `--format json` produces JSON rules. Missing dir exits with code 1. Missing LEARNINGS.md skips gracefully.
- tests: test_cli.py — test argument parsing for all flag combinations, test single-project mode with tmp_path fixtures, test gallery mode project discovery, test --dry-run produces stdout output only, test error handling (missing dir, no results).

## Item 15: End-to-end integration test
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 14]
- spec: specs/knowledge-harvester.md
- description: Create test_integration.py with a full pipeline test. Set up a realistic project directory in tmp_path with LEARNINGS.md (3+ entries), CLARITY_LOG.md (5+ ambiguities), progress.txt (3+ sessions), and a git repo with 10+ commits including fix: messages and file additions/modifications/deletions. Run the full CLI. Verify all output files exist with correct content. Test gallery mode with 2 projects sharing common learnings to verify cross-project confidence escalation.
- acceptance: Full pipeline produces all expected output files (rules/*.yaml, skills/*.md, instability-report.md, spec-guide.md, summary.json). Cross-project test shows confidence="medium" for shared learnings. All output files are valid (YAML parses, JSON parses, markdown is well-formed).
- tests: test_integration.py — test full single-project pipeline end-to-end, test full gallery pipeline with 2+ projects, test cross-project confidence escalation, verify all output file existence and validity.

## Item 16: Gallery path namespacing + dry-run filter application
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 14]
- spec: specs/knowledge-harvester.md (§필수 동작 규칙, added in e2583fd)
- description: Two spec bugs. (1) Gallery mode instability-report.md paths lacked project-name prefix, making same-named files (e.g. main.py) ambiguous across projects. Fixed by prefixing FileChurn.path with project_name/ via dataclasses.replace() in the gallery loop. (2) --dry-run printed total_rules (unfiltered) ignoring --stack/--min-confidence filters. Fixed by computing filtered_count via _passes_filters and displaying "Would write: N rules (filtered by ...)" when filters are active.
- acceptance: gallery instability-report.md shows proj1/main.py not main.py; --dry-run --min-confidence medium shows "Would write: 0 rules (filtered by min-confidence=medium)".
- tests: 4 new tests (2 in test_cli.py, 2 in test_integration.py).

PHASE_1_COMPLETE
