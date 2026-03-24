"""Image downloader for Tistory posts.

Downloads images referenced in a post to a local directory, with:
- Filename collision resolution (-1, -2 suffixes)
- Permanent failure detection (404/410 — no retry)
- Exponential backoff retries for 5xx and network errors
- Rate limiting between requests (not before the first)
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

_RETRY_DELAYS = [1, 2, 4]  # seconds — matches API extractor pattern
_PERMANENT_FAILURE_CODES = {404, 410}


def _url_to_filename(url: str) -> str:
    """Extract a filename from an image URL. Falls back to 'image.jpg'."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    return filename if filename else "image.jpg"


def _resolve_collision(base_path: Path, used_paths: set[Path]) -> Path:
    """Return base_path if unused, else append -1, -2, ... to the stem."""
    if base_path not in used_paths:
        return base_path
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent
    i = 1
    while True:
        candidate = parent / f"{stem}-{i}{suffix}"
        if candidate not in used_paths:
            return candidate
        i += 1


@dataclass
class ImageDownloadResult:
    """Result of downloading images for one post."""

    mapping: dict[str, str]  # original URL → relative local path (/images/{slug}/filename)
    total: int
    succeeded: int
    failed: int


class ImageDownloader:
    """Downloads images for Tistory posts to a local output directory."""

    def __init__(
        self,
        output_dir: Path,
        rate_limit_sleep: float = 0.5,
        no_images: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.rate_limit_sleep = rate_limit_sleep
        self.no_images = no_images
        self._session = session

    def _get_session(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def download_for_post(self, urls: list[str], slug: str) -> ImageDownloadResult:
        """Download all image URLs for a post to output_dir/images/{slug}/.

        Returns an ImageDownloadResult with mapping and statistics.
        """
        if self.no_images:
            total = len(urls)
            return ImageDownloadResult(mapping={}, total=total, succeeded=0, failed=total)

        if not urls:
            return ImageDownloadResult(mapping={}, total=0, succeeded=0, failed=0)

        images_dir = self.output_dir / "images" / slug
        images_dir.mkdir(parents=True, exist_ok=True)

        mapping: dict[str, str] = {}
        used_paths: set[Path] = set()
        succeeded = 0
        failed = 0
        first = True

        for url in urls:
            if not first:
                time.sleep(self.rate_limit_sleep)
            first = False

            local_path = self._download_one(url, images_dir, used_paths)
            if local_path is not None:
                used_paths.add(local_path)
                relative = f"/images/{slug}/{local_path.name}"
                mapping[url] = relative
                succeeded += 1
            else:
                failed += 1

        return ImageDownloadResult(
            mapping=mapping,
            total=len(urls),
            succeeded=succeeded,
            failed=failed,
        )

    def _download_one(
        self, url: str, images_dir: Path, used_paths: set[Path]
    ) -> Path | None:
        """Download one URL. Returns the saved Path, or None on failure."""
        filename = _url_to_filename(url)
        base_path = images_dir / filename
        dest_path = _resolve_collision(base_path, used_paths)

        session = self._get_session()

        for attempt in range(len(_RETRY_DELAYS) + 1):
            if attempt > 0:
                time.sleep(_RETRY_DELAYS[attempt - 1])
            try:
                resp = session.get(url, timeout=30)
            except (requests.Timeout, requests.ConnectionError) as exc:
                logger.warning("Network error downloading %s (attempt %d): %s", url, attempt + 1, exc)
                if attempt < len(_RETRY_DELAYS):
                    continue
                return None

            if resp.status_code == 200:
                dest_path.write_bytes(resp.content)
                logger.debug("Downloaded %s → %s", url, dest_path)
                return dest_path

            if resp.status_code in _PERMANENT_FAILURE_CODES:
                logger.warning("Permanent failure (%d) for %s — skipping", resp.status_code, url)
                return None

            # 5xx or other retryable error
            logger.warning(
                "HTTP %d for %s (attempt %d of %d)",
                resp.status_code,
                url,
                attempt + 1,
                len(_RETRY_DELAYS) + 1,
            )
            if attempt < len(_RETRY_DELAYS):
                continue
            return None

        return None  # unreachable but satisfies type checker
