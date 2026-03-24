"""Tests for converter.py — target ≥70% test code per project convention."""
from __future__ import annotations

from datetime import datetime

import yaml

from tistory_migrator.converter import (
    _generate_frontmatter,
    _replace_img_srcs,
    _url_to_filename,
    convert_post,
    generate_slug,
    process_tistory_tags,
)
from tistory_migrator.models import TistoryPost


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_post(**kwargs) -> TistoryPost:
    defaults = {
        'id': '1',
        'title': '테스트 포스트',
        'content_html': '<p>Hello</p>',
        'category': '개발',
        'tags': ['python', 'test'],
        'published_at': datetime(2024, 6, 15, 12, 0, 0),
        'url': 'https://example.tistory.com/1',
        'images': [],
    }
    defaults.update(kwargs)
    return TistoryPost(**defaults)


# ---------------------------------------------------------------------------
# generate_slug
# ---------------------------------------------------------------------------

class TestGenerateSlug:
    def test_korean_preserved(self):
        assert generate_slug('파이썬 개발 팁') == '파이썬-개발-팁'

    def test_spaces_become_hyphens(self):
        assert generate_slug('hello world') == 'hello-world'

    def test_ascii_lowercased(self):
        assert generate_slug('Hello World') == 'hello-world'

    def test_special_chars_removed(self):
        assert generate_slug('hello! world?') == 'hello-world'

    def test_consecutive_hyphens_collapsed(self):
        assert generate_slug('hello  world') == 'hello-world'

    def test_leading_trailing_hyphens_stripped(self):
        assert generate_slug(' hello ') == 'hello'

    def test_mixed_korean_ascii(self):
        result = generate_slug('Python 파이썬 개발')
        assert result == 'python-파이썬-개발'

    def test_only_special_chars(self):
        assert generate_slug('!!!') == ''

    def test_empty_string(self):
        assert generate_slug('') == ''

    def test_single_word_korean(self):
        assert generate_slug('파이썬') == '파이썬'

    def test_single_word_ascii(self):
        assert generate_slug('Python') == 'python'

    def test_digits_preserved(self):
        assert generate_slug('post 2024') == 'post-2024'

    def test_colons_removed(self):
        assert generate_slug('title: subtitle') == 'title-subtitle'

    def test_slash_removed(self):
        assert generate_slug('a/b') == 'ab'

    def test_dot_removed(self):
        assert generate_slug('v1.0') == 'v10'

    def test_parentheses_removed(self):
        assert generate_slug('hello (world)') == 'hello-world'

    def test_multiple_spaces_collapse(self):
        assert generate_slug('a   b') == 'a-b'

    def test_korean_jamo_preserved(self):
        # Hangul Jamo range U+1100-U+11FF
        assert generate_slug('ᄀ') == 'ᄀ'

    def test_hangul_compat_jamo_preserved(self):
        # Hangul Compatibility Jamo range U+3130-U+318F
        assert generate_slug('ㅎ') == 'ㅎ'

    def test_non_korean_unicode_removed(self):
        # Chinese characters should be removed
        result = generate_slug('hello 中文')
        assert result == 'hello'

    def test_hyphen_only_input(self):
        assert generate_slug('---') == ''


# ---------------------------------------------------------------------------
# process_tistory_tags
# ---------------------------------------------------------------------------

