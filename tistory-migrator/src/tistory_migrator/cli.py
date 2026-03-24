from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from tistory_migrator.converter import convert_post, generate_slug
from tistory_migrator.extractor import (
    ApiAuthError,
    TistoryApiExtractor,
    TistoryBackupExtractor,
    TistoryScraperExtractor,
)
from tistory_migrator.extractor.backup import BackupFileNotFoundError, BackupParseError
from tistory_migrator.extractor.scraper import ScraperBlockedError
from tistory_migrator.image_downloader import ImageDownloader
from tistory_migrator.models import FailedPost, MigrationResult, TistoryPost
from tistory_migrator.writer import Writer

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tistory-migrate",
        description="Migrate Tistory blog posts to Markdown files.",
    )
    parser.add_argument("--blog", help="Tistory blog name (e.g. myblog)")
    parser.add_argument("--token", help="Tistory API access token")
    parser.add_argument("--backup", help="Path to Tistory backup XML file")
    parser.add_argument("--scrape", action="store_true", help="Force scraping mode")
    parser.add_argument("--output", default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--category", help="Filter by category name")
    parser.add_argument("--after", help="Include posts on or after YYYY-MM-DD")
    parser.add_argument("--before", help="Include posts on or before YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Extract and convert without writing files")
    parser.add_argument("--no-images", action="store_true", help="Skip image downloads")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser


def _validate_args(args: argparse.Namespace) -> None:
    """Exit with error if required args are missing."""
    if not args.blog and not args.backup:
        print("error: at least one of --blog or --backup is required", file=sys.stderr)
        sys.exit(1)


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string to a UTC-aware datetime at midnight."""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _extract_posts(args: argparse.Namespace) -> tuple[list[TistoryPost], str]:
    """Run strategy selection and fallback chain. Returns (posts, strategy_name)."""
    after = _parse_date(args.after) if args.after else None
    before = _parse_date(args.before) if args.before else None
    category = args.category

    use_api = bool(args.token)
    use_xml = bool(args.backup)
    # --scrape flag, or --blog provided without --token and without --backup → scrape
    use_scraper_first = args.scrape or (bool(args.blog) and not args.token and not args.backup)

    if use_scraper_first:
        if not args.blog:
            logger.error("Scraping mode requires --blog")
            return [], "scraper"
        logging.info("No access token provided, using web scraping mode.")
        scraper = TistoryScraperExtractor(blog=args.blog)
        try:
            return scraper.extract(category=category, after=after, before=before), "scraper"
        except ScraperBlockedError as e:
            return e.partial_posts, "scraper"

    if use_api:
        if not args.blog:
            logger.error("API mode (--token) requires --blog")
        else:
            extractor = TistoryApiExtractor(blog=args.blog, access_token=args.token)
            try:
                posts = extractor.extract(category=category, after=after, before=before)
                return posts, "api"
            except ApiAuthError:
                print(
                    "Warning: API authentication failed (token may be expired or API deprecated). "
                    "Falling back to next strategy.",
                    file=sys.stderr,
                )

        # API failed or no blog — try XML then scraper
        if use_xml:
            try:
                xml_extractor = TistoryBackupExtractor(backup_path=args.backup)
                posts = xml_extractor.extract(category=category, after=after, before=before)
                return posts, "xml"
            except (BackupFileNotFoundError, BackupParseError) as e:
                print(f"Warning: XML backup failed: {e}. Falling back to scraper.", file=sys.stderr)

        if args.blog:
            scraper = TistoryScraperExtractor(blog=args.blog)
            try:
                return scraper.extract(category=category, after=after, before=before), "scraper"
            except ScraperBlockedError as e:
                return e.partial_posts, "scraper"

        return [], "api"

    if use_xml:
        xml_extractor = TistoryBackupExtractor(backup_path=args.backup)
        posts = xml_extractor.extract(category=category, after=after, before=before)
        return posts, "xml"

    # Should not reach here after _validate_args
    return [], "none"


def _format_duration(seconds: float) -> str:
    if seconds >= 60:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    return f"{seconds:.1f}s"


def _print_summary(result: MigrationResult, output_dir: str) -> None:
    downloaded = result.total_images - result.failed_images
    print("\n=== Tistory Migration Complete ===")
    print(f"  Blog:       {result.blog}")
    print(f"  Strategy:   {result.strategy}")
    print(
        f"  Posts:      {result.total_posts} extracted, "
        f"{result.converted_posts} converted, "
        f"{len(result.failed_posts)} failed"
    )
    print(f"  Categories: {len(result.categories)}")
    print(f"  Tags:       {len(result.tags)} unique")
    print(f"  Images:     {downloaded} downloaded, {result.failed_images} failed")
    print(f"  Output:     {output_dir}")
    print(f"  Duration:   {_format_duration(result.duration_seconds)}")

    if result.failed_posts:
        print("\n  Failed posts:")
        for fp in result.failed_posts:
            print(f"    - [#{fp.id}] {fp.title} (reason: {fp.reason})")


def _run(args: argparse.Namespace) -> int:
    """Main migration pipeline. Returns exit code (0=success, 1=failures)."""
    start_time = time.monotonic()

    if args.blog:
        blog_label = args.blog
    elif args.backup:
        blog_label = Path(args.backup).stem
    else:
        blog_label = "unknown"

    writer = Writer(output_dir=args.output, dry_run=args.dry_run)
    if not args.dry_run:
        writer.setup_directories()

    image_downloader = ImageDownloader(
        output_dir=Path(args.output),
        no_images=args.no_images or args.dry_run,
    )

    posts, strategy = _extract_posts(args)
    total_posts = len(posts)

    failed_posts: list[FailedPost] = []
    converted_posts = 0
    total_images = 0
    failed_images = 0
    all_categories: set[str] = set()
    all_tags: set[str] = set()

    for i, post in enumerate(posts, 1):
        print(f"[{i}/{total_posts}] Converting: {post.title}...")

        if not post.content_html.strip():
            failed_posts.append(FailedPost(id=post.id, title=post.title, reason="empty content"))
            continue

        if post.category:
            all_categories.add(post.category)
        all_tags.update(post.tags)

        try:
            markdown = convert_post(post)
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to convert post %s: %s", post.id, e)
            failed_posts.append(FailedPost(id=post.id, title=post.title, reason=f"conversion error: {e}"))
            continue

        slug = generate_slug(post.title)

        if post.images:
            dl_result = image_downloader.download_for_post(urls=post.images, slug=slug)
            total_images += dl_result.total
            failed_images += dl_result.failed

        date_prefix = post.published_at.strftime("%Y-%m-%d")
        filename_slug = f"{date_prefix}-{slug}"

        written = writer.write_post(slug=filename_slug, content=markdown)
        if not written:
            failed_posts.append(FailedPost(id=post.id, title=post.title, reason="write error"))
            continue

        converted_posts += 1

    duration = time.monotonic() - start_time

    result = MigrationResult(
        blog=blog_label,
        strategy=strategy,
        migrated_at=datetime.now(timezone.utc),
        total_posts=total_posts,
        converted_posts=converted_posts,
        failed_posts=failed_posts,
        categories=sorted(all_categories),
        tags=sorted(all_tags),
        total_images=total_images,
        failed_images=failed_images,
        duration_seconds=duration,
    )

    writer.write_metadata(result)
    _print_summary(result, args.output)

    return 1 if failed_posts else 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    _validate_args(args)
    exit_code = _run(args)
    sys.exit(exit_code)
