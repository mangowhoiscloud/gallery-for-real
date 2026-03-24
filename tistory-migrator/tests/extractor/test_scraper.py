"""Tests for TistoryScraperExtractor."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from tistory_migrator.extractor import (
    ScraperBlockedError,
    TistoryScraperExtractor,
)
from tistory_migrator.models import TistoryPost

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BLOG = "myblog"
BASE = f"https://{BLOG}.tistory.com"


def make_extractor(rate_limit_sleep: float = 0.0) -> TistoryScraperExtractor:
    return TistoryScraperExtractor(blog=BLOG, rate_limit_sleep=rate_limit_sleep)


def mock_response(status_code: int = 200, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


def make_post_html(
    title: str = "Test Post",
    published: str = "2024-01-15T10:00:00",
    category: str = "Tech",
    tags: list[str] | None = None,
    content: str = "<p>Hello</p>",
    use_og_title: bool = True,
    use_time_tag: bool = False,
) -> str:
    tags = tags or []
    tag_html = "".join(f'<a class="tag" href="#">{t}</a>' for t in tags)

    if use_og_title:
        title_html = f'<meta property="og:title" content="{title}" />'
    else:
        title_html = f"<h1>{title}</h1>"

    if use_time_tag:
        pub_html = f'<time datetime="{published}">2024</time>'
    else:
        pub_html = f'<meta property="article:published_time" content="{published}" />'

    return f"""<html><head>
{title_html}
{pub_html}
</head><body>
<div class="category"><a href="#">{category}</a></div>
<div class="tag">{tag_html}</div>
<div class="entry-content">{content}</div>
</body></html>"""


SITEMAP_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://myblog.tistory.com/entry/post-one</loc></url>
  <url><loc>https://myblog.tistory.com/entry/post-two</loc></url>
  <url><loc>https://myblog.tistory.com/</loc></url>
</urlset>"""

ARCHIVE_HTML = """\
<html><body>
<a href="/entry/archive-post-1">Post 1</a>
<a href="https://myblog.tistory.com/entry/archive-post-2">Post 2</a>
<a href="/about">About</a>
<a href="/entry/archive-post-1">Post 1 duplicate</a>
</body></html>"""

ROBOTS_TXT_ALLOW = "User-agent: *\nAllow: /"
ROBOTS_TXT_DISALLOW = "User-agent: *\nDisallow: /"


# ---------------------------------------------------------------------------
# ScraperBlockedError
# ---------------------------------------------------------------------------


class TestScraperBlockedError:
    def test_has_partial_posts(self) -> None:
        posts = [MagicMock(spec=TistoryPost)]
        err = ScraperBlockedError("blocked", partial_posts=posts)
        assert err.partial_posts is posts

    def test_message_accessible(self) -> None:
        err = ScraperBlockedError("403 on /entry/1", partial_posts=[])
        assert "403" in str(err)

    def test_empty_partial_posts(self) -> None:
        err = ScraperBlockedError("blocked", partial_posts=[])
        assert err.partial_posts == []

    def test_is_exception(self) -> None:
        err = ScraperBlockedError("x", partial_posts=[])
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# Name property
# ---------------------------------------------------------------------------


class TestName:
    def test_name_is_scraper(self) -> None:
        e = make_extractor()
        assert e.name == "scraper"

    def test_implements_base_extractor(self) -> None:
        from tistory_migrator.extractor import BaseExtractor
        assert isinstance(make_extractor(), BaseExtractor)


# ---------------------------------------------------------------------------
# _strip_xml_namespaces
# ---------------------------------------------------------------------------


class TestStripXmlNamespaces:
    def test_strips_default_namespace(self) -> None:
        xml = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url/></urlset>'
        stripped = TistoryScraperExtractor._strip_xml_namespaces(xml)
        assert 'xmlns=' not in stripped
        assert "<urlset>" in stripped

    def test_strips_prefixed_namespace(self) -> None:
        xml = '<root xmlns:sm="http://example.com"><sm:loc/></root>'
        stripped = TistoryScraperExtractor._strip_xml_namespaces(xml)
        assert 'xmlns:sm=' not in stripped

    def test_no_namespace_unchanged(self) -> None:
        xml = "<urlset><url><loc>http://x.com</loc></url></urlset>"
        assert TistoryScraperExtractor._strip_xml_namespaces(xml) == xml

    def test_strips_multiple_namespaces(self) -> None:
        xml = '<root xmlns="http://a.com" xmlns:b="http://b.com"/>'
        stripped = TistoryScraperExtractor._strip_xml_namespaces(xml)
        assert "xmlns" not in stripped