class TestProcessTistoryTags:
    def test_image_tag_basic(self):
        html = '[##_Image|photo.jpg|width=300|_##]'
        result = process_tistory_tags(html)
        assert '<img src="photo.jpg">' in result

    def test_image_tag_preserves_first_segment(self):
        html = '[##_Image|my-image.png|200|100|center_##]'
        result = process_tistory_tags(html)
        assert 'src="my-image.png"' in result

    def test_image_tag_with_url(self):
        html = '[##_Image|https://img.tistory.com/pic.jpg|300|_##]'
        result = process_tistory_tags(html)
        assert 'src="https://img.tistory.com/pic.jpg"' in result

    def test_code_tag_with_language(self):
        html = '[##_Code|python|print("hello")_##]'
        result = process_tistory_tags(html)
        assert 'class="language-python"' in result
        assert 'print("hello")' in result
        assert '<pre>' in result

    def test_code_tag_empty_language(self):
        html = '[##_Code||some code_##]'
        result = process_tistory_tags(html)
        assert '<pre><code>some code</code></pre>' in result
        assert 'language-' not in result

    def test_code_tag_bash(self):
        html = '[##_Code|bash|echo hello_##]'
        result = process_tistory_tags(html)
        assert 'class="language-bash"' in result

    def test_code_tag_multiline(self):
        code = 'line1\nline2\nline3'
        html = f'[##_Code|python|{code}_##]'
        result = process_tistory_tags(html)
        assert 'line1\nline2\nline3' in result
        assert 'language-python' in result

    def test_codeblock_tag_no_language(self):
        html = '[##_CodeBlock|some code here_##]'
        result = process_tistory_tags(html)
        assert '<pre><code>some code here</code></pre>' in result
        assert 'language-' not in result

    def test_codeblock_tag_multiline(self):
        html = '[##_CodeBlock|line1\nline2_##]'
        result = process_tistory_tags(html)
        assert 'line1\nline2' in result

    def test_no_custom_tags(self):
        html = '<p>Regular HTML content</p>'
        result = process_tistory_tags(html)
        assert result == html

    def test_multiple_image_tags(self):
        html = '[##_Image|a.jpg|_##] text [##_Image|b.png|_##]'
        result = process_tistory_tags(html)
        assert 'src="a.jpg"' in result
        assert 'src="b.png"' in result

    def test_image_and_code_mixed(self):
        html = '[##_Image|pic.jpg|_##]\n[##_Code|python|x=1_##]'
        result = process_tistory_tags(html)
        assert 'src="pic.jpg"' in result
        assert 'language-python' in result

    def test_original_tag_removed(self):
        html = '[##_Image|photo.jpg|_##]'
        result = process_tistory_tags(html)
        assert '[##_Image' not in result
        assert '_##]' not in result

    def test_code_tag_original_removed(self):
        html = '[##_Code|python|x=1_##]'
        result = process_tistory_tags(html)
        assert '[##_Code' not in result

    def test_code_language_whitespace_stripped(self):
        html = '[##_Code| python |x=1_##]'
        result = process_tistory_tags(html)
        assert 'language-python' in result


# ---------------------------------------------------------------------------
# _url_to_filename
# ---------------------------------------------------------------------------

class TestUrlToFilename:
    def test_simple_url(self):
        assert _url_to_filename('https://example.com/images/photo.jpg') == 'photo.jpg'

    def test_url_with_query(self):
        assert _url_to_filename('https://example.com/img.png?w=300') == 'img.png'

    def test_url_no_extension(self):
        # No extension, basename is still the last path segment
        assert _url_to_filename('https://example.com/images/photo') == 'photo'

    def test_url_empty_path(self):
        assert _url_to_filename('https://example.com/') == 'image.jpg'

    def test_url_with_empty_path_fallback(self):
        # Path ends with /, basename is empty → fallback to image.jpg
        assert _url_to_filename('https://img.daumcdn.net/thumb/R800x0/') == 'image.jpg'

    def test_tistory_image_url(self):
        url = 'https://img1.daumcdn.net/thumb/R800x0/ex/photo.png'
        assert _url_to_filename(url) == 'photo.png'


# ---------------------------------------------------------------------------
# _replace_img_srcs
# ---------------------------------------------------------------------------

