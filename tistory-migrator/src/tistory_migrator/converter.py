from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse

import markdownify
import yaml

from tistory_migrator.models import TistoryPost

logger = logging.getLogger(__name__)

# Korean Unicode ranges to preserve in slugs
_HANGUL_SYLLABLES = ('\uAC00', '\uD7A3')
_HANGUL_JAMO = ('\u1100', '\u11FF')
_HANGUL_COMPAT_JAMO = ('\u3130', '\u318F')


def _is_korean(char: str) -> bool:
    return (
        _HANGUL_SYLLABLES[0] <= char <= _HANGUL_SYLLABLES[1]
        or _HANGUL_JAMO[0] <= char <= _HANGUL_JAMO[1]
        or _HANGUL_COMPAT_JAMO[0] <= char <= _HANGUL_COMPAT_JAMO[1]
    )


def generate_slug(title: str) -> str:
    """Generate a URL slug from a post title.

    Korean syllables are preserved as Unicode. ASCII letters are lowercased.
    Spaces become hyphens. Special characters are removed. Consecutive hyphens
    are collapsed and leading/trailing hyphens are stripped.
    """
    parts: list[str] = []
    for char in title:
        if char == ' ':
            parts.append('-')
        elif char.isascii():
            if char.isalnum():
                parts.append(char.lower())
            # else: skip ASCII special characters
        elif _is_korean(char):
            parts.append(char)
        # else: skip non-ASCII, non-Korean characters

    slug = ''.join(parts)
    slug = re.sub(r'-+', '-', slug)  # collapse consecutive hyphens
    slug = slug.strip('-')           # strip leading/trailing hyphens
    return slug


def process_tistory_tags(html: str) -> str:
    """Convert Tistory custom [##_..._##] tags to standard HTML."""
    # Image tags: [##_Image|filename.jpg|width|height|..._##]
    html = re.sub(
        r'\[##_Image\|([^|]+)\|.*?_##\]',
        lambda m: f'<img src="{m.group(1)}">',
        html,
        flags=re.DOTALL,
    )

    # Code tags with language: [##_Code|language|code_##]
    def _replace_code(m: re.Match) -> str:
        lang = m.group(1).strip()
        code = m.group(2)
        if lang:
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
        return f'<pre><code>{code}</code></pre>'

    html = re.sub(
        r'\[##_Code\|([^|]*)\|(.*?)_##\]',
        _replace_code,
        html,
        flags=re.DOTALL,
    )

    # CodeBlock tags (no language): [##_CodeBlock|code_##]
    html = re.sub(
        r'\[##_CodeBlock\|(.*?)_##\]',
        lambda m: f'<pre><code>{m.group(1)}</code></pre>',
        html,
        flags=re.DOTALL,
    )

    # Unknown custom tags: strip tag syntax but preserve inner text
    def _strip_unknown(m: re.Match) -> str:
        inner = m.group(1)
        logger.warning('Unrecognized Tistory custom tag stripped: %s...', m.group(0)[:40])
        return inner

    html = re.sub(r'\[##_[^|_]+\|(.*?)_##\]', _strip_unknown, html, flags=re.DOTALL)

    return html


def _url_to_filename(url: str) -> str:
    """Extract a filename from an image URL."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    return filename if filename else 'image.jpg'


def _replace_img_srcs(html: str, slug: str) -> str:
    """Replace <img> src attributes with deterministic local paths.

    Output path: /images/{slug}/{filename}
    """
    def _replace_tag(m: re.Match) -> str:
        tag = m.group(0)
        src_m = re.search(r'(src=["\'])([^"\']+)(["\'])', tag, re.IGNORECASE)
        if src_m:
            src = src_m.group(2)
            filename = _url_to_filename(src)
            local_path = f'/images/{slug}/{filename}'
            tag = tag[:src_m.start(2)] + local_path + tag[src_m.end(2):]
        return tag

    return re.sub(r'<img[^>]+>', _replace_tag, html, flags=re.DOTALL | re.IGNORECASE)


def _generate_frontmatter(post: TistoryPost, slug: str) -> str:
    """Generate YAML frontmatter block for a post."""
    data = {
        'title': post.title,
        'date': post.published_at.strftime('%Y-%m-%d'),
        'category': post.category,
        'tags': post.tags,
        'slug': slug,
        'original_url': post.url,
    }
    yaml_str = yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f'---\n{yaml_str}---\n'


def _code_language_callback(el) -> str:
    """Extract programming language from <pre>'s child <code class='language-xxx'>."""
    code = el.find('code')
    if code:
        classes = code.get('class') or []
        for cls in classes:
            if cls.startswith('language-'):
                return cls[len('language-'):]
    return ''


def convert_post(post: TistoryPost) -> str:
    """Convert a TistoryPost to a frontmatter + Markdown string.

    Pipeline:
      1. Process Tistory custom tags → standard HTML
      2. Replace image src URLs with local paths
      3. Strip empty &nbsp; paragraphs
      4. Convert HTML → Markdown (ATX headings, hyphen bullets, language-aware fences)
      5. Collapse excess blank lines
      6. Prepend YAML frontmatter
    """
    slug = generate_slug(post.title)

    html = process_tistory_tags(post.content_html)
    html = _replace_img_srcs(html, slug)

    # Remove empty &nbsp; paragraphs common in Tistory exports
    html = re.sub(r'<p>\s*&nbsp;\s*</p>', '', html, flags=re.IGNORECASE)

    markdown = markdownify.markdownify(
        html,
        heading_style='ATX',
        bullets='-',
        code_language_callback=_code_language_callback,
    )

    # Collapse three or more consecutive blank lines to two
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    markdown = markdown.strip()

    frontmatter = _generate_frontmatter(post, slug)
    return frontmatter + '\n' + markdown