# ---------------------------------------------------------------------------
# _get (rate limiting)
# ---------------------------------------------------------------------------


class TestGet:
    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_sleeps_before_request(self, mock_sleep: MagicMock) -> None:
        e = make_extractor(rate_limit_sleep=2.0)
        e._session.get = MagicMock(return_value=mock_response())
        e._get("http://example.com/page")
        mock_sleep.assert_called_once_with(2.0)

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_response(self, _: MagicMock) -> None:
        e = make_extractor()
        resp = mock_response(200, "hello")
        e._session.get = MagicMock(return_value=resp)
        assert e._get("http://x.com") is resp

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_uses_configured_sleep(self, mock_sleep: MagicMock) -> None:
        e = make_extractor(rate_limit_sleep=0.5)
        e._session.get = MagicMock(return_value=mock_response())
        e._get("http://x.com")
        mock_sleep.assert_called_once_with(0.5)


# ---------------------------------------------------------------------------
# _load_robots
# ---------------------------------------------------------------------------


class TestLoadRobots:
    def test_parses_robots_on_200(self) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ROBOTS_TXT_ALLOW))
        rp = e._load_robots()
        assert rp.can_fetch("*", f"{BASE}/entry/test")

    def test_sets_allow_all_on_404(self) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        rp = e._load_robots()
        assert rp.allow_all is True

    def test_sets_allow_all_on_connection_error(self) -> None:
        e = make_extractor()
        e._session.get = MagicMock(side_effect=ConnectionError("timeout"))
        rp = e._load_robots()
        assert rp.allow_all is True

    def test_uses_session_get_directly(self) -> None:
        """robots.txt must use session.get (not _get) — no rate limit sleep."""
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ROBOTS_TXT_ALLOW))
        with patch.object(e, "_get") as mock_get:
            e._load_robots()
            mock_get.assert_not_called()
        e._session.get.assert_called_once()

    def test_disallow_all_robots(self) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ROBOTS_TXT_DISALLOW))
        rp = e._load_robots()
        assert not rp.can_fetch("*", f"{BASE}/entry/test")

    def test_requests_correct_url(self) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        e._load_robots()
        e._session.get.assert_called_once_with(
            f"{BASE}/robots.txt", timeout=10
        )


# ---------------------------------------------------------------------------
# _discover_urls_from_sitemap
# ---------------------------------------------------------------------------


