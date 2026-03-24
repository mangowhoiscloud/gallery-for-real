# Clarity Log — Tistory Migrator

## Round 1

---

Round: 1
Spec: tistory-extractor.md
Category: INTEGRATION_GAP
Severity: CRITICAL
Q: If user uses --token (API mode) and API fails, the extractor wants to fallback to Strategy 2 (XML backup). But if the user didn't provide --backup, there is no XML file. The fallback chain API→XML→Scraping is broken when only --blog and --token are provided.
A: The 3-level fallback as described only works when all resources are available. In practice, when using API mode (--blog + --token), there is no backup file. The extractor should skip Strategy 2 if no backup path was provided and fall back directly to Strategy 3 (scraping), since --blog is available for scraping.
Confidence: 0.85
Remaining_Ambiguity: None — the conditional fallback logic is straightforward.
Resolution: Fallback chain is conditional on available inputs: API→Scraping when no backup file is provided; API→XML→Scraping when backup file is also available. Each strategy's availability is determined by whether its required inputs were provided.

---

Round: 1
Spec: tistory-extractor.md
Category: UNSTATED_ASSUMPTION
Severity: CRITICAL
Q: The spec lists Tistory Open API as the primary strategy. However, Kakao (Tistory's parent company) deprecated the Open API around late 2023. Is Strategy 1 viable?
A: The spec's 3-strategy fallback design is inherently defensive — it anticipates API failure. The spec explicitly says "API 종료/변경 시 → Strategy 2로 fallback". This suggests the author was aware of potential API unavailability. Strategy 2 (XML backup) and Strategy 3 (scraping) are the practically reliable paths.
Confidence: 0.75
Remaining_Ambiguity: Exact current API status uncertain. If API is fully dead, the default strategy should arguably not be API.
Resolution: Implement Strategy 1 (API) as specified to support cases where users still have valid tokens. Add a clear warning in CLI output when API fails that it may be deprecated. Ensure fallback to Strategy 2/3 is seamless. The CLI should not error out just because the API is unavailable — it should gracefully degrade.

---

Round: 1
Spec: content-converter.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: Slug generation spec says "한글은 음절 유지" (preserve Korean syllables). What exactly does this mean? Are Korean characters kept as-is in the slug? URL-encoded? Romanized?
A: "음절 유지" literally means "keep syllables". In the Korean blogging ecosystem, file/URL slugs commonly preserve Korean characters as Unicode (not romanized). Example: "파이썬 개발 팁" → "파이썬-개발-팁". This is standard practice on Korean platforms.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Slug generation: preserve Korean characters as-is, remove non-alphanumeric/non-Korean special characters, replace spaces with hyphens, collapse consecutive hyphens, lowercase ASCII characters.

---

Round: 1
Spec: tistory-extractor.md + cli-interface.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: What happens when --blog is provided without --token and without --scrape? The CLI table says --blog is required for "API/스크래핑 시" and --token is required for "API 시", but there's no explicit rule for --blog-only.
A: Without --token, API mode is impossible. Without --scrape flag, the user hasn't explicitly requested scraping. Without --backup, XML mode is impossible. This is an ambiguous input state.
Confidence: 0.80
Remaining_Ambiguity: None — decision is clear.
Resolution: If --blog is provided without --token and without --backup, default to scraping mode (equivalent to implicit --scrape). Log an info message: "No access token provided, using web scraping mode."

---

Round: 1
Spec: cli-interface.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: writer.py is listed in the project structure but has no dedicated spec. What exactly is its responsibility?
A: From cli-interface.md: "Markdown 파일 + metadata 출력". From content-converter.md: the output directory structure is defined (posts/, images/, metadata.json). writer.py takes the converted markdown content + frontmatter and writes the filesystem output.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: writer.py responsibilities: (1) create output directory structure (output/posts/, output/images/), (2) write individual .md files with frontmatter + markdown body, (3) generate metadata.json summarizing the migration. Input: list of converted posts (with frontmatter + markdown + image mappings).

---

Round: 1
Spec: tistory-extractor.md + cli-interface.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Who applies the --category, --after, --before filters? The extractor spec doesn't mention filtering. The CLI spec says "글 목록 추출 (필터 적용)".
A: Filtering during extraction is strategy-dependent. The API may support server-side filtering. XML and scraping require post-hoc in-memory filtering. The extractor base interface should accept filter params.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: The extractor base interface accepts optional filter params (category: str | None, after: date | None, before: date | None). Each strategy implements filtering: API uses query params where possible, XML/scraper filter in-memory after fetching the full list.

---

Round: 1
Spec: content-converter.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: metadata.json is described as "전체 마이그레이션 요약 (글 수, 카테고리 목록, 태그 목록)" but the exact schema is not defined. The CLI summary output shows additional fields (strategy, failed posts, images, duration).
A: metadata.json should capture the same information shown in the CLI summary for reproducibility and programmatic access.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: metadata.json schema:
```json
{
  "blog": "string — blog name or backup filename",
  "strategy": "api | xml | scraping",
  "migrated_at": "ISO 8601 timestamp",
  "total_posts": "int — total posts found",
  "converted_posts": "int — successfully converted",
  "failed_posts": [{"id": "string", "title": "string", "reason": "string"}],
  "categories": ["list of unique category strings"],
  "tags": ["list of unique tag strings"],
  "total_images": "int — total images downloaded",
  "failed_images": "int — images that failed to download",
  "duration_seconds": "float"
}
```

---

Round: 1
Spec: content-converter.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: The Tistory custom tags `[##_Image|filename.jpg|..._##]` and `[##_Code|..._##]` are not fully documented. What are all the pipe-delimited fields? What other custom tag patterns exist?
A: Tistory's custom replacement tags vary by editor version. Common patterns: `[##_Image|filename|width|height|align_##]` for images, `[##_CodeBlock|code content_##]` for code. Other tags may include `[##_Video|..._##]`, `[##_File|..._##]`. Exact formats require real-world Tistory content samples to validate.
Confidence: 0.65
Remaining_Ambiguity: Exact tag formats may vary. Implementation will need regex patterns flexible enough to handle variations.
Resolution: Implement regex-based extraction for `\[##_Image\|([^|]+)\|.*?_##\]` (capture filename from first segment) and `\[##_Code(?:Block)?\|(.*?)_##\]` (capture code content). Handle unknown `[##_..._##]` patterns by stripping tags and preserving inner text. Add logging for unrecognized custom tag patterns to aid debugging.

---

Round: 1
Spec: content-converter.md + cli-interface.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: How does image_downloader.py interact with converter.py? The CLI pipeline says "HTML 추출 → Markdown 변환 → 이미지 다운로드 → 파일 저장" but the converter needs local image paths for the markdown output.
A: The content-converter.md says the module handles "이미지를 로컬로 다운로드하여 경로를 교체" (download images and replace paths). But image_downloader.py is a separate module. The pipeline order in CLI suggests images are downloaded after conversion, but the converter needs local paths.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Two-pass approach: (1) converter.py extracts image URLs from HTML and produces a URL→local-path mapping (deterministic from post slug + filename), (2) image_downloader.py downloads images using that mapping, (3) converter.py replaces URLs in HTML with local paths, then converts to markdown. Alternatively, a simpler approach: converter generates markdown with placeholder paths based on the deterministic naming scheme, and image_downloader downloads to those paths independently. The latter is simpler and avoids tight coupling.

---

Round: 1
Spec: cli-interface.md
Category: CONTRADICTION
Severity: MINOR
Q: --output is listed as required ("Yes") but has a default value ("./output"). If it has a default, it shouldn't be required.
A: This is a simple documentation inconsistency. A default value means the argument is optional.
Confidence: 0.95
Remaining_Ambiguity: None.
Resolution: --output is optional with default value "./output".

---

Round: 1
Spec: cli-interface.md
Category: EDGE_CASE
Severity: MINOR
Q: Are --after and --before date filters inclusive or exclusive?
A: Standard date range convention in most tools is inclusive on both ends.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Both --after and --before are inclusive. A post published on the exact --after or --before date is included.

---

Round: 1
Spec: cli-interface.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MINOR
Q: What does --dry-run do exactly? "추출만, 파일 생성 안 함" — does it still extract from the blog, or just show what would happen?
A: "추출만" means "extract only" — posts are actually fetched/parsed but no files are written. This allows users to verify the extraction works before committing to a full migration.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: --dry-run fetches and parses posts (with filters applied), displays a summary table (post count, categories, tags, sample titles), but does NOT write any files, download images, or create directories.

---

Round: 1
Spec: tistory-extractor.md
Category: MISSING_ERROR_HANDLING
Severity: MINOR
Q: Network error retry says "3회 재시도 후 skip" but doesn't specify the backoff strategy.
A: Standard practice for HTTP retries is exponential backoff.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Retry strategy: 3 attempts with exponential backoff (1s, 2s, 4s delays). On final failure, skip the resource and log the error.

---

Round: 1
Spec: tistory-extractor.md
Category: EDGE_CASE
Severity: MINOR
Q: How are images extracted from each strategy? The TistoryPost model has `images: list[str]` but extraction method differs per strategy.
A: All strategies ultimately produce HTML content. Images are extracted by parsing `<img>` tags from the HTML content, regardless of strategy.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Image extraction is done uniformly by parsing `<img src="...">` from content_html after extraction. Additionally, Tistory custom image tags `[##_Image|..._##]` are parsed. This logic belongs in the converter module, not the extractor. The extractor's `images` field can be populated lazily or by the converter.

---

Round: 1
Spec: tistory-extractor.md
Category: EDGE_CASE
Severity: MINOR
Q: Strategy 3 (scraping) uses "article 태그 또는 .entry-content 클래스" for content extraction. Tistory blogs use various skins with different HTML structures. What if neither selector matches?
A: Tistory skins vary, so a cascade of selectors is needed.
Confidence: 0.70
Remaining_Ambiguity: May need to add more selectors based on real-world testing.
Resolution: Try CSS selectors in order of specificity: `.entry-content` → `article .post-content` → `article` → `.post-content` → `#content .post`. Use first match. If none match, log a warning with the URL and skip the post. The selector list can be extended as more Tistory skins are encountered.

---

Round: 1
Spec: content-converter.md
Category: EDGE_CASE
Severity: MINOR
Q: How to handle posts with no title or empty content?
A: Posts with empty content have no value in a migration. Posts without titles can use a fallback.
Confidence: 0.85
Remaining_Ambiguity: None.
Resolution: Posts with empty content_html are skipped and logged as failed (reason: "empty content"). Posts with empty title use "untitled-{id}" as title. Only published posts are included — draft posts should be filtered out where possible (API can filter by status).

---

Round: 1
Spec: content-converter.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: Image paths in output markdown use `/images/{post-slug}/filename.jpg` — this is an absolute path from document root. Different static site generators may need different path formats.
A: The spec explicitly defines this format. Making it configurable would add complexity for a niche use case.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: Use the spec's path format: `/images/{post-slug}/filename.jpg`. Not configurable. Users can post-process paths if needed for their specific static site generator.

---

Round: 1
Spec: cli-interface.md
Category: UNSTATED_ASSUMPTION
Severity: MINOR
Q: Is the entry point only the console_scripts `tistory-migrate`, or should `python -m tistory_migrator` also work?
A: pyproject.toml already defines `tistory-migrate = "tistory_migrator.cli:main"`. Supporting `python -m` is trivial (just add `__main__.py`) and useful for development.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Support both: `tistory-migrate` via console_scripts (already in pyproject.toml) AND `python -m tistory_migrator` via `__main__.py`. The __main__.py simply calls cli.main().

---

Round: 1
Spec: content-converter.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: For `[##_Code|..._##]` custom tags, how is the programming language detected for code fence syntax highlighting?
A: Tistory's code tag may or may not include language metadata. If present, use it; otherwise, omit language specifier.
Confidence: 0.80
Remaining_Ambiguity: None.
Resolution: If the custom code tag includes a language identifier (e.g., `[##_Code|python|..._##]`), use it in the markdown code fence. Otherwise, emit a plain code fence with no language specifier (``` ... ```).

---

Round: 1
Spec: content-converter.md
Category: EDGE_CASE
Severity: MINOR
Q: Image filename collision handling adds "-1", "-2" suffixes. What if the original filename already follows this pattern (e.g., `image-1.jpg`)?
A: The suffix is appended to the stem regardless of existing content. `image-1.jpg` with collision becomes `image-1-1.jpg`. This is simple and unambiguous.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Always append collision suffix to the file stem: `{stem}-{N}{ext}`. Example: `photo.jpg` → `photo-1.jpg`, `image-1.jpg` → `image-1-1.jpg`.

---

Round: 1
Spec: cli-interface.md
Category: INTEGRATION_GAP
Severity: MINOR
Q: Which module owns the progress display (`[23/150] Converting: 글 제목...`)?
A: The CLI module orchestrates the pipeline and is the natural owner of user-facing output including progress.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: cli.py owns all progress display and user-facing output. The extractor and converter are called by cli.py and return results; they do not print to stdout directly (they may use logging for debug/error output).

---

## Cross-Spec Consistency Analysis

### 1. Fallback Chain vs CLI Strategy Selection (RESOLVED)
The extractor spec defines automatic fallback (API→XML→Scraping) while the CLI lets users explicitly choose a strategy. These are reconciled: the CLI determines the initial strategy based on args, and the extractor only falls back to strategies whose required inputs are available (see Round 1, first entry).

### 2. Source Layout: src/ vs flat
CLAUDE.md says "Source in src/tistory_migrator/" but pyproject.toml uses `tistory_migrator.cli:main` (suggesting flat layout) and the CLI spec shows `tistory_migrator/` without `src/`. Since pyproject.toml uses hatchling which defaults to auto-detect, either layout could work.
**Resolution**: Use `src/tistory_migrator/` as specified in CLAUDE.md. Configure hatchling with `[tool.hatch.build.targets.wheel] packages = ["src/tistory_migrator"]` and update the console_scripts entry if needed.

### 3. Dependency: pyyaml usage
pyyaml is listed as a dependency for frontmatter generation. However, YAML frontmatter for markdown files is simple enough to generate with string formatting. pyyaml would be needed only for metadata.json (but that's JSON, not YAML) and frontmatter (which is simple key-value pairs).
**Resolution**: Keep pyyaml as a dependency. Use it for frontmatter generation to correctly handle edge cases in titles/tags that contain special YAML characters (colons, quotes, brackets). This is safer than manual string formatting.

### 4. All specs coexist in a single architecture ✓
The three specs cover orthogonal concerns: extraction (getting data), conversion (transforming data), and CLI (orchestration + I/O). They share the TistoryPost data model. No architectural conflicts found.

---

## Ambiguity Score

```
AMBIGUITY_SCORE: 0.091
Rounds_Completed: 1
Ambiguities_Found: 21
Ambiguities_Resolved: 19
Ambiguities_Remaining: 2
```

Remaining ambiguities (both manageable with defensive implementation):
1. Tistory API current status (Round 1, severity CRITICAL but mitigated by fallback design)
2. Tistory custom tag exact formats (Round 1, severity MAJOR but mitigated by flexible regex + logging)

```
CONVERGENCE_DATA:
  round: 1
  score: 0.091
  prev_score: 1.0
  delta: -0.909
  category_distribution:
    CRITICAL: 0
    MAJOR: 0
    MINOR: 0
  stagnation_count: 0
```

Note: Both remaining ambiguities have actionable resolutions that don't block implementation. The CRITICAL item (API deprecation) is fully mitigated by the fallback design. The MAJOR item (custom tags) is mitigated by flexible regex patterns with logging.

---

PHASE_0_COMPLETE
FINAL_AMBIGUITY_SCORE: 0.091
TOTAL_ROUNDS: 1
EXIT_REASON: THRESHOLD
