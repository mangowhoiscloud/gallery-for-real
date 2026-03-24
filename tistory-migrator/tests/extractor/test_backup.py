"""Tests for TistoryBackupExtractor (XML backup parsing)."""
from __future__ import annotations

import textwrap
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from tistory_migrator.extractor.backup import (
    BackupFileNotFoundError,
    BackupParseError,
    TistoryBackupExtractor,
)
from tistory_migrator.extractor.base import BaseExtractor

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_XML = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <blog>
      <posts>
        <post>
          <id>42</id>
          <title>파이썬 개발 팁</title>
          <content><![CDATA[<h2>본문</h2><img src="https://img.example.com/photo.jpg">]]></content>
          <category>Python</category>
          <tags>
            <tag>Python</tag>
            <tag>Flask</tag>
          </tags>
          <published>2024-06-15T10:30:00+09:00</published>
          <url>https://blog.tistory.com/42</url>
        </post>
      </posts>
    </blog>
""")

SAMPLE_XML_SPACE_DATE = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <blog>
      <posts>
        <post>
          <id>1</id>
          <title>Hello</title>
          <content><![CDATA[<p>content</p>]]></content>
          <category>Dev</category>
          <tags/>
          <published>2024-01-15 09:00:00</published>
          <url>https://blog.tistory.com/1</url>
        </post>
      </posts>
    </blog>
""")

SAMPLE_XML_DATE_ONLY = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <blog>
      <posts>
        <post>
          <id>2</id>
          <title>Date only</title>
          <content><![CDATA[<p>content</p>]]></content>
          <category>Dev</category>
          <tags/>
          <published>2024-03-10</published>
          <url>https://blog.tistory.com/2</url>
        </post>
      </posts>
    </blog>
""")

SAMPLE_XML_ID_ATTR = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <blog>
      <posts>
        <post id="99">
          <title>Attr ID</title>
          <content><![CDATA[<p>attr id content</p>]]></content>
          <category>Test</category>
          <tags/>
          <published>2024-05-01T00:00:00</published>
          <url>https://blog.tistory.com/99</url>
        </post>
      </posts>
    </blog>
""")

MULTI_POST_XML = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <blog>
      <posts>
        <post>
          <id>1</id>
          <title>First Post</title>
          <content><![CDATA[<p>first</p>]]></content>
          <category>A</category>
          <tags><tag>foo</tag></tags>
          <published>2024-01-01T00:00:00</published>
          <url>https://blog.tistory.com/1</url>
        </post>
        <post>
          <id>2</id>
          <title>Second Post</title>
          <content><![CDATA[<p>second</p>]]></content>
          <category>B</category>
          <tags><tag>bar</tag></tags>
          <published>2024-06-01T00:00:00</published>
          <url>https://blog.tistory.com/2</url>
        </post>
        <post>
          <id>3</id>
          <title>Third Post</title>
          <content><![CDATA[<p>third</p>]]></content>
          <category>A</category>
          <tags><tag>baz</tag></tags>
          <published>2024-12-01T00:00:00</published>
          <url>https://blog.tistory.com/3</url>
        </post>
      </posts>
    </blog>