class TestReplaceImgSrcs:
    def test_single_img(self):
        html = '<img src="https://example.com/photo.jpg">'
        result = _replace_img_srcs(html, 'my-post')
        assert 'src="/images/my-post/photo.jpg"' in result

    def test_double_quoted(self):
        html = '<img src="https://example.com/pic.png">'
        result = _replace_img_srcs(html, 'slug')
        assert '/images/slug/pic.png' in result

    def test_single_quoted(self):
        html = "<img src='https://example.com/pic.png'>"
        result = _replace_img_srcs(html, 'slug')
        assert '/images/slug/pic.png' in result

    def test_img_with_other_attrs(self):
        html = '<img alt="photo" src="https://example.com/x.jpg" width="300">'
        result = _replace_img_srcs(html, 'post')
        assert 'src="/images/post/x.jpg"' in result
        assert 'alt="photo"' in result
        assert 'width="300"' in result

    def test_multiple_imgs(self):
        html = '<img src="https://a.com/1.jpg"> <img src="https://b.com/2.png">'
        result = _replace_img_srcs(html, 'slug')
        assert '/images/slug/1.jpg' in result
        assert '/images/slug/2.png' in result

    def test_no_imgs_unchanged(self):
        html = '<p>No images here</p>'
        result = _replace_img_srcs(html, 'slug')
        assert result == html

    def test_korean_slug(self):
        html = '<img src="https://example.com/photo.jpg">'
        result = _replace_img_srcs(html, '파이썬-개발')
        assert '/images/파이썬-개발/photo.jpg' in result

    def test_local_path_src_unchanged_structure(self):
        # Already-local src still gets replaced (two-pass design: converter is called once)
        html = '<img src="/already/local.jpg">'
        result = _replace_img_srcs(html, 'slug')
        assert '/images/slug/local.jpg' in result


# ---------------------------------------------------------------------------
# _generate_frontmatter
# ---------------------------------------------------------------------------