class TestDiscoverUrlsFromSitemap:
    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_entry_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, SITEMAP_XML))
        urls = e._discover_urls_from_sitemap()
        assert urls == [
            "https://myblog.tistory.com/entry/post-one",
            "https://myblog.tistory.com/entry/post-two",
        ]

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_excludes_non_entry_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, SITEMAP_XML))
        urls = e._discover_urls_from_sitemap()
        assert all("/entry/" in u for u in (urls or []))

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_raises_blocked_on_403(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(403))
        with pytest.raises(ScraperBlockedError):
            e._discover_urls_from_sitemap()

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_none_on_non_200(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        assert e._discover_urls_from_sitemap() is None

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_none_on_parse_error(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, "NOT XML <<>>"))
        assert e._discover_urls_from_sitemap() is None

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_none_when_no_entry_urls(self, _: MagicMock) -> None:
        xml = '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://myblog.tistory.com/</loc></url></urlset>'
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, xml))
        assert e._discover_urls_from_sitemap() is None

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_none_on_request_exception(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(side_effect=ConnectionError("down"))
        assert e._discover_urls_from_sitemap() is None

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_strips_namespace_before_parsing(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, SITEMAP_XML))
        # Should not raise and should return URLs (namespace stripped)
        urls = e._discover_urls_from_sitemap()
        assert urls is not None
        assert len(urls) == 2

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_requests_sitemap_url(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        e._discover_urls_from_sitemap()
        e._session.get.assert_called_once_with(
            f"{BASE}/sitemap.xml", timeout=30
        )

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_blocked_error_has_empty_partial_posts(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(403))
        with pytest.raises(ScraperBlockedError) as exc_info:
            e._discover_urls_from_sitemap()
        assert exc_info.value.partial_posts == []


# ---------------------------------------------------------------------------
# _discover_urls_from_archive
# ---------------------------------------------------------------------------


class TestDiscoverUrlsFromArchive:
    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_entry_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ARCHIVE_HTML))
        urls = e._discover_urls_from_archive()
        assert "https://myblog.tistory.com/entry/archive-post-1" in urls
        assert "https://myblog.tistory.com/entry/archive-post-2" in urls

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_deduplicates_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ARCHIVE_HTML))
        urls = e._discover_urls_from_archive()
        # archive-post-1 appears twice in ARCHIVE_HTML
        assert urls.count("https://myblog.tistory.com/entry/archive-post-1") == 1

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_excludes_non_entry_links(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ARCHIVE_HTML))
        urls = e._discover_urls_from_archive()
        assert all("/entry/" in u for u in urls)

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_handles_relative_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><a href="/entry/relative-post">x</a></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        urls = e._discover_urls_from_archive()
        assert f"{BASE}/entry/relative-post" in urls

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_handles_absolute_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        html = f'<html><body><a href="{BASE}/entry/abs-post">x</a></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        urls = e._discover_urls_from_archive()
        assert f"{BASE}/entry/abs-post" in urls

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_raises_blocked_on_403(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(403))
        with pytest.raises(ScraperBlockedError):
            e._discover_urls_from_archive()

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_empty_on_non_200(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        assert e._discover_urls_from_archive() == []

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_empty_on_exception(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(side_effect=ConnectionError("down"))
        assert e._discover_urls_from_archive() == []

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_requests_category_url(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(404))
        e._discover_urls_from_archive()
        e._session.get.assert_called_once_with(
            f"{BASE}/category", timeout=30
        )


# ---------------------------------------------------------------------------
# _discover_urls (strategy dispatch)
# ---------------------------------------------------------------------------


class TestDiscoverUrls:
    def test_uses_sitemap_when_available(self) -> None:
        e = make_extractor()
        sitemap_urls = ["https://myblog.tistory.com/entry/post-1"]
        with patch.object(e, "_discover_urls_from_sitemap", return_value=sitemap_urls):
            with patch.object(e, "_discover_urls_from_archive") as mock_arch:
                result = e._discover_urls()
        assert result == sitemap_urls
        mock_arch.assert_not_called()

    def test_falls_back_to_archive_when_sitemap_none(self) -> None:
        e = make_extractor()
        archive_urls = ["https://myblog.tistory.com/entry/post-a"]
        with patch.object(e, "_discover_urls_from_sitemap", return_value=None):
            with patch.object(e, "_discover_urls_from_archive", return_value=archive_urls):
                result = e._discover_urls()
        assert result == archive_urls

    def test_catches_sitemap_blocked_and_tries_archive(self) -> None:
        e = make_extractor()
        archive_urls = ["https://myblog.tistory.com/entry/post-a"]
        blocked = ScraperBlockedError("sitemap 403", partial_posts=[])
        with patch.object(e, "_discover_urls_from_sitemap", side_effect=blocked):
            with patch.object(e, "_discover_urls_from_archive", return_value=archive_urls):
                result = e._discover_urls()
        assert result == archive_urls

    def test_returns_empty_when_both_blocked(self) -> None:
        e = make_extractor()
        blocked = ScraperBlockedError("403", partial_posts=[])
        with patch.object(e, "_discover_urls_from_sitemap", side_effect=blocked):
            with patch.object(e, "_discover_urls_from_archive", side_effect=blocked):
                result = e._discover_urls()
        assert result == []

    def test_returns_empty_when_both_empty(self) -> None:
        e = make_extractor()
        with patch.object(e, "_discover_urls_from_sitemap", return_value=None):
            with patch.object(e, "_discover_urls_from_archive", return_value=[]):
                result = e._discover_urls()
        assert result == []


# ---------------------------------------------------------------------------
# _parse_post_page
# ---------------------------------------------------------------------------


class TestParsePostPage:
    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_og_title(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(title="My Post", use_og_title=True)
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/my-post")
        assert post.title == "My Post"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_falls_back_to_h1_title(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(title="H1 Title", use_og_title=False)
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/h1-post")
        assert post.title == "H1 Title"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_title_untitled_when_no_h1(self, _: MagicMock) -> None:
        e = make_extractor()
        html = "<html><body><div class='entry-content'>text</div></body></html>"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/no-title")
        assert post.title == "untitled"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_published_from_meta(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(published="2024-03-15T12:30:00")
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/dated")
        assert post.published_at == datetime(2024, 3, 15, 12, 30, 0)

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_published_from_time_tag(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(published="2024-05-20T08:00:00", use_time_tag=True)
        # Remove article:published_time meta from html
        html = html.replace('<meta property="article:published_time"', '<meta property="x-other"')
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/time-tag")
        assert post.published_at == datetime(2024, 5, 20, 8, 0, 0)

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_uses_datetime_min_when_no_date(self, _: MagicMock) -> None:
        e = make_extractor()
        html = "<html><body><div class='entry-content'>text</div></body></html>"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/no-date")
        assert post.published_at == datetime.min

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_category_from_category_a(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(category="Python")
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/cat-post")
        assert post.category == "Python"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_category_from_link_cate(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><a class="link_cate" href="#">Dev</a><div class="entry-content">x</div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/cate-post")
        assert post.category == "Dev"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_empty_category_when_none_found(self, _: MagicMock) -> None:
        e = make_extractor()
        html = "<html><body><div class='entry-content'>text</div></body></html>"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/no-cat")
        assert post.category == ""

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_tags_from_tag_a(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html(tags=["python", "django"])
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/tagged")
        assert post.tags == ["python", "django"]

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_tags_from_link_tag(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><a class="link_tag" href="#">flask</a><div class="entry-content">x</div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/link-tag")
        assert post.tags == ["flask"]

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_empty_tags_when_none_found(self, _: MagicMock) -> None:
        e = make_extractor()
        html = "<html><body><div class='entry-content'>text</div></body></html>"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/no-tags")
        assert post.tags == []

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_content_selector_entry_content(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div class="entry-content"><p>body</p></div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/content-1")
        assert "<p>body</p>" in post.content_html

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_content_selector_article_post_content(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><article><div class="post-content"><p>text</p></div></article></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/content-2")
        assert "<p>text</p>" in post.content_html

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_content_selector_article_fallback(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><article><p>article text</p></article></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/content-3")
        assert "<p>article text</p>" in post.content_html

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_content_selector_post_content_fallback(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div class="post-content"><p>pc text</p></div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/content-4")
        assert "<p>pc text</p>" in post.content_html

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_content_selector_content_post_fallback(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div id="content"><div class="post"><p>nested</p></div></div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/content-5")
        assert "<p>nested</p>" in post.content_html

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_empty_content_when_no_selector_matches(self, _: MagicMock) -> None:
        e = make_extractor()
        html = "<html><body><div class='other'>text</div></body></html>"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/no-content")
        assert post.content_html == ""

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_raises_blocked_on_403(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(403))
        with pytest.raises(ScraperBlockedError):
            e._parse_post_page(f"{BASE}/entry/blocked")

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_raises_http_error_on_404(self, _: MagicMock) -> None:
        import requests as req
        e = make_extractor()
        resp = mock_response(404)
        resp.raise_for_status.side_effect = req.HTTPError("404")
        e._session.get = MagicMock(return_value=resp)
        with pytest.raises(req.HTTPError):
            e._parse_post_page(f"{BASE}/entry/missing")

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_images_from_content(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div class="entry-content"><img src="https://img.example.com/photo.jpg" /></div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/with-img")
        assert "https://img.example.com/photo.jpg" in post.images

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_extracts_id_from_url(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div class="entry-content">x</div></body></html>'
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/my-post-title")
        assert post.id == "my-post-title"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_post_url_stored(self, _: MagicMock) -> None:
        e = make_extractor()
        html = '<html><body><div class="entry-content">x</div></body></html>'
        url = f"{BASE}/entry/stored-url"
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(url)
        assert post.url == url

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_tistory_post(self, _: MagicMock) -> None:
        e = make_extractor()
        html = make_post_html()
        e._session.get = MagicMock(return_value=mock_response(200, html))
        post = e._parse_post_page(f"{BASE}/entry/check-type")
        assert isinstance(post, TistoryPost)


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

POST_HTML_1 = make_post_html(title="Post One", published="2024-01-10T10:00:00", category="Tech", tags=["py"])
POST_HTML_2 = make_post_html(title="Post Two", published="2024-06-20T10:00:00", category="Life", tags=["travel"])


class TestExtract:
    def _setup_extractor(
        self,
        urls: list[str],
        post_htmls: dict[str, str],
        robots_txt: str = ROBOTS_TXT_ALLOW,
    ) -> TistoryScraperExtractor:
        e = make_extractor()

        def session_get(url: str, **kwargs: object) -> MagicMock:
            if "robots.txt" in url:
                return mock_response(200, robots_txt)
            if url in post_htmls:
                return mock_response(200, post_htmls[url])
            return mock_response(404)

        with patch.object(e, "_discover_urls", return_value=urls):
            with patch("tistory_migrator.extractor.scraper.time.sleep"):
                e._session.get = MagicMock(side_effect=session_get)
                return e

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_all_posts(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-2"
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1) if "post-1" in u
            else mock_response(200, POST_HTML_2)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            posts = e.extract()
        assert len(posts) == 2

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_raises_blocked_with_partial_posts(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-blocked"
        responses = {
            url1: mock_response(200, POST_HTML_1),
            url2: mock_response(403),
        }
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else responses.get(u, mock_response(404))
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            with pytest.raises(ScraperBlockedError) as exc_info:
                e.extract()
        assert len(exc_info.value.partial_posts) == 1
        assert exc_info.value.partial_posts[0].title == "Post One"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_skips_post_on_other_error(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-error"

        def get_side_effect(u: str, **kw: object) -> MagicMock:
            if "robots" in u:
                return mock_response(200, ROBOTS_TXT_ALLOW)
            if "post-1" in u:
                return mock_response(200, POST_HTML_1)
            raise ConnectionError("network error")

        e._session.get = MagicMock(side_effect=get_side_effect)
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            posts = e.extract()
        # Should get the first post, skip the second
        assert len(posts) == 1

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_filters_by_category_case_insensitive(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-2"
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1) if "post-1" in u
            else mock_response(200, POST_HTML_2)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            posts = e.extract(category="TECH")
        assert len(posts) == 1
        assert posts[0].title == "Post One"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_filters_by_after_inclusive(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-2"
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1) if "post-1" in u
            else mock_response(200, POST_HTML_2)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            posts = e.extract(after=datetime(2024, 1, 10, 10, 0, 0))
        assert len(posts) == 2  # inclusive: post-1 published exactly at after

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_filters_by_before_inclusive(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-2"
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1) if "post-1" in u
            else mock_response(200, POST_HTML_2)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2]):
            posts = e.extract(before=datetime(2024, 1, 10, 10, 0, 0))
        assert len(posts) == 1  # only post-1 (exactly at boundary)
        assert posts[0].title == "Post One"

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_skips_disallowed_robots(self, _: MagicMock) -> None:
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_DISALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1]):
            posts = e.extract()
        assert len(posts) == 0

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_returns_empty_when_no_urls(self, _: MagicMock) -> None:
        e = make_extractor()
        e._session.get = MagicMock(return_value=mock_response(200, ROBOTS_TXT_ALLOW))
        with patch.object(e, "_discover_urls", return_value=[]):
            posts = e.extract()
        assert posts == []

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_robots_loaded_before_crawl(self, _: MagicMock) -> None:
        """robots.txt is loaded via session.get before any _get calls."""
        e = make_extractor()
        robot_called = []

        def session_get(u: str, **kw: object) -> MagicMock:
            if "robots" in u:
                robot_called.append(u)
                return mock_response(200, ROBOTS_TXT_ALLOW)
            return mock_response(200, POST_HTML_1)

        e._session.get = MagicMock(side_effect=session_get)
        url1 = f"{BASE}/entry/post-1"
        with patch.object(e, "_discover_urls", return_value=[url1]):
            with patch.object(e, "_get", wraps=e._get):
                e.extract()
        assert len(robot_called) == 1

    @patch("tistory_migrator.extractor.scraper.time.sleep")
    def test_blocked_error_partial_posts_accumulate(self, _: MagicMock) -> None:
        """partial_posts includes posts successfully extracted before the block."""
        e = make_extractor()
        url1 = f"{BASE}/entry/post-1"
        url2 = f"{BASE}/entry/post-2"
        url3 = f"{BASE}/entry/post-blocked"
        html_p2 = make_post_html(title="Post Two Alt", published="2024-02-01T00:00:00")
        e._session.get = MagicMock(side_effect=lambda u, **kw: (
            mock_response(200, ROBOTS_TXT_ALLOW) if "robots" in u
            else mock_response(200, POST_HTML_1) if "post-1" in u
            else mock_response(200, html_p2) if "post-2" in u
            else mock_response(403)
        ))
        with patch.object(e, "_discover_urls", return_value=[url1, url2, url3]):
            with pytest.raises(ScraperBlockedError) as exc_info:
                e.extract()
        assert len(exc_info.value.partial_posts) == 2


# ---------------------------------------------------------------------------
# Package import
# ---------------------------------------------------------------------------


class TestPackageImport:
    def test_scraper_importable_from_extractor(self) -> None:
        from tistory_migrator.extractor import (
            ScraperBlockedError,
            TistoryScraperExtractor,
        )
        assert TistoryScraperExtractor
        assert ScraperBlockedError

    def test_all_exports_present(self) -> None:
        import tistory_migrator.extractor as ext
        assert "TistoryScraperExtractor" in ext.__all__
        assert "ScraperBlockedError" in ext.__all__
