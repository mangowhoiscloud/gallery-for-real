from __future__ import annotations

import re
import time
from datetime import datetime

import requests

from tistory_migrator.extractor.base import BaseExtractor
from tistory_migrator.models import TistoryPost

TISTORY_API_BASE = "https://www.tistory.com/apis"
_RETRY_DELAYS = [1, 2, 4]


class ApiAuthError(Exception):
    """Raised when API returns 401 — token expired/invalid. CLI should fallback."""


class ApiUnavailableError(Exception):
    """Raised when API fails after all retries. Individual posts are skipped."""


class TistoryApiExtractor(BaseExtractor):
    def __init__(
        self,
        blog: str,
        access_token: str,
        rate_limit_sleep: float = 1.0,
    ) -> None:
        self._blog = blog
        self._access_token = access_token
        self._rate_limit_sleep = rate_limit_sleep
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return "api"

    def _request(self, endpoint: str, params: dict) -> dict:
        """Make an API request with rate limiting and retry logic.

        Sleeps rate_limit_sleep before the first attempt, then _RETRY_DELAYS[i]
        before each subsequent retry.
        """
        url = f"{TISTORY_API_BASE}{endpoint}"
        full_params = {
            "access_token": self._access_token,
            "output": "json",
            **params,
        }

        for attempt in range(4):
            if attempt == 0:
                time.sleep(self._rate_limit_sleep)
            else:
                time.sleep(_RETRY_DELAYS[attempt - 1])

            try:
                resp = self._session.get(url, params=full_params, timeout=30)
            except requests.Timeout:
                if attempt == 3:
                    raise ApiUnavailableError(f"Timeout on {endpoint} after retries")
                continue
            except requests.ConnectionError:
                if attempt == 3:
                    raise ApiUnavailableError(
                        f"Connection error on {endpoint} after retries"
                    )
                continue

            if resp.status_code == 401:
                raise ApiAuthError("API authentication failed (HTTP 401)")

            if resp.status_code >= 500:
                if attempt == 3:
                    raise ApiUnavailableError(
                        f"Server error {resp.status_code} on {endpoint} after retries"
                    )
                continue

            resp.raise_for_status()

            data = resp.json()
            tistory = data.get("tistory", {})
            if str(tistory.get("status", "")) == "401":
                raise ApiAuthError("API authentication failed (status 401 in body)")

            return tistory

        raise ApiUnavailableError(f"Failed to fetch {endpoint}")

    def _get_category_map(self) -> dict[str, str]:
        """Fetch category id → name mapping. Returns empty dict on failure."""
        try:
            data = self._request("/category/list", {"blogName": self._blog})
        except ApiUnavailableError:
            return {}

        categories_data = (
            data.get("item", {}).get("categories", {}).get("category", [])
        )
        if isinstance(categories_data, dict):
            categories_data = [categories_data]

        return {
            str(cat["id"]): cat["name"]
            for cat in categories_data
            if "id" in cat and "name" in cat
        }

    @staticmethod
    def _extract_images(html: str) -> list[str]:
        """Extract image URLs from HTML content."""
        return re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)

    def _parse_post(self, item: dict, category_map: dict[str, str]) -> TistoryPost:
        """Parse a single post API response item into TistoryPost."""
        post_id = str(item.get("id", ""))
        title = item.get("title", "") or f"untitled-{post_id}"
        content_html = item.get("content", "") or ""

        category_id = str(item.get("categoryId", ""))
        category = category_map.get(category_id, "")

        tags_data = item.get("tags") or {}
        raw_tags = tags_data.get("tag", []) if isinstance(tags_data, dict) else []
        if isinstance(raw_tags, str):
            tag_list: list[str] = [raw_tags] if raw_tags else []
        else:
            tag_list = [t for t in raw_tags if t]

        date_str = item.get("date", "")
        try:
            published_at = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            try:
                published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                published_at = datetime.min

        url = item.get("postUrl", "") or item.get("url", "") or ""
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

    def _fetch_post_ids(self) -> list[str]:
        """Fetch all post IDs via pagination."""
        post_ids: list[str] = []
        page = 1
        while True:
            data = self._request(
                "/post/list", {"blogName": self._blog, "page": str(page)}
            )
            item = data.get("item", {})
            posts_data = item.get("posts", {})
            post_list = posts_data.get("post", [])
            if isinstance(post_list, dict):
                post_list = [post_list]
            if not post_list:
                break

            for p in post_list:
                post_ids.append(str(p.get("id", "")))

            count = int(item.get("count", len(post_list)))
            total_count = int(item.get("totalCount", 0))
            if total_count == 0 or page * count >= total_count:
                break
            page += 1

        return post_ids

    def extract(
        self,
        category: str | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
    ) -> list[TistoryPost]:
        """Extract posts from Tistory Open API with optional filters."""
        category_map = self._get_category_map()
        post_ids = self._fetch_post_ids()

        posts: list[TistoryPost] = []
        for post_id in post_ids:
            try:
                data = self._request(
                    "/post/read", {"blogName": self._blog, "postId": post_id}
                )
                post = self._parse_post(data.get("item", {}), category_map)
            except ApiAuthError:
                raise
            except Exception:  # noqa: BLE001 — one post failure should not stop migration
                continue

            if after is not None and post.published_at < after:
                continue
            if before is not None and post.published_at > before:
                continue
            if category is not None and post.category.lower() != category.lower():
                continue

            posts.append(post)

        return posts