""")


def _make_extractor(xml_string: str) -> TistoryBackupExtractor:
    """Create an extractor that reads xml_string instead of a real file."""
    ext = TistoryBackupExtractor("/fake/backup.xml")
    ext._parse_xml_string  # ensure method exists
    with patch.object(ext, "_load_xml", return_value=ext._parse_xml_string(xml_string)):
        pass
    # Patch at extract time via _load_xml
    return ext


# ---------------------------------------------------------------------------
# Interface / inheritance
# ---------------------------------------------------------------------------


def test_is_baseextractor():
    ext = TistoryBackupExtractor("/fake/path.xml")
    assert isinstance(ext, BaseExtractor)


def test_name_property():
    ext = TistoryBackupExtractor("/fake/path.xml")
    assert ext.name == "xml"


# ---------------------------------------------------------------------------
# File loading errors
# ---------------------------------------------------------------------------


def test_file_not_found_raises(tmp_path: Path):
    ext = TistoryBackupExtractor(str(tmp_path / "nonexistent.xml"))
    with pytest.raises(BackupFileNotFoundError):
        ext.extract()


def test_malformed_xml_raises(tmp_path: Path):
    bad_xml = tmp_path / "bad.xml"
    bad_xml.write_text("<blog><unclosed>", encoding="utf-8")
    ext = TistoryBackupExtractor(str(bad_xml))
    with pytest.raises(BackupParseError):
        ext.extract()


def test_empty_xml_raises(tmp_path: Path):
    empty = tmp_path / "empty.xml"
    empty.write_text("", encoding="utf-8")
    ext = TistoryBackupExtractor(str(empty))
    with pytest.raises(BackupParseError):
        ext.extract()


def test_parse_xml_string_raises_on_malformed():
    ext = TistoryBackupExtractor("/fake/path.xml")
    with pytest.raises(BackupParseError):
        ext._parse_xml_string("<bad><unclosed>")


# ---------------------------------------------------------------------------
# Basic extraction from XML string (via mocked _load_xml)
# ---------------------------------------------------------------------------


def _extract_from_string(xml_string: str, **kwargs) -> list:
    ext = TistoryBackupExtractor("/fake/path.xml")
    root = ext._parse_xml_string(xml_string)
    with patch.object(ext, "_load_xml", return_value=root):
        return ext.extract(**kwargs)


def test_extract_basic_post():
    posts = _extract_from_string(SAMPLE_XML)
    assert len(posts) == 1
    post = posts[0]
    assert post.id == "42"
    assert post.title == "파이썬 개발 팁"
    assert "<h2>본문</h2>" in post.content_html
    assert post.category == "Python"


def test_extract_tags_list():
    posts = _extract_from_string(SAMPLE_XML)
    assert posts[0].tags == ["Python", "Flask"]


def test_extract_published_at_iso_with_timezone():
    posts = _extract_from_string(SAMPLE_XML)
    post = posts[0]
    assert post.published_at.year == 2024
    assert post.published_at.month == 6
    assert post.published_at.day == 15
    assert post.published_at.hour == 10
    assert post.published_at.minute == 30


def test_extract_url():
    posts = _extract_from_string(SAMPLE_XML)
    assert posts[0].url == "https://blog.tistory.com/42"


def test_extract_images_from_content():
    posts = _extract_from_string(SAMPLE_XML)
    assert posts[0].images == ["https://img.example.com/photo.jpg"]


# ---------------------------------------------------------------------------
# ID formats
# ---------------------------------------------------------------------------


def test_id_from_child_element():
    posts = _extract_from_string(SAMPLE_XML)
    assert posts[0].id == "42"


def test_id_from_attribute():
    posts = _extract_from_string(SAMPLE_XML_ID_ATTR)
    assert posts[0].id == "99"
    assert posts[0].title == "Attr ID"


# ---------------------------------------------------------------------------
# Date format variants
# ---------------------------------------------------------------------------


def test_date_space_separated():
    """Format: %Y-%m-%d %H:%M:%S"""
    posts = _extract_from_string(SAMPLE_XML_SPACE_DATE)
    assert len(posts) == 1
    p = posts[0]
    assert p.published_at.year == 2024
    assert p.published_at.month == 1
    assert p.published_at.day == 15
    assert p.published_at.hour == 9


def test_date_only_format():
    """Format: %Y-%m-%d"""
    posts = _extract_from_string(SAMPLE_XML_DATE_ONLY)
    assert len(posts) == 1
    p = posts[0]
    assert p.published_at.year == 2024
    assert p.published_at.month == 3
    assert p.published_at.day == 10


def test_published_at_never_datetime_min():
    """Spec-reinforced: published_at must be a real date, not datetime.min."""
    posts = _extract_from_string(SAMPLE_XML)
    for post in posts:
        assert post.published_at != datetime.min


# ---------------------------------------------------------------------------
# Edge cases: empty / missing fields
# ---------------------------------------------------------------------------


def test_empty_content_post_is_skipped():
    xml = textwrap.dedent("""\
        <blog><posts>
          <post>
            <id>9</id>
            <title>Empty</title>
            <content><![CDATA[]]></content>
            <category>X</category>
            <tags/>
            <published>2024-01-01T00:00:00</published>
            <url>https://blog.tistory.com/9</url>
          </post>
        </posts></blog>
    """)
    posts = _extract_from_string(xml)
    assert posts == []


def test_missing_content_element_is_skipped():
    xml = textwrap.dedent("""\
        <blog><posts>
          <post>
            <id>10</id>
            <title>No content element</title>
            <category>X</category>
            <tags/>
            <published>2024-01-01T00:00:00</published>
            <url>https://blog.tistory.com/10</url>
          </post>
        </posts></blog>
    """)
    posts = _extract_from_string(xml)
    assert posts == []


def test_missing_title_uses_untitled_fallback():
    xml = textwrap.dedent("""\
        <blog><posts>
          <post>
            <id>11</id>
            <title></title>
            <content><![CDATA[<p>content</p>]]></content>
            <category>X</category>
            <tags/>
            <published>2024-01-01T00:00:00</published>
            <url>https://blog.tistory.com/11</url>
          </post>
        </posts></blog>
    """)
    posts = _extract_from_string(xml)
    assert posts[0].title == "untitled-11"


def test_unparseable_date_is_skipped():
    xml = textwrap.dedent("""\
        <blog><posts>
          <post>
            <id>12</id>
            <title>Bad date</title>
            <content><![CDATA[<p>content</p>]]></content>
            <category>X</category>
            <tags/>
            <published>not-a-date</published>
            <url>https://blog.tistory.com/12</url>
          </post>
        </posts></blog>
    """)
    posts = _extract_from_string(xml)
    assert posts == []


def test_empty_tags_element_gives_empty_list():
    posts = _extract_from_string(SAMPLE_XML_SPACE_DATE)
    assert posts[0].tags == []


def test_tags_with_multiple_children():
    posts = _extract_from_string(SAMPLE_XML)
    assert len(posts[0].tags) == 2
    assert "Python" in posts[0].tags
    assert "Flask" in posts[0].tags


def test_no_images_gives_empty_list():
    xml = textwrap.dedent("""\
        <blog><posts>
          <post>
            <id>5</id>
            <title>No images</title>
            <content><![CDATA[<p>text only</p>]]></content>
            <category>X</category>
            <tags/>
            <published>2024-01-01T00:00:00</published>
            <url>https://blog.tistory.com/5</url>
          </post>
        </posts></blog>
    """)
    posts = _extract_from_string(xml)
    assert posts[0].images == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_filter_by_category():
    posts = _extract_from_string(MULTI_POST_XML, category="A")
    assert len(posts) == 2
    assert all(p.category == "A" for p in posts)


def test_filter_by_category_case_insensitive():
    posts = _extract_from_string(MULTI_POST_XML, category="a")
    assert len(posts) == 2


def test_filter_by_after_inclusive():
    after = datetime(2024, 6, 1, 0, 0, 0)
    posts = _extract_from_string(MULTI_POST_XML, after=after)
    assert len(posts) == 2
    for p in posts:
        assert p.published_at >= after


def test_filter_by_before_inclusive():
    before = datetime(2024, 6, 1, 0, 0, 0)
    posts = _extract_from_string(MULTI_POST_XML, before=before)
    assert len(posts) == 2
    for p in posts:
        assert p.published_at <= before


def test_filter_combined_date_and_category():
    after = datetime(2024, 1, 1, 0, 0, 0)
    before = datetime(2024, 6, 30, 0, 0, 0)
    posts = _extract_from_string(MULTI_POST_XML, after=after, before=before, category="B")
    assert len(posts) == 1
    assert posts[0].id == "2"


def test_filter_no_match_returns_empty():
    posts = _extract_from_string(SAMPLE_XML, category="NonExistent")
    assert posts == []


def test_no_filters_returns_all():
    posts = _extract_from_string(MULTI_POST_XML)
    assert len(posts) == 3


# ---------------------------------------------------------------------------
# Real file I/O (uses tmp_path fixture)
# ---------------------------------------------------------------------------


def test_extract_from_real_file(tmp_path: Path):
    xml_file = tmp_path / "backup.xml"
    xml_file.write_text(SAMPLE_XML, encoding="utf-8")
    ext = TistoryBackupExtractor(str(xml_file))
    posts = ext.extract()
    assert len(posts) == 1
    assert posts[0].id == "42"


def test_extract_multiple_posts_from_real_file(tmp_path: Path):
    xml_file = tmp_path / "multi.xml"
    xml_file.write_text(MULTI_POST_XML, encoding="utf-8")
    ext = TistoryBackupExtractor(str(xml_file))
    posts = ext.extract()
    assert len(posts) == 3


# ---------------------------------------------------------------------------
# Package import
# ---------------------------------------------------------------------------


def test_package_import():
    from tistory_migrator.extractor import (  # noqa: F401
        BackupFileNotFoundError,
        BackupParseError,
        TistoryBackupExtractor,
    )
