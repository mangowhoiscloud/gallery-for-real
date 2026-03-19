# Implementation Plan
Generated: 2026-03-19T00:00:00Z
Total_Items: 5
Completed: 5
Test_Items: 5 (target: ≥70% of implementation items — each item includes tests, plus Item 5 is dedicated integration tests)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1, Item 2, Item 3]   # no dependencies between these
  - group_2: [Item 4]                   # depends on group_1
  - group_3: [Item 5]                   # depends on group_2
Build_Order: group_1 → group_2 → group_3
```

## Item 1: Tokenizer module
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/word-definition.md
- clarity_ref: CLARITY_LOG.md#Round-1, #Round-5, #Round-10, #Round-11
- description: Implement `src/word_counter/tokenizer.py` with a `tokenize(text: str) -> list[str]` function that extracts words from text. A word is a maximal sequence of Unicode alphanumeric characters and intra-word apostrophes. Hyphens split words. Apostrophes are kept only when flanked by alphanumeric characters on both sides; leading/trailing apostrophes are stripped. Underscores act as word separators. Multiple consecutive hyphens produce no empty tokens. Uses Unicode-aware character classes (not ASCII-only).
- acceptance:
  - `tokenize("hello, world!")` → `["hello", "world"]`
  - `tokenize("don't")` → `["don't"]`
  - `tokenize("'twas dogs'")` → `["twas", "dogs"]`
  - `tokenize("well-known")` → `["well", "known"]`
  - `tokenize("word--break")` → `["word", "break"]`
  - `tokenize("42 is a number")` → `["42", "is", "a", "number"]`
  - `tokenize("café naïve")` → `["café", "naïve"]`
  - `tokenize("my_variable")` → `["my", "variable"]`
  - Empty string → `[]`
- tests: `tests/test_tokenizer.py` — unit tests covering all word-definition rules, apostrophe boundaries, hyphens, Unicode, underscores, empty input, punctuation-only input, mixed edge cases. Target: ≥30 test cases.

## Item 2: Counter module
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/word-counter-cli.md
- clarity_ref: CLARITY_LOG.md#Round-2, #Round-4
- description: Implement `src/word_counter/counter.py` with a `count_words(words: list[str], ignore_case: bool = False) -> CountResult` function. `CountResult` is a dataclass/NamedTuple holding: `frequencies` (list of (word, count) tuples sorted by count descending then alphabetically ascending), `total` (total word count), `unique` (unique word count). When `ignore_case` is True, all words are lowercased before counting and displayed in lowercase.
- acceptance:
  - `count_words(["the", "a", "the"])` → frequencies=[("the", 2), ("a", 1)], total=3, unique=2
  - Tie-breaking: words with same count are sorted alphabetically
  - `count_words(["Hello", "hello"], ignore_case=True)` → frequencies=[("hello", 2)], total=2, unique=1
  - `count_words([])` → frequencies=[], total=0, unique=0
- tests: `tests/test_counter.py` — unit tests for counting, sorting order, tie-breaking, ignore-case, empty input. Target: ≥15 test cases.

## Item 3: Formatter module
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/word-counter-cli.md
- clarity_ref: CLARITY_LOG.md#Round-6, #Round-9
- description: Implement `src/word_counter/formatter.py` with `format_table(frequencies: list[tuple[str, int]], total: int, unique: int, top_n: int = 10) -> str`. Produces a formatted table matching the spec example: header row (`# | Word | Count | %`), separator row with `+`, data rows with adaptive column widths, right-aligned numbers, left-aligned words. Percentages formatted to one decimal place. Limits output to `top_n` entries. Appends summary line: `Total: {total} words, {unique} unique words`. Handles zero-word case gracefully.
- acceptance:
  - Output matches spec format with `+` separators and adaptive widths
  - Percentages use exactly one decimal place (e.g., `8.4%`)
  - `top_n` limits rows; `top_n=3` with 10 entries shows only 3
  - Zero words → header + separator + summary with 0/0
  - Column widths adapt to longest word and largest count
- tests: `tests/test_formatter.py` — unit tests for format correctness, column alignment, percentage formatting, top-N limiting, zero-word edge case, wide words/large counts. Target: ≥15 test cases.

## Item 4: CLI module
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3]
- spec: specs/word-counter-cli.md
- clarity_ref: CLARITY_LOG.md#Round-3, #Round-7, #Round-8
- description: Implement `src/word_counter/cli.py` with a `main()` function as the entry point for the `wc-freq` command. Uses argparse for `--top N` (positive integer, default 10) and `--ignore-case` flags, plus positional file path arguments. Reads from stdin when no files given (and stdin is not a TTY). Aggregates text from all input sources. Prints errors to stderr for missing files and continues with remaining files. Exits with code 1 when no valid input (all files failed + no stdin). Orchestrates tokenizer → counter → formatter pipeline.
- acceptance:
  - `wc-freq file1.txt file2.txt` aggregates both files
  - `echo "hello world" | wc-freq` reads from stdin
  - `wc-freq --top 5 --ignore-case file.txt` works correctly
  - `wc-freq nonexistent.txt` prints error to stderr, exits 1
  - `wc-freq nonexistent.txt valid.txt` prints error for first, processes second
  - `wc-freq --top 0` produces argument error
  - `wc-freq --top -1` produces argument error
  - `wc-freq --top abc` produces argument error
- tests: `tests/test_cli.py` — unit tests for argument parsing, file reading, stdin handling, error paths, exit codes. Uses subprocess or monkeypatching. Target: ≥20 test cases.

## Item 5: Integration tests with test data
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 4]
- spec: specs/word-counter-cli.md, specs/word-definition.md
- clarity_ref: CLARITY_LOG.md (all resolutions)
- description: Create test data files in `tests/fixtures/` and end-to-end integration tests in `tests/test_integration.py`. Tests invoke the CLI via subprocess (or `main()` directly) with real text files and verify full output including table format and summary line. Covers: single file, multiple files, stdin pipe, `--ignore-case`, `--top N`, missing file errors, empty file, Unicode content, mixed edge cases from both specs.
- acceptance:
  - Full pipeline test: file → tokenize → count → format → verify output
  - Tests use actual text files with known word counts
  - At least one test per clarity resolution that affects output
  - All 11 clarity resolutions exercised across the test suite
- tests: `tests/test_integration.py` + `tests/fixtures/` — end-to-end tests. Target: ≥15 test cases.

PHASE_1_COMPLETE