class TestGenerateFrontmatter:
    def test_basic_output(self):
        post = _make_post()
        slug = 'test-post'
        result = _generate_frontmatter(post, slug)
        assert result.startswith('---\n')
        assert result.strip().endswith('---')

    def test_valid_yaml(self):
        post = _make_post()
        result = _generate_frontmatter(post, 'my-slug')
        inner = result[4:-4]  # strip leading/trailing ---\n
        parsed = yaml.safe_load(inner)
        assert isinstance(parsed, dict)

    def test_title_field(self):
        post = _make_post(title='My Post Title')
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['title'] == 'My Post Title'

    def test_date_format(self):
        post = _make_post(published_at=datetime(2024, 1, 15, 9, 30, 0))
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['date'] == '2024-01-15'

    def test_category_field(self):
        post = _make_post(category='Python')
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['category'] == 'Python'

    def test_tags_list(self):
        post = _make_post(tags=['python', 'django', 'web'])
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['tags'] == ['python', 'django', 'web']

    def test_slug_field(self):
        post = _make_post()
        result = _generate_frontmatter(post, 'my-custom-slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['slug'] == 'my-custom-slug'

    def test_original_url_field(self):
        url = 'https://myblog.tistory.com/42'
        post = _make_post(url=url)
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['original_url'] == url

    def test_title_with_colon_valid_yaml(self):
        post = _make_post(title='Python: A Guide')
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['title'] == 'Python: A Guide'

    def test_title_with_quotes_valid_yaml(self):
        post = _make_post(title='He said "hello"')
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['title'] == 'He said "hello"'

    def test_korean_title_unicode(self):
        post = _make_post(title='파이썬 개발')
        result = _generate_frontmatter(post, 'slug')
        assert '파이썬 개발' in result
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['title'] == '파이썬 개발'

    def test_empty_tags(self):
        post = _make_post(tags=[])
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        assert parsed['tags'] == []

    def test_all_required_fields_present(self):
        post = _make_post()
        result = _generate_frontmatter(post, 'slug')
        parsed = yaml.safe_load(result[4:-4])
        for field in ('title', 'date', 'category', 'tags', 'slug', 'original_url'):
            assert field in parsed, f'Missing field: {field}'


# ---------------------------------------------------------------------------
# convert_post — full pipeline
# ---------------------------------------------------------------------------

class TestConvertPost:
    def test_returns_string(self):
        post = _make_post()
        result = convert_post(post)
        assert isinstance(result, str)

    def test_starts_with_frontmatter(self):
        post = _make_post()
        result = convert_post(post)
        assert result.startswith('---\n')

    def test_frontmatter_followed_by_markdown(self):
        post = _make_post(content_html='<p>Hello world</p>')
        result = convert_post(post)
        # After closing ---, there should be markdown content
        assert '---\n' in result
        parts = result.split('---\n', 2)
        assert len(parts) >= 3

    def test_heading_style_atx(self):
        post = _make_post(content_html='<h1>Main Title</h1>')
        result = convert_post(post)
        assert '# Main Title' in result
        # Not setext-style (should not have === underline)
        assert '===' not in result

    def test_list_bullets_hyphen(self):
        post = _make_post(content_html='<ul><li>item1</li><li>item2</li></ul>')
        result = convert_post(post)
        assert '- item1' in result
        assert '- item2' in result

    def test_code_block_language_detected(self):
        html = '<pre><code class="language-python">print("hello")</code></pre>'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '```python' in result
        assert 'print("hello")' in result

    def test_code_block_no_language(self):
        html = '<pre><code>plain code</code></pre>'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '```\n' in result or '```' in result
        assert 'plain code' in result

    def test_tistory_image_tag_converted(self):
        html = '[##_Image|photo.jpg|300|200_##]'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '![' in result or '/images/' in result

    def test_tistory_code_tag_converted(self):
        html = '[##_Code|python|x = 1_##]'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '```python' in result
        assert 'x = 1' in result

    def test_image_src_replaced(self):
        html = '<img src="https://example.com/photo.jpg">'
        post = _make_post(content_html=html, title='My Post')
        result = convert_post(post)
        assert '/images/my-post/photo.jpg' in result
        assert 'example.com' not in result

    def test_slug_from_korean_title(self):
        post = _make_post(title='파이썬 개발 팁', content_html='<p>content</p>')
        result = convert_post(post)
        # Slug should appear in frontmatter
        assert '파이썬-개발-팁' in result

    def test_nbsp_paragraph_removed(self):
        html = '<p>content</p><p>&nbsp;</p><p>more content</p>'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '&nbsp;' not in result

    def test_consecutive_blank_lines_collapsed(self):
        # markdownify can produce multiple blank lines
        html = '<p>a</p><p>b</p><p>c</p>'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '\n\n\n' not in result

    def test_strong_preserved(self):
        post = _make_post(content_html='<p><strong>bold text</strong></p>')
        result = convert_post(post)
        assert '**bold text**' in result

    def test_link_preserved(self):
        post = _make_post(content_html='<p><a href="https://example.com">click</a></p>')
        result = convert_post(post)
        assert '[click](https://example.com)' in result

    def test_date_in_frontmatter(self):
        post = _make_post(published_at=datetime(2024, 6, 15, 12, 0, 0))
        result = convert_post(post)
        assert '2024-06-15' in result

    def test_blockquote_converted(self):
        post = _make_post(content_html='<blockquote>quote text</blockquote>')
        result = convert_post(post)
        assert '> quote text' in result or '>quote text' in result

    def test_h2_atx(self):
        post = _make_post(content_html='<h2>Section</h2>')
        result = convert_post(post)
        assert '## Section' in result

    def test_h3_atx(self):
        post = _make_post(content_html='<h3>Sub</h3>')
        result = convert_post(post)
        assert '### Sub' in result

    def test_code_bash_language(self):
        html = '<pre><code class="language-bash">echo hello</code></pre>'
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '```bash' in result

    def test_empty_content_produces_frontmatter(self):
        post = _make_post(content_html='')
        result = convert_post(post)
        assert result.startswith('---\n')

    def test_tags_in_frontmatter(self):
        post = _make_post(tags=['python', 'web'])
        result = convert_post(post)
        assert 'python' in result
        assert 'web' in result

    def test_original_url_in_frontmatter(self):
        url = 'https://myblog.tistory.com/42'
        post = _make_post(url=url)
        result = convert_post(post)
        assert url in result

    def test_em_preserved(self):
        post = _make_post(content_html='<p><em>italic</em></p>')
        result = convert_post(post)
        assert '*italic*' in result

    def test_ordered_list(self):
        post = _make_post(content_html='<ol><li>first</li><li>second</li></ol>')
        result = convert_post(post)
        assert '1.' in result or 'first' in result

    def test_multiple_code_blocks_different_languages(self):
        html = (
            '<pre><code class="language-python">x=1</code></pre>'
            '<pre><code class="language-javascript">var x=1</code></pre>'
        )
        post = _make_post(content_html=html)
        result = convert_post(post)
        assert '```python' in result
        assert '```javascript' in result
