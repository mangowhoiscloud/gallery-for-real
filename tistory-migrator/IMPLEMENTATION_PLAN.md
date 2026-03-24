# Implementation Plan
Generated: 2026-03-24T23:45:00+09:00
Total_Items: 9
Completed: 9
Test_Items: 9 (target: ≥70% of implementation items — each item includes companion tests)

## Dependency Graph
```
Independent_Groups:
  - group_1: [Item 1]                          # data models — no dependencies
  - group_2: [Item 2, Item 3, Item 7, Item 8]  # depend only on Item 1
  - group_3: [Item 4, Item 5, Item 6]          # depend on Items 1, 2
  - group_4: [Item 9]                          # depends on all
Build_Order: group_1 → group_2 → group_3 → group_4
```

## Spec-Reinforced Rules (from previous build bugs)
These MUST be verified in acceptance tests — they caused regressions previously:
1. **XML `<published>` parsing**: Must produce real datetime. `datetime.min` (0001-01-01) is forbidden as a default
2. **XML `<tags>` parsing**: Each `<tag>` child element → individual string in `tags: list[str]`. Must not be empty when tags exist in XML
3. **Output filename format**: `{YYYY-MM-DD}-{slug}.md` — date prefix from `published_at` is mandatory
4. **Code language detection**: `<code class="language-xxx">` → ` ```xxx ` in markdown. Must detect language from class attribute

---

## Item 1: Package skeleton and data models
- status: DONE
- priority: P0
- complexity: S
- depends_on: []
- spec: specs/tistory-extractor.md, specs/content-converter.md, specs/cli-interface.md
- clarity_ref: CLARITY_LOG.md#Round-1 (metadata.json schema, FailedPost dataclass)
- description: Create TistoryPost, FailedPost, and MigrationResult dataclasses in models.py. TistoryPost holds extracted post data. FailedPost tracks id/title/reason for failures. MigrationResult holds migration summary with to_dict() for JSON serialization. Also create __main__.py entry point and fix pyproject.toml dev dependencies.
- acceptance:
  - TistoryPost fields: id(str), title(str), content_html(str), category(str), tags(list[str]), published_at(datetime), url(str), images(list[str])
  - FailedPost fields: id(str), title(str), reason(str)
  - MigrationResult fields: blog, strategy, migrated_at(datetime), total_posts, converted_posts, failed_posts(list[FailedPost]), categories(list[str]), tags(list[str]), total_images, failed_images, duration_seconds(float)
  - MigrationResult.to_dict() serializes to metadata.json-compatible dict (ISO 8601 for migrated_at, FailedPost as dicts)
  - __main__.py enables `python -m tistory_migrator`
  - `uv run pytest tests/test_models.py` passes
- tests: tests/test_models.py — dataclass creation, equality, to_dict() output, ISO timestamps, zero/empty edge cases

## Item 2: Extractor base interface
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1]
- spec: specs/tistory-extractor.md
- clarity_ref: CLARITY_LOG.md#Round-1 (filter params on base interface)
- description: Create BaseExtractor ABC in extractor/base.py with abstract `name` property and `extract()` method. The extract() method accepts optional category, after, before filter params (all inclusive). Create extractor/__init__.py with public exports.
- acceptance:
  - Cannot instantiate BaseExtractor directly (TypeError)
  - Concrete subclass must implement both `name` (property) and `extract()`
  - extract() signature: `(category: str | None = None, after: datetime | None = None, before: datetime | None = None) -> list[TistoryPost]`
  - All filter defaults are None
  - Package import works: `from tistory_migrator.extractor import BaseExtractor`
  - `uv run pytest tests/extractor/test_base.py` passes
- tests: tests/extractor/test_base.py — abstract instantiation fails, concrete subclass works, filter defaults, package imports

## Item 3: Content converter
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1]
- spec: specs/content-converter.md
- clarity_ref: CLARITY_LOG.md#Round-1 (slug Korean Unicode, Tistory custom tags, image two-pass, code language detection)
- description: Create converter.py with generate_slug(), process_tistory_tags(), _replace_img_srcs(), _generate_frontmatter(), and convert_post(). Slug preserves Korean Unicode syllables. Tistory custom tags converted via regex. Image URLs replaced with deterministic local paths. Frontmatter generated with pyyaml. convert_post() is the full pipeline.
- acceptance:
  - generate_slug("파이썬 개발 팁") → "파이썬-개발-팁" (Korean preserved, spaces→hyphens)
  - generate_slug removes special chars, collapses consecutive hyphens, strips leading/trailing hyphens, lowercases ASCII
  - process_tistory_tags converts `[##_Image|file.jpg|..._##]` → `<img src="file.jpg">`
  - process_tistory_tags converts `[##_Code|python|code_##]` → `<pre><code class="language-python">code</code></pre>`
  - **SPEC-REINFORCED**: `<code class="language-xxx">` → ` ```xxx ` code fence (language detected from class attribute)
  - _replace_img_srcs replaces URLs with `/images/{slug}/{filename}`
  - _generate_frontmatter outputs valid YAML with title, date, category, tags, slug, original_url
  - convert_post() produces frontmatter + markdown body
  - **SPEC-REINFORCED**: convert_post uses `heading_style='ATX'` and `bullets='-'` for markdownify
  - `uv run pytest tests/test_converter.py` passes
- tests: tests/test_converter.py — slug generation (Korean, ASCII, special chars, edge cases), tistory tag conversion, img src replacement, frontmatter generation (YAML special chars), full pipeline

## Item 4: Tistory Open API extractor
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/tistory-extractor.md
- clarity_ref: CLARITY_LOG.md#Round-1 (API deprecation handling, filter application, retry strategy)
- description: Create extractor/api.py with TistoryApiExtractor, ApiAuthError, ApiUnavailableError. Implements BaseExtractor. Uses Tistory Open API endpoints (/post/list, /post/read, /category/list). Rate limiting (1s between requests). Retry with exponential backoff (1s, 2s, 4s). Auth errors propagate for CLI fallback. Individual post failures are skipped.
- acceptance:
  - Implements BaseExtractor (name="api")
  - _request() sleeps rate_limit on first attempt, exponential backoff on retries
  - ApiAuthError raised on 401 (propagates to CLI for fallback)
  - ApiUnavailableError after 3 retries (individual post skipped)
  - Pagination via page parameter on /post/list
  - Category mapping via /category/list
  - Date filtering inclusive (after <= published_at <= before)
  - Category filtering case-insensitive
  - Images extracted via `<img src>` regex from content_html
  - `uv run pytest tests/extractor/test_api.py` passes
- tests: tests/extractor/test_api.py — rate limit sleep ordering, auth vs unavailable errors, pagination, tag parsing, category mapping, date filtering, individual post failure skip, all HTTP mocked

## Item 5: XML Backup extractor
- status: DONE
- priority: P0
- complexity: S
- depends_on: [Item 1, Item 2]
- spec: specs/tistory-extractor.md
- clarity_ref: CLARITY_LOG.md#Round-1 (filter application)
- description: Create extractor/backup.py with TistoryBackupExtractor, BackupFileNotFoundError, BackupParseError. Parses user-downloaded XML backup files. Supports two id formats (attribute vs child element), three date formats, individual tag elements.
- acceptance:
  - Implements BaseExtractor (name="xml")
  - Uses ET.fromstring() for in-memory parsing (testable without file I/O)
  - Supports `<post id="N">` attribute AND `<id>N</id>` child element
  - **SPEC-REINFORCED**: `<published>` parsed to real datetime via fromisoformat() or strptime(). Three formats: `%Y-%m-%d %H:%M:%S`, ISO with T, date-only. Must NOT default to datetime.min
  - **SPEC-REINFORCED**: `<tags>` with `<tag>` children → each tag text in list. Must not be empty when tags exist
  - `<category>` text stored as-is in category field
  - `<content>` CDATA HTML stored in content_html
  - BackupFileNotFoundError on missing file, BackupParseError on malformed XML
  - Date/category filtering inclusive, case-insensitive category
  - Empty content posts skipped
  - `uv run pytest tests/extractor/test_backup.py` passes
- tests: tests/extractor/test_backup.py — XML parsing, two id formats, three date formats, tag element parsing, category/date filters, error types, empty content skip, all file I/O mocked

## Item 6: Web scraper extractor
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2]
- spec: specs/tistory-extractor.md
- clarity_ref: CLARITY_LOG.md#Round-1 (selector cascade, Python 3.14 RobotFileParser)
- description: Create extractor/scraper.py with TistoryScraperExtractor, ScraperBlockedError. URL discovery via sitemap.xml (with namespace stripping) or archive page fallback. Content extraction via CSS selector cascade. Rate limiting (2s). robots.txt compliance with Python 3.14 compatibility (explicit allow_all=True).
- acceptance:
  - Implements BaseExtractor (name="scraper")
  - Discovery: sitemap.xml first (XML namespace stripped via regex), archive page fallback
  - robots.txt loaded once before crawl; on 404/failure, set allow_all=True explicitly (Python 3.14 compat)
  - Content selector cascade: `.entry-content` → `article .post-content` → `article` → `.post-content` → `#content .post`
  - Title: og:title meta → h1 fallback
  - Published: meta[property="article:published_time"] → time[datetime] → datetime.min
  - Category selectors: `.category a` → `.link_cate`
  - Tag selectors: `.tag a` → `.link_tag`
  - Rate limit: 2s between requests
  - Per-URL 403 → ScraperBlockedError with partial_posts attribute
  - Other per-URL errors → skip + log
  - Date/category filtering inclusive
  - `uv run pytest tests/extractor/test_scraper.py` passes
- tests: tests/extractor/test_scraper.py — sitemap parsing, archive fallback, robots.txt with allow_all, selector cascade, title/date/category/tag extraction, 403 handling, error skipping, all HTTP mocked

## Item 7: Image downloader
- status: DONE
- priority: P1
- complexity: M
- depends_on: [Item 1]
- spec: specs/content-converter.md
- clarity_ref: CLARITY_LOG.md#Round-1 (image two-pass approach, filename collision)
- description: Create image_downloader.py with ImageDownloader and ImageDownloadResult. Downloads images per post to {output}/images/{slug}/. Collision resolution appends -1, -2 to stem. Retry with exponential backoff (404/410 no retry, 5xx/timeout 3 retries). Rate limiting (0.5s between requests). no_images mode returns immediately.
- acceptance:
  - _url_to_filename() extracts filename from URL, fallback to "image.jpg"
  - Collision resolution: `photo.jpg` → `photo-1.jpg`, `image-1.jpg` → `image-1-1.jpg`
  - Per-post collision tracking (no global state, each post has own slug dir)
  - 404/410 → permanent failure (no retry); 5xx/timeout → 3 retries with exponential backoff
  - Rate limit: 0.5s sleep between requests (not before first)
  - no_images=True → return immediately with failed=total
  - ImageDownloadResult: mapping(dict), total(int), succeeded(int), failed(int)
  - `uv run pytest tests/test_image_downloader.py` passes
- tests: tests/test_image_downloader.py — URL to filename, collision resolution, retry logic (permanent vs retryable), rate limiting, no_images skip, result statistics, all HTTP mocked

## Item 8: Writer module
- status: DONE
- priority: P1
- complexity: S
- depends_on: [Item 1]
- spec: specs/content-converter.md, specs/cli-interface.md
- clarity_ref: CLARITY_LOG.md#Round-1 (writer responsibilities, dry-run behavior)
- description: Create writer.py with Writer class. Wraps filesystem I/O for creating directories, writing .md posts, and generating metadata.json. Dry-run mode skips all writes. Korean UTF-8 output with ensure_ascii=False.
- acceptance:
  - setup_directories() creates posts/ and images/ subdirs (skip in dry-run, propagate OSError)
  - **SPEC-REINFORCED**: write_post(slug, content) writes to `posts/{slug}.md` — caller must provide `{YYYY-MM-DD}-{slug}` format slug
  - write_post returns bool; OSError → False (logged), no exception propagation
  - write_metadata(result) writes metadata.json with ensure_ascii=False (Korean UTF-8)
  - Dry-run: all methods return True without writing
  - posts_dir, images_dir, output_dir exposed as public attributes
  - `uv run pytest tests/test_writer.py` passes
- tests: tests/test_writer.py — directory creation, post writing (content preservation, Korean), metadata JSON validity, dry-run behavior, error handling, all using tmp_path

## Item 9: CLI orchestration and integration
- status: DONE
- priority: P0
- complexity: M
- depends_on: [Item 1, Item 2, Item 3, Item 4, Item 5, Item 6, Item 7, Item 8]
- spec: specs/cli-interface.md
- clarity_ref: CLARITY_LOG.md#Round-1 (fallback chain conditional logic, blog without token, dry-run behavior, progress display ownership)
- description: Rewrite cli.py (currently stub) with _build_parser(), _validate_args(), _parse_date(), _extract_posts() (strategy fallback chain), _run() (main pipeline), _print_summary(), and main(). Strategy selection conditional on available inputs per CLARITY_LOG. Pipeline: extract → convert loop with progress → download images → write posts → write metadata.
- acceptance:
  - argparse with all 11 CLI arguments per spec
  - _validate_args: requires --blog or --backup
  - Strategy selection: --token → API; --backup → XML; --scrape or --blog-only → Scraper
  - Fallback chain: API→Scraper (no backup); API→XML→Scraper (backup available)
  - --blog without --token → default to scraping, log info message
  - **SPEC-REINFORCED**: _run() creates post filenames as `{YYYY-MM-DD}-{slug}.md` using published_at date
  - dry_run: extract+convert but no file writes, no image downloads
  - Progress display: `[N/M] Converting: title...`
  - Summary output matches spec format (blog, strategy, posts, categories, tags, images, duration)
  - Exit code: 0 success, 1 if failed_posts exist
  - Uses datetime.now(UTC) not deprecated utcnow()
  - `uv run pytest tests/test_cli.py` passes
- tests: tests/test_cli.py — arg parsing, validation, strategy selection, fallback chain, date parsing, pipeline integration, summary formatting, exit codes, dry-run behavior, all extractors/writer mocked

PHASE_1_COMPLETE
