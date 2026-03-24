"""Tests for cli.py — arg parsing, validation, strategy selection, pipeline, summary."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tistory_migrator.cli import (
    _build_parser,
    _extract_posts,
    _format_duration,
    _parse_date,
    _print_summary,
    _run,
    _validate_args,
    main,
)
from tistory_migrator.models import FailedPost, MigrationResult, TistoryPost


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_post(
    id: str = "1",
    title: str = "Test Post",
    content_html: str = "<p>Hello</p>",
    category: str = "Tech",
    tags: list[str] | None = None,
    published_at: datetime | None = None,
    url: str = "https://blog.tistory.com/1",
    images: list[str] | None = None,
) -> TistoryPost:
    return TistoryPost(
        id=id,
        title=title,
        content_html=content_html,
        category=category,
        tags=tags or ["python"],
        published_at=published_at or datetime(2024, 1, 15, tzinfo=timezone.utc),
        url=url,
        images=images or [],
    )


def _make_result(**kwargs) -> MigrationResult:
    defaults = dict(
        blog="myblog",
        strategy="api",
        migrated_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        total_posts=10,
        converted_posts=9,
        failed_posts=[],
        categories=["Tech", "Life"],
        tags=["python", "django"],
        total_images=5,
        failed_images=1,
        duration_seconds=45.5,
    )
    defaults.update(kwargs)
    return MigrationResult(**defaults)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_all_args_present(self):
        parser = _build_parser()
        args = parser.parse_args([
            "--blog", "myblog",
            "--token", "tok123",
            "--backup", "backup.xml",
            "--scrape",
            "--output", "./out",
            "--category", "Tech",
            "--after", "2024-01-01",
            "--before", "2024-12-31",
            "--dry-run",
            "--no-images",
            "--verbose",
        ])
        assert args.blog == "myblog"
        assert args.token == "tok123"
        assert args.backup == "backup.xml"
        assert args.scrape is True
        assert args.output == "./out"
        assert args.category == "Tech"
        assert args.after == "2024-01-01"
        assert args.before == "2024-12-31"
        assert args.dry_run is True
        assert args.no_images is True
        assert args.verbose is True

    def test_defaults(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog"])
        assert args.token is None
        assert args.backup is None
        assert args.scrape is False
        assert args.output == "./output"
        assert args.category is None
        assert args.after is None
        assert args.before is None
        assert args.dry_run is False
        assert args.no_images is False
        assert args.verbose is False

    def test_blog_only(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog"])
        assert args.blog == "myblog"

    def test_backup_only(self):
        parser = _build_parser()
        args = parser.parse_args(["--backup", "file.xml"])
        assert args.backup == "file.xml"
        assert args.blog is None

    def test_scrape_is_store_true(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog", "--scrape"])
        assert args.scrape is True

    def test_dry_run_is_store_true(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog", "--dry-run"])
        assert args.dry_run is True

    def test_no_images_is_store_true(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog", "--no-images"])
        assert args.no_images is True

    def test_verbose_is_store_true(self):
        parser = _build_parser()
        args = parser.parse_args(["--blog", "myblog", "--verbose"])
        assert args.verbose is True


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateArgs:
    def _args(self, blog=None, backup=None):
        parser = _build_parser()
        argv = []
        if blog:
            argv += ["--blog", blog]
        if backup:
            argv += ["--backup", backup]
        return parser.parse_args(argv)

    def test_no_blog_no_backup_exits(self):
        parser = _build_parser()
        args = parser.parse_args([])
        with pytest.raises(SystemExit) as exc_info:
            _validate_args(args)
        assert exc_info.value.code == 1

    def test_blog_passes(self):
        args = self._args(blog="myblog")
        _validate_args(args)  # should not raise

    def test_backup_passes(self):
        args = self._args(backup="backup.xml")
        _validate_args(args)  # should not raise

    def test_both_passes(self):
        args = self._args(blog="myblog", backup="backup.xml")
        _validate_args(args)  # should not raise

    def test_error_message_printed(self, capsys):
        parser = _build_parser()
        args = parser.parse_args([])
        with pytest.raises(SystemExit):
            _validate_args(args)
        captured = capsys.readouterr()
        assert "required" in captured.err


# ---------------------------------------------------------------------------
# Date parsing tests
# ---------------------------------------------------------------------------

class TestParseDate:
    def test_valid_date(self):
        dt = _parse_date("2024-03-15")
        assert dt == datetime(2024, 3, 15, tzinfo=timezone.utc)

    def test_timezone_is_utc(self):
        dt = _parse_date("2023-01-01")
        assert dt.tzinfo == timezone.utc

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            _parse_date("15-03-2024")

    def test_invalid_date_raises(self):
        with pytest.raises(ValueError):
            _parse_date("2024-13-01")


# ---------------------------------------------------------------------------
# Duration formatting tests
# ---------------------------------------------------------------------------

class TestFormatDuration:
    def test_under_60_seconds(self):
        assert _format_duration(45.5) == "45.5s"

    def test_exactly_60_seconds(self):
        assert _format_duration(60.0) == "1m 0s"

    def test_over_60_seconds(self):
        assert _format_duration(154.0) == "2m 34s"

    def test_zero_seconds(self):
        assert _format_duration(0.0) == "0.0s"

    def test_small_seconds(self):
        assert _format_duration(3.2) == "3.2s"


# ---------------------------------------------------------------------------
# Strategy selection / _extract_posts tests
# ---------------------------------------------------------------------------

class TestExtractPosts:
    def _args(self, **kwargs):
        defaults = dict(blog=None, token=None, backup=None, scrape=False,
                        category=None, after=None, before=None)
        defaults.update(kwargs)
        ns = MagicMock()
        for k, v in defaults.items():
            setattr(ns, k, v)
        return ns

    def test_api_strategy_used_when_token_given(self):
        args = self._args(blog="myblog", token="tok")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryApiExtractor") as MockAPI:
            MockAPI.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "api"
        assert posts == [post]
        MockAPI.assert_called_once_with(blog="myblog", access_token="tok")

    def test_xml_strategy_used_when_backup_only(self):
        args = self._args(backup="file.xml")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryBackupExtractor") as MockXML:
            MockXML.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "xml"
        assert posts == [post]
        MockXML.assert_called_once_with(backup_path="file.xml")

    def test_scraper_used_when_scrape_flag(self):
        args = self._args(blog="myblog", scrape=True)
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryScraperExtractor") as MockScraper:
            MockScraper.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "scraper"
        assert posts == [post]

    def test_scraper_used_when_blog_without_token(self):
        args = self._args(blog="myblog")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryScraperExtractor") as MockScraper:
            MockScraper.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "scraper"

    def test_api_falls_back_to_scraper_on_auth_error(self):
        args = self._args(blog="myblog", token="tok")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryApiExtractor") as MockAPI, \
             patch("tistory_migrator.cli.TistoryScraperExtractor") as MockScraper:
            from tistory_migrator.extractor import ApiAuthError
            MockAPI.return_value.extract.side_effect = ApiAuthError("auth failed")
            MockScraper.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "scraper"
        assert posts == [post]

    def test_api_falls_back_to_xml_then_scraper_on_auth_error(self):
        args = self._args(blog="myblog", token="tok", backup="file.xml")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryApiExtractor") as MockAPI, \
             patch("tistory_migrator.cli.TistoryBackupExtractor") as MockXML, \
             patch("tistory_migrator.cli.TistoryScraperExtractor"):
            from tistory_migrator.extractor import ApiAuthError
            MockAPI.return_value.extract.side_effect = ApiAuthError("auth failed")
            MockXML.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "xml"
        assert posts == [post]

    def test_fallback_xml_then_scraper_when_xml_also_fails(self):
        args = self._args(blog="myblog", token="tok", backup="file.xml")
        post = _make_post()
        with patch("tistory_migrator.cli.TistoryApiExtractor") as MockAPI, \
             patch("tistory_migrator.cli.TistoryBackupExtractor") as MockXML, \
             patch("tistory_migrator.cli.TistoryScraperExtractor") as MockScraper:
            from tistory_migrator.extractor import ApiAuthError
            from tistory_migrator.extractor.backup import BackupParseError
            MockAPI.return_value.extract.side_effect = ApiAuthError("auth failed")
            MockXML.return_value.extract.side_effect = BackupParseError("bad xml")
            MockScraper.return_value.extract.return_value = [post]
            posts, strategy = _extract_posts(args)
        assert strategy == "scraper"
        assert posts == [post]

    def test_scraper_blocked_returns_partial_posts(self):
        args = self._args(blog="myblog", scrape=True)
        partial = [_make_post()]
        with patch("tistory_migrator.cli.TistoryScraperExtractor") as MockScraper:
            from tistory_migrator.extractor.scraper import ScraperBlockedError
            MockScraper.return_value.extract.side_effect = ScraperBlockedError("blocked", partial)
            posts, strategy = _extract_posts(args)
        assert strategy == "scraper"
        assert posts == partial

    def test_filters_passed_to_extractor(self):
        args = self._args(blog="myblog", token="tok",
                          category="Tech", after="2024-01-01", before="2024-12-31")
        with patch("tistory_migrator.cli.TistoryApiExtractor") as MockAPI:
            MockAPI.return_value.extract.return_value = []
            _extract_posts(args)
        call_kwargs = MockAPI.return_value.extract.call_args[1]
        assert call_kwargs["category"] == "Tech"
        assert call_kwargs["after"] == _parse_date("2024-01-01")
        assert call_kwargs["before"] == _parse_date("2024-12-31")

    def test_no_blog_scrape_flag_returns_empty(self):
        args = self._args(scrape=True, blog=None)
        posts, strategy = _extract_posts(args)
        assert posts == []
        assert strategy == "scraper"


# ---------------------------------------------------------------------------
# _run pipeline tests
# ---------------------------------------------------------------------------

class TestRun:
    def _make_args(self, **kwargs):
        defaults = dict(
            blog="myblog", token=None, backup=None, scrape=False,
            output="./output", category=None, after=None, before=None,
            dry_run=False, no_images=False, verbose=False,
        )
        defaults.update(kwargs)
        ns = MagicMock()
        for k, v in defaults.items():
            setattr(ns, k, v)
        return ns

    def _patch_all(self, posts=None, markdown="# Hello", slug="test-post",
                   write_post_result=True, img_total=0, img_failed=0):
        """Return a context manager that patches all I/O for _run."""
        if posts is None:
            posts = [_make_post()]
        patches = {
            "_extract_posts": patch("tistory_migrator.cli._extract_posts", return_value=(posts, "api")),
            "convert_post": patch("tistory_migrator.cli.convert_post", return_value=markdown),
            "generate_slug": patch("tistory_migrator.cli.generate_slug", return_value=slug),
            "Writer": patch("tistory_migrator.cli.Writer"),
            "ImageDownloader": patch("tistory_migrator.cli.ImageDownloader"),
            "time_mono": patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 5.0]),
        }
        return patches

    def test_returns_0_on_success(self):
        args = self._make_args()
        post = _make_post()
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="test-post"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 5.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            code = _run(args)
        assert code == 0

    def test_returns_1_when_failed_posts(self):
        args = self._make_args()
        post = _make_post(content_html="")  # empty content → failure
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 5.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            code = _run(args)
        assert code == 1

    def test_filename_uses_date_prefix_and_slug(self):
        args = self._make_args()
        post = _make_post(published_at=datetime(2024, 3, 15, tzinfo=timezone.utc))
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="my-slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 5.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        call_args = MockWriter.return_value.write_post.call_args
        assert call_args[1]["slug"] == "2024-03-15-my-slug"

    def test_empty_content_creates_failed_post(self):
        args = self._make_args()
        post = _make_post(content_html="   ")
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert len(result.failed_posts) == 1
        assert result.failed_posts[0].reason == "empty content"

    def test_write_failure_creates_failed_post(self):
        args = self._make_args()
        post = _make_post()
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_post.return_value = False
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert len(result.failed_posts) == 1
        assert result.failed_posts[0].reason == "write error"

    def test_conversion_error_creates_failed_post(self):
        args = self._make_args()
        post = _make_post()
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", side_effect=RuntimeError("bad")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert len(result.failed_posts) == 1
        assert "conversion error" in result.failed_posts[0].reason

    def test_dry_run_does_not_setup_directories(self):
        args = self._make_args(dry_run=True)
        post = _make_post()
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        MockWriter.return_value.setup_directories.assert_not_called()

    def test_dry_run_writer_created_with_dry_run_true(self):
        args = self._make_args(dry_run=True)
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        MockWriter.assert_called_once_with(output_dir="./output", dry_run=True)

    def test_images_downloaded_for_post_with_images(self):
        args = self._make_args()
        post = _make_post(images=["https://example.com/img.jpg"])
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader") as MockDL, \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            dl_result = MagicMock(total=1, succeeded=1, failed=0)
            MockDL.return_value.download_for_post.return_value = dl_result
            _run(args)
        MockDL.return_value.download_for_post.assert_called_once_with(
            urls=["https://example.com/img.jpg"], slug="slug"
        )

    def test_no_images_flag_passed_to_downloader(self):
        args = self._make_args(no_images=True)
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader") as MockDL, \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        call_kwargs = MockDL.call_args[1]
        assert call_kwargs["no_images"] is True

    def test_dry_run_disables_image_downloads(self):
        args = self._make_args(dry_run=True, no_images=False)
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader") as MockDL, \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        call_kwargs = MockDL.call_args[1]
        assert call_kwargs["no_images"] is True

    def test_categories_and_tags_accumulated(self):
        args = self._make_args()
        posts = [
            _make_post(id="1", category="Tech", tags=["python", "django"]),
            _make_post(id="2", category="Life", tags=["travel"]),
        ]
        with patch("tistory_migrator.cli._extract_posts", return_value=(posts, "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 2.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert sorted(result.categories) == ["Life", "Tech"]
        assert sorted(result.tags) == ["django", "python", "travel"]

    def test_blog_label_from_blog_arg(self):
        args = self._make_args(blog="myblog", backup=None)
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "api")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert result.blog == "myblog"

    def test_blog_label_from_backup_stem(self):
        args = self._make_args(blog=None, backup="/path/to/myblog-backup.xml")
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "xml")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert result.blog == "myblog-backup"

    def test_progress_printed(self, capsys):
        args = self._make_args()
        post = _make_post(title="My Post")
        with patch("tistory_migrator.cli._extract_posts", return_value=([post], "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
        captured = capsys.readouterr()
        assert "[1/1] Converting: My Post..." in captured.out

    def test_result_strategy_matches_extracted_strategy(self):
        args = self._make_args()
        with patch("tistory_migrator.cli._extract_posts", return_value=([], "xml")), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 1.0]):
            MockWriter.return_value.write_metadata.return_value = True
            _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert result.strategy == "xml"

    def test_multiple_posts_all_converted(self):
        args = self._make_args()
        posts = [_make_post(id=str(i), title=f"Post {i}") for i in range(3)]
        with patch("tistory_migrator.cli._extract_posts", return_value=(posts, "api")), \
             patch("tistory_migrator.cli.convert_post", return_value="# md"), \
             patch("tistory_migrator.cli.generate_slug", return_value="slug"), \
             patch("tistory_migrator.cli.Writer") as MockWriter, \
             patch("tistory_migrator.cli.ImageDownloader"), \
             patch("tistory_migrator.cli.time.monotonic", side_effect=[0.0, 3.0]):
            MockWriter.return_value.write_post.return_value = True
            MockWriter.return_value.write_metadata.return_value = True
            code = _run(args)
            result = MockWriter.return_value.write_metadata.call_args[0][0]
        assert code == 0
        assert result.total_posts == 3
        assert result.converted_posts == 3


# ---------------------------------------------------------------------------
# _print_summary tests
# ---------------------------------------------------------------------------

class TestPrintSummary:
    def test_basic_output(self, capsys):
        result = _make_result()
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "=== Tistory Migration Complete ===" in captured.out
        assert "myblog" in captured.out
        assert "api" in captured.out

    def test_posts_line(self, capsys):
        result = _make_result(total_posts=10, converted_posts=9,
                              failed_posts=[FailedPost(id="1", title="x", reason="r")])
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "10 extracted" in captured.out
        assert "9 converted" in captured.out
        assert "1 failed" in captured.out

    def test_images_line(self, capsys):
        result = _make_result(total_images=10, failed_images=2)
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "8 downloaded" in captured.out
        assert "2 failed" in captured.out

    def test_categories_count(self, capsys):
        result = _make_result(categories=["A", "B", "C"])
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "3" in captured.out

    def test_tags_count(self, capsys):
        result = _make_result(tags=["x", "y"])
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "2 unique" in captured.out

    def test_failed_posts_section_shown(self, capsys):
        result = _make_result(
            failed_posts=[FailedPost(id="42", title="Bad Post", reason="empty content")]
        )
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "Failed posts:" in captured.out
        assert "[#42]" in captured.out
        assert "Bad Post" in captured.out
        assert "empty content" in captured.out

    def test_no_failed_posts_section_when_empty(self, capsys):
        result = _make_result(failed_posts=[])
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "Failed posts:" not in captured.out

    def test_duration_over_minute(self, capsys):
        result = _make_result(duration_seconds=154.0)
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "2m 34s" in captured.out

    def test_duration_under_minute(self, capsys):
        result = _make_result(duration_seconds=45.5)
        _print_summary(result, "./output")
        captured = capsys.readouterr()
        assert "45.5s" in captured.out

    def test_output_dir_shown(self, capsys):
        result = _make_result()
        _print_summary(result, "/custom/path")
        captured = capsys.readouterr()
        assert "/custom/path" in captured.out


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

class TestMain:
    def test_main_exits_0_on_success(self):
        with patch("sys.argv", ["tistory-migrate", "--blog", "myblog"]), \
             patch("tistory_migrator.cli._run", return_value=0), \
             pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_main_exits_1_on_failure(self):
        with patch("sys.argv", ["tistory-migrate", "--blog", "myblog"]), \
             patch("tistory_migrator.cli._run", return_value=1), \
             pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_exits_1_no_blog_no_backup(self):
        with patch("sys.argv", ["tistory-migrate"]), \
             pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_verbose_sets_debug_logging(self):
        with patch("sys.argv", ["tistory-migrate", "--blog", "myblog", "--verbose"]), \
             patch("tistory_migrator.cli._run", return_value=0), \
             patch("tistory_migrator.cli.logging.basicConfig") as mock_log, \
             pytest.raises(SystemExit):
            main()
        import logging
        mock_log.assert_called_with(level=logging.DEBUG)

    def test_main_default_logging_is_warning(self):
        with patch("sys.argv", ["tistory-migrate", "--blog", "myblog"]), \
             patch("tistory_migrator.cli._run", return_value=0), \
             patch("tistory_migrator.cli.logging.basicConfig") as mock_log, \
             pytest.raises(SystemExit):
            main()
        import logging
        mock_log.assert_called_with(level=logging.WARNING)
