from __future__ import annotations

import json
import logging
from pathlib import Path

from tistory_migrator.models import MigrationResult

logger = logging.getLogger(__name__)


class Writer:
    def __init__(self, output_dir: str | Path, dry_run: bool = False) -> None:
        self.output_dir = Path(output_dir)
        self.posts_dir = self.output_dir / "posts"
        self.images_dir = self.output_dir / "images"
        self.dry_run = dry_run

    def setup_directories(self) -> None:
        if self.dry_run:
            return
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def write_post(self, slug: str, content: str) -> bool:
        if self.dry_run:
            return True
        post_path = self.posts_dir / f"{slug}.md"
        try:
            post_path.write_text(content, encoding="utf-8")
            return True
        except OSError as e:
            logger.error("Failed to write post %s: %s", slug, e)
            return False

    def write_metadata(self, result: MigrationResult) -> bool:
        if self.dry_run:
            return True
        metadata_path = self.output_dir / "metadata.json"
        try:
            metadata_path.write_text(
                json.dumps(result.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return True
        except OSError as e:
            logger.error("Failed to write metadata.json: %s", e)
            return False
