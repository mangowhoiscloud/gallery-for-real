from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from tistory_migrator.extractor.base import BaseExtractor
from tistory_migrator.models import TistoryPost

logger = logging.getLogger(__name__)


class BackupFileNotFoundError(Exception):
    """Raised when the backup XML file does not exist or cannot be read."""


class BackupParseError(Exception):
    """Raised when the backup XML file is malformed and cannot be parsed."""


class TistoryBackupExtractor(BaseExtractor):
    def __init__(self, backup_path: str) -> None:
        self._backup_path = Path(backup_path)

    @property
    def name(self) -> str:
        return "xml"

    def _parse_xml_string(self, xml_string: str) -> ET.Element:
        """Parse XML string to Element. Raises BackupParseError on malformed XML."""
        try:
            return ET.fromstring(xml_string)
        except ET.ParseError as e:
            raise BackupParseError(f"Failed to parse XML: {e}") from e

    def _load_xml(self) -> ET.Element:
        """Load and parse XML from the backup file."""
        if not self._backup_path.exists():
            raise BackupFileNotFoundError(
                f"Backup file not found: {self._backup_path}"
            )
        try:
            xml_string = self._backup_path.read_text(encoding="utf-8")
        except OSError as e:
            raise BackupFileNotFoundError(
                f"Cannot read backup file: {self._backup_path}"
            ) from e
        return self._parse_xml_string(xml_string)

    @staticmethod
    def _parse_published(text: str | None) -> datetime:
        """Parse published date. Supports ISO 8601, space-separated, and date-only.

        Raises ValueError if the date cannot be parsed. Never returns datetime.min.
        """
        if not text:
            raise ValueError("Empty published date")

        # fromisoformat handles: ISO with T (±timezone), space-separated, date-only
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass

        # Extra fallback for non-standard space-separated format
        try:
            return datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        raise ValueError(f"Cannot parse date: {text!r}")

    @staticmethod
    def _extract_images(html: str) -> list[str]:
        return re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)

    def _parse_post_element(self, elem: ET.Element) -> TistoryPost | None:
        """Parse a <post> element into TistoryPost. Returns None if content is empty
        or the published date cannot be parsed."""
        # ID: attribute first, then child element
        post_id = elem.get("id") or ""
        if not post_id:
            id_elem = elem.find("id")
            post_id = (id_elem.text or "").strip() if id_elem is not None else ""

        title_elem = elem.find("title")
        title = (title_elem.text or "").strip() if title_elem is not None else ""
        if not title:
            title = f"untitled-{post_id}"

        content_elem = elem.find("content")
        content_html = (
            (content_elem.text or "").strip() if content_elem is not None else ""
        )
        if not content_html:
            logger.warning("Skipping post %s: empty content", post_id)
            return None

        category_elem = elem.find("category")
        category = (
            (category_elem.text or "").strip() if category_elem is not None else ""
        )

        tags_elem = elem.find("tags")
        tag_list: list[str] = []
        if tags_elem is not None:
            for tag_elem in tags_elem.findall("tag"):
                tag_text = (tag_elem.text or "").strip()
                if tag_text:
                    tag_list.append(tag_text)

        published_elem = elem.find("published")
        published_text = (
            (published_elem.text or "").strip() if published_elem is not None else ""
        )
        try:
            published_at = self._parse_published(published_text)
        except ValueError:
            logger.warning(
                "Skipping post %s: cannot parse date %r", post_id, published_text
            )
            return None

        url_elem = elem.find("url")
        url = (url_elem.text or "").strip() if url_elem is not None else ""

        images = self._extract_images(content_html)

        return TistoryPost(
            id=post_id,
            title=title,
            content_html=content_html,
            category=category,
            tags=tag_list,
            published_at=published_at,
            url=url,
            images=images,
        )

    def extract(
        self,
        category: str | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[TistoryPost]:
        """Extract posts from Tistory XML backup with optional filters."""
        root = self._load_xml()

        posts_elem = root.find(".//posts")
        if posts_elem is not None:
            post_elems = posts_elem.findall("post")
        else:
            post_elems = root.findall("post")

        posts: list[TistoryPost] = []
        for elem in post_elems:
            post = self._parse_post_element(elem)
            if post is None:
                continue

            if after is not None and post.published_at < after:
                continue
            if before is not None and post.published_at > before:
                continue
            if category is not None and post.category.lower() != category.lower():
                continue

            posts.append(post)

        return posts
