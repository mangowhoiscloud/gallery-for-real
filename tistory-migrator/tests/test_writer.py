from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from tistory_migrator.models import FailedPost, MigrationResult
from tistory_migrator.writer import Writer


def make_result(**kwargs) -> MigrationResult:
    defaults = dict(
        blog="test.tistory.com",
        strategy="api",
        migrated_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        total_posts=5,
        converted_posts=4,
        failed_posts=[],
        categories=["Python", "Dev"],
        tags=["python", "tip"],
        total_images=10,
        failed_images=1,
        duration_seconds=3.5,
    )
    defaults.update(kwargs)
    return MigrationResult(**defaults)


# ---------------------------------------------------------------------------
# setup_directories
# ---------------------------------------------------------------------------


def test_setup_directories_creates_posts_and_images(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    w.setup_directories()
    assert w.posts_dir.is_dir()
    assert w.images_dir.is_dir()


def test_setup_directories_creates_nested_output_dir(tmp_path: Path) -> None:
    w = Writer(tmp_path / "deep" / "nested" / "out")
    w.setup_directories()
    assert w.output_dir.is_dir()


def test_setup_directories_is_idempotent(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    w.setup_directories()
    w.setup_directories()  # should not raise
    assert w.posts_dir.is_dir()


def test_setup_directories_dry_run_skips_creation(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out", dry_run=True)
    w.setup_directories()
    assert not (tmp_path / "out").exists()


def test_setup_directories_propagates_oserror(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    with patch.object(Path, "mkdir", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            w.setup_directories()


# ---------------------------------------------------------------------------
# public attributes
# ---------------------------------------------------------------------------


def test_output_dir_attribute(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    assert w.output_dir == tmp_path / "out"


def test_posts_dir_attribute(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    assert w.posts_dir == tmp_path / "out" / "posts"


def test_images_dir_attribute(tmp_path: Path) -> None:
    w = Writer(tmp_path / "out")
    assert w.images_dir == tmp_path / "out" / "images"


def test_accepts_string_path(tmp_path: Path) -> None:
    w = Writer(str(tmp_path / "out"))
    assert isinstance(w.output_dir, Path)


# ---------------------------------------------------------------------------
# write_post
# ---------------------------------------------------------------------------


def test_write_post_creates_md_file(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    result = w.write_post("2024-01-15-hello-world", "# Hello")
    assert result is True
    assert (tmp_path / "posts" / "2024-01-15-hello-world.md").exists()


def test_write_post_content_preserved(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    content = "---\ntitle: Test\n---\n\n# Body\n"
    w.write_post("2024-01-15-test", content)
    assert (tmp_path / "posts" / "2024-01-15-test.md").read_text(encoding="utf-8") == content


def test_write_post_korean_content(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    korean = "---\ntitle: 파이썬 팁\n---\n\n한국어 내용입니다.\n"
    w.write_post("2024-01-15-파이썬-팁", korean)
    assert (tmp_path / "posts" / "2024-01-15-파이썬-팁.md").read_text(encoding="utf-8") == korean


def test_write_post_returns_false_on_oserror(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    with patch.object(Path, "write_text", side_effect=OSError("no space")):
        result = w.write_post("2024-01-15-slug", "content")
    assert result is False


def test_write_post_does_not_raise_on_oserror(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    with patch.object(Path, "write_text", side_effect=OSError("no space")):
        # must not raise
        w.write_post("2024-01-15-slug", "content")


def test_write_post_dry_run_returns_true_without_writing(tmp_path: Path) -> None:
    w = Writer(tmp_path, dry_run=True)
    result = w.write_post("2024-01-15-slug", "content")
    assert result is True
    assert not (tmp_path / "posts" / "2024-01-15-slug.md").exists()


def test_write_post_uses_slug_as_filename(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    w.setup_directories()
    w.write_post("2026-03-24-my-post", "# content")
    assert (tmp_path / "posts" / "2026-03-24-my-post.md").exists()


# ---------------------------------------------------------------------------
# write_metadata
# ---------------------------------------------------------------------------


def test_write_metadata_creates_file(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result()
    assert w.write_metadata(result) is True
    assert (tmp_path / "metadata.json").exists()


def test_write_metadata_valid_json(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result()
    w.write_metadata(result)
    data = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert data["blog"] == "test.tistory.com"


def test_write_metadata_korean_utf8(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result(blog="한국어.tistory.com", tags=["파이썬"])
    w.write_metadata(result)
    raw = (tmp_path / "metadata.json").read_bytes().decode("utf-8")
    assert "한국어" in raw
    assert "파이썬" in raw
    assert "\\u" not in raw


def test_write_metadata_no_unicode_escapes(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result(categories=["개발"])
    w.write_metadata(result)
    raw = (tmp_path / "metadata.json").read_text(encoding="utf-8")
    assert "개발" in raw


def test_write_metadata_failed_posts_serialized(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    fp = FailedPost(id="42", title="실패 포스트", reason="404")
    result = make_result(failed_posts=[fp])
    w.write_metadata(result)
    data = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert data["failed_posts"][0]["id"] == "42"
    assert data["failed_posts"][0]["title"] == "실패 포스트"


def test_write_metadata_iso_timestamp(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result()
    w.write_metadata(result)
    data = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    assert "2024-01-15" in data["migrated_at"]


def test_write_metadata_returns_false_on_oserror(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result()
    with patch.object(Path, "write_text", side_effect=OSError("disk full")):
        assert w.write_metadata(result) is False


def test_write_metadata_dry_run_returns_true_without_writing(tmp_path: Path) -> None:
    w = Writer(tmp_path, dry_run=True)
    result = make_result()
    assert w.write_metadata(result) is True
    assert not (tmp_path / "metadata.json").exists()


def test_write_metadata_all_fields_present(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    result = make_result()
    w.write_metadata(result)
    data = json.loads((tmp_path / "metadata.json").read_text(encoding="utf-8"))
    for key in [
        "blog", "strategy", "migrated_at", "total_posts", "converted_posts",
        "failed_posts", "categories", "tags", "total_images", "failed_images",
        "duration_seconds",
    ]:
        assert key in data


# ---------------------------------------------------------------------------
# dry_run attribute
# ---------------------------------------------------------------------------


def test_dry_run_false_by_default(tmp_path: Path) -> None:
    w = Writer(tmp_path)
    assert w.dry_run is False


def test_dry_run_true_when_set(tmp_path: Path) -> None:
    w = Writer(tmp_path, dry_run=True)
    assert w.dry_run is True
