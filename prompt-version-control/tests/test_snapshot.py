"""Tests for the snapshot command."""

from pathlib import Path

import pytest

from prompt_vc.commands.init import init
from prompt_vc.commands.snapshot import NoChangesError, NotInitializedError, snapshot
from prompt_vc.hashing import hash_file, hash_version
from prompt_vc.storage import read_index, read_yaml, store_path


def _make_prompt_dir(base: Path) -> Path:
    """Create a prompts/ subdirectory and return its path."""
    d = base / "prompts"
    d.mkdir()
    return d


def _init_with_prompts(tmp_path: Path) -> Path:
    """Init store and return prompt_dir with one file."""
    pdir = _make_prompt_dir(tmp_path)
    (pdir / "PROMPT_system.md").write_text("system prompt v1")
    init(tmp_path, pdir)
    return pdir


# ── first snapshot ──────────────────────────────────────────────────────────


def test_first_snapshot_version_id(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    meta = snapshot(tmp_path, "initial")
    assert meta.version == "v1"


def test_first_snapshot_parent_is_none(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    meta = snapshot(tmp_path, "initial")
    assert meta.parent is None


def test_first_snapshot_message_stored(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    meta = snapshot(tmp_path, "my first message")
    assert meta.message == "my first message"


def test_first_snapshot_files_key_present(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    meta = snapshot(tmp_path, "initial")
    assert "PROMPT_system.md" in meta.files


def test_first_snapshot_directory_created(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "initial")
    snap_dir = store_path(tmp_path) / "snapshots" / "v1"
    assert snap_dir.is_dir()


def test_first_snapshot_file_copied(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "initial")
    snap_dir = store_path(tmp_path) / "snapshots" / "v1"
    assert (snap_dir / "PROMPT_system.md").exists()


def test_first_snapshot_metadata_yaml_created(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "initial")
    snap_dir = store_path(tmp_path) / "snapshots" / "v1"
    assert (snap_dir / "metadata.yaml").exists()


# ── index updates ───────────────────────────────────────────────────────────


def test_first_snapshot_updates_current_version(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "initial")
    index = read_index(tmp_path)
    assert index.current_version == "v1"


def test_first_snapshot_appended_to_index_versions(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "initial")
    index = read_index(tmp_path)
    assert len(index.versions) == 1
    assert index.versions[0].version == "v1"


# ── sequential snapshots ────────────────────────────────────────────────────


def test_second_snapshot_version_id(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("system prompt v2")
    meta2 = snapshot(tmp_path, "second")
    assert meta2.version == "v2"


def test_second_snapshot_parent_is_v1(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("system prompt v2")
    meta2 = snapshot(tmp_path, "second")
    assert meta2.parent == "v1"


def test_sequential_snapshots_index_has_two_versions(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("system prompt v2")
    snapshot(tmp_path, "second")
    index = read_index(tmp_path)
    assert len(index.versions) == 2
    assert index.current_version == "v2"


def test_sequential_snapshots_separate_dirs(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("system prompt v2")
    snapshot(tmp_path, "second")
    assert (store_path(tmp_path) / "snapshots" / "v1").is_dir()
    assert (store_path(tmp_path) / "snapshots" / "v2").is_dir()


def test_third_snapshot_parent_chain(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("v2")
    snapshot(tmp_path, "second")
    (pdir / "PROMPT_system.md").write_text("v3")
    meta3 = snapshot(tmp_path, "third")
    assert meta3.version == "v3"
    assert meta3.parent == "v2"


# ── no-change detection ─────────────────────────────────────────────────────


def test_no_change_raises_no_changes_error(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    with pytest.raises(NoChangesError):
        snapshot(tmp_path, "identical content")


def test_no_change_does_not_create_new_version(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    try:
        snapshot(tmp_path, "identical content")
    except NoChangesError:
        pass
    index = read_index(tmp_path)
    assert len(index.versions) == 1


def test_content_change_after_no_change_succeeds(tmp_path: Path) -> None:
    pdir = _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    (pdir / "PROMPT_system.md").write_text("changed!")
    meta2 = snapshot(tmp_path, "changed")
    assert meta2.version == "v2"


# ── hash correctness ────────────────────────────────────────────────────────


def test_file_hash_matches_hash_file(tmp_path: Path) -> None:
    pdir = _make_prompt_dir(tmp_path)
    f = pdir / "PROMPT_system.md"
    f.write_text("known content for hashing")
    init(tmp_path, pdir)
    meta = snapshot(tmp_path, "test")
    assert meta.files["PROMPT_system.md"] == hash_file(f)


def test_version_hash_matches_hash_version(tmp_path: Path) -> None:
    pdir = _make_prompt_dir(tmp_path)
    f = pdir / "PROMPT_system.md"
    f.write_text("known content for hashing")
    init(tmp_path, pdir)
    meta = snapshot(tmp_path, "test")
    expected = hash_version({"PROMPT_system.md": hash_file(f)})
    assert meta.hash == expected


def test_multiple_files_hashed(tmp_path: Path) -> None:
    pdir = _make_prompt_dir(tmp_path)
    (pdir / "PROMPT_system.md").write_text("system")
    (pdir / "PROMPT_user.md").write_text("user")
    init(tmp_path, pdir)
    meta = snapshot(tmp_path, "multi")
    assert "PROMPT_system.md" in meta.files
    assert "PROMPT_user.md" in meta.files
    assert len(meta.files) == 2


# ── metadata.yaml validation ─────────────────────────────────────────────────


def test_metadata_yaml_version_field(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "msg")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert data["version"] == "v1"


def test_metadata_yaml_message_field(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "the message")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert data["message"] == "the message"


def test_metadata_yaml_parent_none_for_first(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert data.get("parent") is None


def test_metadata_yaml_has_timestamp(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert data.get("timestamp") is not None


def test_metadata_yaml_has_hash(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert data.get("hash") is not None


def test_metadata_yaml_has_files(tmp_path: Path) -> None:
    _init_with_prompts(tmp_path)
    snapshot(tmp_path, "first")
    data = read_yaml(store_path(tmp_path) / "snapshots" / "v1" / "metadata.yaml")
    assert "files" in data


# ── not-initialized guard ────────────────────────────────────────────────────


def test_snapshot_not_initialized_raises(tmp_path: Path) -> None:
    with pytest.raises(NotInitializedError):
        snapshot(tmp_path, "test")
