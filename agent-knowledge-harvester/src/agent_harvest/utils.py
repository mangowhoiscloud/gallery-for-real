from __future__ import annotations

import re


def slugify(text: str, max_length: int = 60) -> str:
    """Lowercase text, replace non-alphanumeric chars with hyphens, collapse
    multiple hyphens, strip leading/trailing hyphens, truncate to max_length."""
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_length]


def make_unique_id(slug: str, existing_ids: set[str]) -> str:
    """Return slug unchanged if not in existing_ids, otherwise append -2, -3, etc."""
    if slug not in existing_ids:
        return slug
    counter = 2
    while True:
        candidate = f"{slug}-{counter}"
        if candidate not in existing_ids:
            return candidate
        counter += 1
