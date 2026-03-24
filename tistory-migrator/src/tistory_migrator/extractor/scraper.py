from __future__ import annotations

import logging
import re
import time
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from tistory_migrator.extractor.base import BaseExtractor
from tistory_migrator.models import TistoryPost

logger = logging.getLogger(__name__)

_CONTENT_SELECTORS = [
    ".entry-content",
    "article .post-content",
    "article",
    ".post-content",
    "#content .post",
]


class ScraperBlockedError(Exception):
    """Raised when a 403 is encountered during scraping.

    partial_posts contains any posts successfully extracted before the block.
    """

    def __init__(self, message: str, partial_posts: list[TistoryPost]) -> None:
        super().__init__(message)
        self.partial_posts = partial_posts


class TistoryScraperExtractor(BaseExtractor):
    def __init__(
        self,
        blog: str,
        rate_limit_sleep: float = 2.0,
    ) -> None:
        self._blog = blog
        self._rate_limit_sleep = rate_limit_sleep
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return "scraper"

    def _get(self, url: str) -> requests.Response:
        """GET a URL with rate limiting (sleeps before request)."""
        time.sleep(self._rate_limit_sleep)
        return self._session.get(url, timeout=30)

    def _load_robots(self) -> urllib.robotparser.RobotFileParser:
        """Load robots.txt via session.get (no rate limit sleep).

        On any failure or non-200, sets allow_all=True explicitly.
        Python 3.14 changed RobotFileParser default to deny-all, so
        we must set allow_all=True when robots.txt is unavailable.
        """
        rp = urllib.robotparser.RobotFileParser()
        robots_url = f"https://{self._blog}.tistory.com/robots.txt"
        try:
            resp = self._session.get(robots_url, timeout=10)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                return rp
        except Exception:  # noqa: BLE001
            pass
        rp.allow_all = True
        return rp

    @staticmethod
    def _strip_xml_namespaces(xml_text: str) -> str:
        """Remove xmlns declarations so ET can parse without namespace prefixes."""
        return re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", xml_text)

    def _discover_urls_from_sitemap(self) -> list[str] | None:
        """Try sitemap.xml for post URLs.

        Returns list of /entry/ URLs if found, None if sitemap is
        unavailable or has no post URLs. Raises ScraperBlockedError on 403.
        """
        base = f"https://{self._blog}.tistory.com"
        try:
            resp = self._get(f"{base}/sitemap.xml")
        except Exception as e:
            logger.debug("Sitemap request failed: %s", e)
            return None

        if resp.status_code == 403:
            raise ScraperBlockedError("Blocked (403) on sitemap.xml", partial_posts=[])
        if resp.status_code != 200:
            return None

        xml_stripped = self._strip_xml_namespaces(resp.text)
        try:
            root = ET.fromstring(xml_stripped)
        except ET.ParseError:
            return None

        urls = [
            (loc.text or "").strip()
            for loc in root.iter("loc")
            if "/entry/" in (loc.text or "")
        ]
        return urls if urls else None

    def _discover_urls_from_archive(self) -> list[str]:
        """Try the blog's category/archive page for post URLs.

        Returns list of /entry/ URLs (deduplicated). Raises ScraperBlockedError on 403.
        """
        base = f"https://{self._blog}.tistory.com"
        try:
            resp = self._get(f"{base}/category")
        except Exception as e:
            logger.debug("Archive request failed: %s", e)
            return []

        if resp.status_code == 403:
            raise ScraperBlockedError("Blocked (403) on archive page", partial_posts=[])
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        seen: set[str] = set()
        urls: list[str] = []
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if "/entry/" in href:
                full_url = href if href.startswith("http") else base + href
                if full_url not in seen:
                    seen.add(full_url)
                    urls.append(full_url)
        return urls

    def _discover_urls(self) -> list[str]:
        """Discover all post URLs: sitemap first, archive fallback.

        Discovery-level 403s are caught and trigger the next strategy.
        """
        try:
            sitemap_urls = self._discover_urls_from_sitemap()
            if sitemap_urls is not None:
                return sitemap_urls
        except ScraperBlockedError:
            logger.debug("Blocked on sitemap.xml, trying archive page")

        try:
            return self._discover_urls_from_archive()
        except ScraperBlockedError:
            logger.debug("Blocked on archive page, no URLs discovered")
            return []

    def _parse_post_page(self, url: str) -> TistoryPost:
        """Fetch and parse a single post page into TistoryPost."""
        resp = self._get(url)
        if resp.status_code == 403:
            raise ScraperBlockedError(
                f"Blocked (403) fetching post: {url}", partial_posts=[]
            )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Title: og:title meta → h1 fallback
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = str(og_title["content"])
        else:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else "untitled"

        # Published: meta article:published_time → time[datetime] → datetime.min
        published_at: datetime
        pub_meta = soup.find("meta", property="article:published_time")
        if pub_meta and pub_meta.get("content"):
            try:
                published_at = datetime.fromisoformat(str(pub_meta["content"]))
            except ValueError:
                published_at = datetime.min
        else:
            time_tag = soup.find("time", attrs={"datetime": True})
            if time_tag:
                try:
                    published_at = datetime.fromisoformat(str(time_tag["datetime"]))
                except ValueError:
                    published_at = datetime.min
            else:
                published_at = datetime.min

        # Category: .category a → .link_cate fallback
        cat_elem = soup.select_one(".category a") or soup.select_one(".link_cate")
        category = cat_elem.get_text(strip=True) if cat_elem else ""

        # Tags: .tag a → .link_tag fallback
        tag_elems = soup.select(".tag a") or soup.select(".link_tag")
        tags = [t.get_text(strip=True) for t in tag_elems if t.get_text(strip=True)]

        # Content: selector cascade
        content_el = None
        for selector in _CONTENT_SELECTORS:
            content_el = soup.select_one(selector)
            if content_el:
                break
        content_html = str(content_el) if content_el else ""

        images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)

        # ID from last URL path segment
        post_id = url.rstrip("/").rsplit("/", 1)[-1]

        return TistoryPost(
            id=post_id,
            title=title,
            content_html=content_html,
            category=category,
            tags=tags,
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
        """Extract posts by scraping, with optional filters."""
        rp = self._load_robots()
        urls = self._discover_urls()

        posts: list[TistoryPost] = []
        for url in urls:
            if not rp.can_fetch("*", url):
                logger.debug("robots.txt disallows: %s", url)
                continue

            try:
                post = self._parse_post_page(url)
            except ScraperBlockedError as e:
                raise ScraperBlockedError(e.args[0], partial_posts=posts)
            except Exception:  # noqa: BLE001
                logger.warning("Skipping post %s due to error", url)
                continue

            if after is not None and post.published_at < after:
                continue
            if before is not None and post.published_at > before:
                continue
            if category is not None and post.category.lower() != category.lower():
                continue

            posts.append(post)

        return posts
