# Learnings

### Learning: pytest and ruff not pre-installed
- Context: Running `uv run pytest` after project setup
- Discovery: pyproject.toml had no dev dependencies — pytest and ruff must be added explicitly
- Rule: Always run `uv add --dev pytest ruff` before first test run in a new uv project

### Learning: hatchling requires explicit wheel package config
- Context: `uv run pytest` failed with hatchling ValueError about file selection
- Discovery: When src/ layout is used, `[tool.hatch.build.targets.wheel] packages = ["src/tistory_migrator"]` is required
- Rule: Add hatch wheel packages config to pyproject.toml when using src/ layout with hatchling

### Learning: FailedPost is a separate dataclass (not a count int)
- Context: IMPLEMENTATION_PLAN.md listed `failed_posts` in MigrationResult but CLARITY_LOG defines it as list of objects
- Discovery: CLARITY_LOG schema shows `failed_posts: [{"id", "title", "reason"}]` — need a FailedPost dataclass
- Rule: Always check CLARITY_LOG for exact schema details, not just IMPLEMENTATION_PLAN field names

### Learning: markdownify ATX headings and list bullets
- Context: Converting Tistory HTML to Markdown with markdownify
- Discovery: Pass heading_style='ATX' for # headings and bullets='-' for hyphen list items; defaults produce setext-style headings and * bullets which may differ from target static-site generators
- Rule: Always specify heading_style='ATX' and bullets='-' when calling markdownify for Tistory content

### Learning: pyyaml auto-quotes date-like strings in frontmatter
- Context: Frontmatter generation with yaml.dump({'date': '2024-01-15'})
- Discovery: pyyaml quotes date strings (output: `date: '2024-01-15'`) so yaml.safe_load returns them as strings, not datetime.date objects — the test assertion `parsed['date'] == '2024-01-15'` (string) works correctly
- Rule: No manual quoting needed for date fields; yaml.dump with allow_unicode=True handles special cases automatically

### Learning: Python 3.14 RobotFileParser defaults to deny-all
- Context: Implementing robots.txt check in scraper extractor
- Discovery: `urllib.robotparser.RobotFileParser().can_fetch("*", url)` returns False when parser is uninitialized (Python 3.14 changed the default from allow-all to deny-all)
- Rule: Always set `rp.allow_all = True` explicitly when robots.txt is unavailable or parsing fails; never rely on an uninitialized parser allowing access

### Learning: markdownify has built-in code_language_callback option
- Context: Implementing language-aware code fences from <code class="language-xxx">
- Discovery: markdownify.MarkdownConverter (and markdownify() function) accept a code_language_callback kwarg. The callback receives the <pre> element and should return a language string. No subclassing needed.
- Rule: Pass code_language_callback=fn to markdownify() instead of subclassing MarkdownConverter for language extraction.

### Learning: Tistory CDN URL path ending with slash gives empty basename
- Context: Extracting filename from https://img.daumcdn.net/thumb/R800x0/ style URLs
- Discovery: os.path.basename('/thumb/R800x0/') returns '' (empty string) because path ends with /. Fallback to 'image.jpg' is correct.
- Rule: Always check for empty basename from urlparse + os.path.basename and apply fallback filename.
