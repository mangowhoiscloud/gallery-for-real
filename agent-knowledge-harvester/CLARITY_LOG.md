# CLARITY_LOG

## Round 1

### Specs Analyzed
- `specs/knowledge-harvester.md` — Full feature spec (CLI tool for extracting reusable patterns from harness sessions)
- `CLAUDE.md` — Stack-specific rules (Python 3.11+, uv, regex-based extraction)
- Real harness output samples from `examples/prompt-version-control/`, `examples/agent-cost-analyzer/`, `examples/personal-blog/`

### Ambiguities

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: What is the exact format of LEARNINGS.md that the parser must handle? The spec shows the LearningEntry dataclass but not the input format.
A: Real harness outputs show a consistent format: H3 headers (`### Learning: [title]`) with 3 sub-bullets (`- Context:`, `- Discovery:`, `- Rule:`). Examples from agent-cost-analyzer and prompt-version-control confirm this structure. The personal-blog project also follows this pattern.
Confidence: 0.95
Remaining_Ambiguity: Minor variations in formatting (e.g., extra blank lines, missing sub-bullets) must be handled gracefully.
Resolution: Parse LEARNINGS.md by splitting on `### Learning:` headers. Extract Context, Discovery, Rule from `- Context:`, `- Discovery:`, `- Rule:` prefixed lines. Handle missing fields gracefully (use empty string). The `description` maps to the title after `### Learning:`, `context` maps to Context + Discovery combined, and `rule` content informs the HarvestRule.rule field.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: How does the parser extract structured learnings from progress.txt, which is described as "세션별 자유 텍스트 로그" (free-text session log)? The spec requires no LLM, only regex-based heuristics.
A: Real progress.txt files are more structured than "free text" implies. They follow a consistent format: `=== Session TIMESTAMP ===` delimiters with fields like `Completed:`, `Changes:`, `Why:`, `Discovered:`, `Difficulty:`. The `Discovered:` field is particularly valuable — it contains runtime findings similar to LEARNINGS.md entries. The `Why:` field provides design rationale context.
Confidence: 0.90
Remaining_Ambiguity: Not all sessions have all fields. Some sessions have free-form text without field labels. Need a fallback strategy for unstructured entries.
Resolution: Parse progress.txt by splitting on `=== Session` delimiters. Within each session block, extract `Discovered:` and `Why:` fields as potential learning sources. For sessions without labeled fields, skip extraction (don't attempt to parse free-form text without LLM). Mark learnings from progress.txt with `source_file: "progress.txt"`.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: CRITICAL
Q: How are learnings matched across projects to compute confidence scores? The spec says "동일 학습이 2개 이상 프로젝트에서 반복 → confidence=high" but doesn't define what "동일 학습" (same learning) means without an LLM.
A: Without LLM-based semantic similarity, matching must be keyword-based. Two options: (1) exact category + overlapping stack tags = potential match, then check for keyword overlap in description/rule text; (2) match by generated rule ID (slugified from category + key terms). Option 2 is fragile. Option 1 is more robust. A reasonable heuristic: same category AND significant keyword overlap (e.g., Jaccard similarity on tokenized words > 0.5) AND at least one shared stack tag.
Confidence: 0.70
Remaining_Ambiguity: The threshold for "similar enough" is arbitrary. Jaccard > 0.5 may be too strict or too loose.
Resolution: Use category + stack overlap as primary grouping, then keyword overlap (tokenized words from description, ignoring stopwords) with Jaccard similarity >= 0.4 as the merge threshold. If two learnings match, merge into one HarvestRule with combined source_projects. Confidence levels: 3+ source_projects = "high", 2 = "medium", 1 = "low". This is a best-effort heuristic — document the threshold as configurable for future tuning.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: The spec says to detect revert patterns ("같은 파일이 추가→삭제→재추가") from `git log --stat`, but `git log --stat` only shows files changed and lines added/deleted per commit. It cannot distinguish file creation vs modification vs deletion. How should revert detection work?
A: `git log --stat` alone is insufficient for revert detection. You need either `git log --diff-filter=ADMRTUX --name-status` (which shows A=added, D=deleted, M=modified per file per commit) or `git log --name-status`. The `--name-status` format shows the operation type per file. To detect "add→delete→re-add", track each file's operation sequence across commits chronologically.
Confidence: 0.95
Remaining_Ambiguity: None — the solution is clear.
Resolution: Use `git log --name-status --format="%H"` instead of (or in addition to) `git log --stat` for file-level operation tracking. Parse operation codes (A/D/M/R) per file per commit. Detect revert pattern: a file that appears with A, then D, then A again (or M→D→A). Still use `--stat` for line-change counts (net_changes in FileChurn). The spec's mention of `--stat` is a suggestion, not a constraint on implementation.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What keywords map to each of the 6 learning categories (error-recovery, library-quirk, pattern, performance, testing, compatibility)?
A: The CLAUDE.md says "Category classification: keyword-based heuristic (not ML)" but provides no keyword list. Reasonable inference from the category names and real LEARNINGS.md content:
  - error-recovery: error, exception, crash, fail, fallback, retry, handle, catch, recover, fix, bug
  - library-quirk: library, import, version, API, behavior, unexpected, quirk, workaround, gotcha, caveat
  - pattern: pattern, architecture, design, approach, strategy, refactor, structure, convention
  - performance: performance, slow, fast, optimize, cache, memory, latency, throughput, efficient
  - testing: test, assert, mock, fixture, coverage, pytest, jest, spec, verify
  - compatibility: compatible, version, migrate, upgrade, downgrade, breaking, deprecated, legacy, polyfill
Confidence: 0.80
Remaining_Ambiguity: Keyword lists are guesses. Overlapping keywords (e.g., "version" could be library-quirk or compatibility). Priority/tiebreaker needed.
Resolution: Implement keyword lists as above. On overlap, use priority order: error-recovery > library-quirk > compatibility > pattern > performance > testing (most specific first). If no keywords match, default to "pattern" as the most generic category. Keywords should be matched case-insensitively against the full learning text (title + context + rule).
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: How are stack tags extracted from LEARNINGS.md text content? The spec says "파일 확장자/라이브러리 언급에서" but doesn't define the mapping.
A: Two sources for stack detection: (1) project-level detection from marker files (pyproject.toml → python, etc. — well-defined in spec), and (2) text-level extraction from learning content. For text-level: scan for known library/framework names (e.g., "pytest" → python, "React" → react, "Spring" → spring, "Next.js" → nextjs) and file extensions mentioned (e.g., ".py" → python, ".java" → java, ".tsx" → react).
Confidence: 0.85
Remaining_Ambiguity: The library-to-stack mapping needs to be comprehensive but not infinite. Where is the boundary?
Resolution: Maintain a static dictionary mapping ~30-50 common library/extension names to stack tags. Start with libraries mentioned in real harness outputs (pytest, ruff, mypy → python; Jest, React, Next.js → nextjs/react; Spring, MyBatis → java/spring; Cargo → rust; go.mod → go). Additionally, the project-level stack detection (from marker files) should be used as a fallback/default when no text-level stacks are found. `applicable_stacks` should be the union of text-detected and project-detected stacks.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: How are multiple LearningEntry items synthesized into a single HarvestRule? The spec says "추출된 학습 + git 분석 결과를 종합하여 재사용 가능한 룰 생성" but doesn't define the synthesis algorithm.
A: Two scenarios: (1) Single-project mode: each learning → one rule (1:1 mapping), with git analysis providing supplementary context. (2) Cross-project mode: matching learnings are merged into one rule with combined source_projects and elevated confidence. The `rule` text should come from the most detailed learning entry (longest rule text), and `applicable_to` should be a synthesis of all matched learnings' contexts.
Confidence: 0.75
Remaining_Ambiguity: In single-project mode, do git-only findings (instability, revert patterns) also generate rules, or are they only in the instability report?
Resolution: In single-project mode, each LearningEntry maps 1:1 to a HarvestRule. Git analysis results (FileChurn data) produce the instability-report.md and inform the `fix:` pattern extraction, but do NOT generate standalone HarvestRules (they lack the learning context needed for actionable rules). In cross-project mode, merge matching learnings using the similarity algorithm defined above, picking the most detailed rule text.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: How is a "project" identified within a gallery directory? The spec says `--gallery <gallery-dir>` scans all projects but doesn't define what constitutes a project.
A: The spec's input source diagram shows `.git/` as a component. A reasonable definition: a subdirectory of the gallery directory that contains a `.git/` directory OR any of the stack marker files (pyproject.toml, package.json, pom.xml, Cargo.toml, go.mod). Non-recursive (only immediate children of gallery dir).
Confidence: 0.85
Remaining_Ambiguity: Should nested projects (monorepo with sub-projects) be detected? Probably not for v1.
Resolution: A project is an immediate subdirectory of the gallery directory that contains at least one of: `.git/`, `pyproject.toml`, `package.json`, `pom.xml`, `Cargo.toml`, `go.mod`. Only scan one level deep (no recursive project discovery). Hidden directories (starting with `.`) are excluded.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What format should the skills output files (e.g., `skills/python-common.md`) have? The spec says "CLAUDE.md에 바로 복사 가능한 스킬 블록" but doesn't show the format.
A: Looking at real CLAUDE.md files in the repo, they contain markdown sections with headers, bullet points, and code blocks. A "CLAUDE.md-ready skill block" should be a markdown section with a clear header and bullet-pointed rules that can be copy-pasted into a project's CLAUDE.md under a `## Stack-Specific Rules` or similar section.
Confidence: 0.85
Remaining_Ambiguity: None significant.
Resolution: Skills files should be plain markdown with:
  - A top-level `# [Stack] Common Rules` header
  - `## Source` with the list of source projects
  - A bulleted list of rules, each prefixed with `- ` and containing the actionable rule text
  - Only include high and medium confidence rules (low confidence rules are too noisy for CLAUDE.md)
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: What threshold defines a file as "unstable" for the instability report? The spec says "자주 수정되는 파일 = '불안정 모듈'" but doesn't quantify "자주" (frequently).
A: Without an explicit threshold, a reasonable heuristic: a file modified in more than 30% of total commits, or with a modify_count > 5, or with any revert_count > 0. The spec's intent is to flag files that are disproportionately changed — this suggests a relative threshold (top N% of files by change frequency) rather than an absolute one.
Confidence: 0.70
Remaining_Ambiguity: The exact threshold is arbitrary. Different projects have different change patterns.
Resolution: Use a relative threshold: include files in the top 20% by modify_count, OR any file with revert_count > 0, OR any file with modify_count >= 5 (whichever produces results). Sort by modify_count descending. This captures both relatively unstable files and absolutely unstable ones. The instability report should show all FileChurn data, leaving interpretation to the user.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: The spec mentions extracting `fix:` patterns from commit messages → "에러 패턴 데이터베이스" but this database is not listed in the output format. Where does it go?
A: The output structure in the spec has no dedicated file for error patterns from commit messages. This data could either: (1) be folded into the rules/ output as rules with category "error-recovery", (2) be added to the instability report, or (3) become a new output file. Since the spec doesn't list it as a separate output, option (1) is most consistent — treat `fix:` commit messages as another input source for learning extraction.
Confidence: 0.80
Remaining_Ambiguity: How much context can be extracted from a commit message alone? Usually just a one-liner.
Resolution: Extract `fix:` prefixed commit messages as lightweight LearningEntry items with category="error-recovery", description = commit message (sans `fix:` prefix), context = associated files from the commit, and source_file = "git-log". These feed into the normal rule synthesis pipeline. Do NOT create a separate error pattern database — it's not in the spec's output structure.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: How are LearningEntry.id and HarvestRule.id generated? The spec says "자동 생성 (slugified)" for LearningEntry.id but doesn't specify the input to slugification.
A: Slugification typically takes a human-readable string and converts it to a URL-safe identifier. For LearningEntry.id: slugify the `description` field (the title from `### Learning: [title]`). For HarvestRule.id: the spec example shows `python-datetime-parsing` which is `stack-topic` format — slugify from a combination of primary stack + key terms from the rule description.
Confidence: 0.80
Remaining_Ambiguity: Slug collisions are possible if two learnings have similar titles.
Resolution: LearningEntry.id = slugify(description), truncated to 60 chars. If collision occurs, append `-2`, `-3`, etc. HarvestRule.id = slugify(primary_stack + "-" + first_meaningful_words_of_description), truncated to 60 chars, with same collision handling. Slugify function: lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens, strip leading/trailing hyphens.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MAJOR
Q: How should FileChurn distinguish between file addition, modification, and deletion when `git log --stat` only shows lines changed? The FileChurn dataclass has add_count, modify_count, delete_count as separate fields.
A: As established in the revert detection ambiguity, we need `git log --name-status` which shows A (added), M (modified), D (deleted), R (renamed) per file per commit. The add_count = number of commits where file appears with status A, modify_count = M count, delete_count = D count. The net_changes (총 변경 라인 수) comes from `git log --stat` or `--numstat` which shows insertions/deletions per file.
Confidence: 0.95
Remaining_Ambiguity: None — two git commands needed.
Resolution: Run two git commands: (1) `git log --name-status --format="%H"` for per-file operation types (A/M/D/R), (2) `git log --numstat --format="%H"` for per-file line changes. Combine results per file to populate FileChurn. R (rename) counts as delete of old path + add of new path (or track separately and count as modify — prefer counting as modify to avoid inflating add/delete counts).
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MINOR
Q: What does `--format json` produce? Does it replace ALL output (rules YAML, markdown reports) with a single JSON file, or just the rules?
A: The spec says `--format json` with comment "JSON 출력 (기본: yaml+md)". This implies the entire output switches format. However, converting markdown reports (instability-report.md, spec-guide.md, skills/*.md) to JSON would lose readability. More practically: rules switch from YAML to JSON, and summary.json is already JSON. Markdown reports stay as markdown.
Confidence: 0.75
Remaining_Ambiguity: Spec is ambiguous on scope of --format flag.
Resolution: `--format json` changes rules/ output from YAML to JSON format. summary.json is always JSON regardless of flag. Markdown files (instability-report.md, spec-guide.md, skills/*.md) remain markdown regardless of flag. This gives the most practical result.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MINOR
Q: What output does `--dry-run` produce? The spec says "파싱만 하고 파일 생성 안 함" but doesn't specify what the user sees.
A: A dry run that produces no output at all is useless. The intent is to preview what would be generated without writing to disk. Standard CLI convention: print a summary to stdout showing what files would be created and how many rules/learnings were extracted.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: `--dry-run` performs all parsing and analysis but does NOT write to the output directory. Instead, print to stdout: (1) number of learnings extracted, (2) number of rules synthesized, (3) list of output files that would be created, (4) category and stack distribution. Essentially, print the HarvestResult summary to stdout.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MINOR
Q: Does `--stack python` filter entire projects by detected stack, or filter individual rules by their stack tags?
A: Two interpretations: (1) only analyze projects whose detected stack includes "python", (2) analyze all projects but only output rules tagged with "python". In gallery mode, option (1) is more efficient (skip irrelevant projects entirely). In single-project mode, option (2) is the only sensible interpretation (you're already pointing at one project).
Confidence: 0.80
Remaining_Ambiguity: None significant.
Resolution: `--stack` filters at the rule output level (option 2). All projects are analyzed, but only rules whose `stacks` list includes the specified stack are included in output. This is consistent across single-project and gallery modes, and simpler to implement. A project may contain cross-stack learnings (e.g., a Python project learning about Docker).
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MINOR
Q: Does `--min-confidence` filter during extraction or at output time?
A: Since confidence is determined during the synthesis/merge phase (based on cross-project occurrence count), it must filter at output time — confidence isn't known until all projects are analyzed.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: `--min-confidence` filters rules at output time, after synthesis is complete. Values: "low" (includes all), "medium" (excludes low), "high" (only high). Default: include all (no filter).
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: EDGE_CASE
Severity: MINOR
Q: Does summary.json exactly mirror the HarvestResult dataclass, or does it contain additional/different fields?
A: The spec defines HarvestResult with specific fields. summary.json should be a direct serialization of HarvestResult. No reason to diverge.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: summary.json is a direct JSON serialization of HarvestResult. The `unstable_files` field serializes each FileChurn as a JSON object. Use `json.dumps` with `indent=2` for readability.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: The input source diagram lists IMPLEMENTATION_PLAN.md, CLAUDE.md, and specs/ as input sources, but the extraction logic only describes LEARNINGS.md, CLARITY_LOG.md, progress.txt, and git log. Are the other files used?
A: CLAUDE.md is explicitly used for stack detection (checking for stack markers). IMPLEMENTATION_PLAN.md and specs/ are listed in the diagram as part of the project structure but NOT referenced in the extraction features. They may be future inputs or simply shown for context about the project layout.
Confidence: 0.85
Remaining_Ambiguity: Are we leaving value on the table by not parsing these?
Resolution: For v1, only parse LEARNINGS.md, CLARITY_LOG.md, progress.txt, and git log as learning sources. CLAUDE.md is read only for stack detection context (not for learning extraction). IMPLEMENTATION_PLAN.md and specs/ are NOT parsed — they are shown in the diagram as project context only. This keeps scope manageable and matches the spec's feature descriptions.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: How is spec-guide.md generated? The spec says "Socratic Q&A에서 추출한 스펙 작성 시 명시해야 할 것들" and "반복되는 질문 패턴 → 스펙 작성 가이드라인으로 승격" but doesn't define the algorithm for detecting repeating question patterns.
A: In cross-project mode, if the same type of question (same Category in ClarityEntry) appears in multiple projects' CLARITY_LOG.md files, it indicates a common spec gap. For single-project mode, the spec-guide extracts all questions with high-confidence answers as "things to specify next time."
Confidence: 0.70
Remaining_Ambiguity: "Same type of question" is fuzzy. Category matching alone is too coarse.
Resolution: For spec-guide.md generation: (1) Group ClarityEntry items by Category across projects, (2) Within each category group, use keyword overlap (same approach as learning matching) to find recurring question patterns, (3) For each recurring pattern, write a guideline: "When writing specs, explicitly specify [topic of question]." For single-project mode, simply list all resolved questions as guidelines. spec-guide.md is a best-effort output — document its heuristic nature.
---
```

```
Round: 1
Spec: knowledge-harvester.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: What is ClarityEntry.decision extracted from? The CLARITY_LOG.md format shows a `Resolution:` field but the dataclass has a `decision` field.
A: The CLARITY_LOG.md format has a `Resolution:` line in each ambiguity block. This maps directly to ClarityEntry.decision. The naming difference (Resolution vs decision) is just a spec-to-implementation mapping.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: Parse `Resolution:` from CLARITY_LOG.md into ClarityEntry.decision. Parse `Q:` → question, `A:` → answer. The `Round:` line provides the round number.
---
```

### Cross-Spec Consistency Check

Only one spec file exists (`specs/knowledge-harvester.md`), so no cross-spec contradictions are possible. However, there are internal consistency points to verify between the spec and CLAUDE.md:

1. **Spec says "pyyaml만 의존" but CLAUDE.md also lists ruff and pytest as dev deps** — No contradiction; ruff and pytest are dev-only, not runtime dependencies. Consistent.

2. **Spec says "단일 pip install로 설치 가능" but project uses uv** — The spec's intent is simple installation. `pip install .` works with hatchling build-backend regardless of whether development uses uv. Consistent.

3. **Spec says `git log --stat` but implementation needs `--name-status`** — This is a spec imprecision, not a contradiction. The spec describes intent ("파일별 변경 빈도 분석") which is satisfied by a combination of git log flags. Resolved above.

4. **Data model vs output format alignment** — HarvestResult matches summary.json. HarvestRule matches the YAML example in the spec. LearningEntry is an internal model not directly output. FileChurn feeds into instability-report.md. All consistent.

5. **CLI entry point** — pyproject.toml defines `agent-harvest = "agent_harvest.cli:main"` matching the spec's `agent-harvest` CLI command. Consistent.

### Ambiguity Score

```
AMBIGUITY_SCORE: 0.05
Rounds_Completed: 1
Ambiguities_Found: 20
Ambiguities_Resolved: 19
Ambiguities_Remaining: 1
```

The one remaining ambiguity (cross-project learning matching threshold of Jaccard >= 0.4) is a tunable parameter, not a blocking ambiguity. It has a reasonable default and is documented as configurable.

```
CONVERGENCE_DATA:
  round: 1
  score: 0.05
  prev_score: 1.0
  delta: -0.95
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 0
  stagnation_count: 0
```

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.05
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
