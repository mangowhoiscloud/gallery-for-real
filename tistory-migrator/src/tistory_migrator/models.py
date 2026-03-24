from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TistoryPost:
    id: str
    title: str
    content_html: str
    category: str
    tags: list[str]
    published_at: datetime
    url: str
    images: list[str]


@dataclass
class FailedPost:
    id: str
    title: str
    reason: str


@dataclass
class MigrationResult:
    blog: str
    strategy: str
    migrated_at: datetime
    total_posts: int
    converted_posts: int
    failed_posts: list[FailedPost]
    categories: list[str]
    tags: list[str]
    total_images: int
    failed_images: int
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "blog": self.blog,
            "strategy": self.strategy,
            "migrated_at": self.migrated_at.isoformat(),
            "total_posts": self.total_posts,
            "converted_posts": self.converted_posts,
            "failed_posts": [
                {"id": fp.id, "title": fp.title, "reason": fp.reason}
                for fp in self.failed_posts
            ],
            "categories": self.categories,
            "tags": self.tags,
            "total_images": self.total_images,
            "failed_images": self.failed_images,
            "duration_seconds": self.duration_seconds,
        }
