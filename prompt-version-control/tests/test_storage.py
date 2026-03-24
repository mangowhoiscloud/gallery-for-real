"""Tests for storage layer (YAML I/O, directory ops, file discovery, snapshot copy)."""

from pathlib import Path

from prompt_vc.models import ConfigData, IndexData, VersionMeta
from prompt_vc.storage import (
    copy_snapshot,
    discover_prompts,
    ensure_store,
    is_initialized,
    read_config,
    read_index,
    read_yaml,
    store_path,
    write_config,
    write_index,
    write_yaml,
)


# ── store_path / is_initialized / ensure_store ─────────────────────────────


def test_store_path_returns_dot_prompt_vc(tmp_path: Path) -> None:
    assert store_path(tmp_path) == tmp_path / ".prompt-vc"


def test_is_initialized_false_before_init(tmp_path: Path) -> None:
    assert not is_initialized(tmp_path)


def test_is_initialized_true_after_ensure_store(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    assert is_initialized(tmp_path)


def test_ensure_store_creates_snapshots_and_bindings(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    assert (tmp_path / ".prompt-vc" / "snapshots").is_dir()
    assert (tmp_path / ".prompt-vc" / "bindings").is_dir()


def test_ensure_store_is_idempotent(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    ensure_store(tmp_path)  # should not raise
    assert is_initialized(tmp_path)


# ── read_yaml / write_yaml ──────────────────────────────────────────────────


def test_write_and_read_yaml_round_trip(tmp_path: Path) -> None:
    data = {"key": "value", "number": 42, "nested": {"a": 1}}
    path = tmp_path / "data.yaml"
    write_yaml(path, data)
    assert read_yaml(path) == data


def test_write_yaml_preserves_unicode(tmp_path: Path) -> None:
    data = {"message": "Socratic 질문 개선", "emoji": "✅"}
    path = tmp_path / "unicode.yaml"
    write_yaml(path, data)
    assert read_yaml(path) == data


def test_read_yaml_empty_file_returns_empty_dict(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    assert read_yaml(path) == {}


# ── read_config / write_config ──────────────────────────────────────────────


def test_write_and_read_config_round_trip(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    config = ConfigData(prompt_dir="./prompts", file_pattern="PROMPT_*.md")
    write_config(tmp_path, config)
    result = read_config(tmp_path)
    assert result.prompt_dir == "./prompts"
    assert result.file_pattern == "PROMPT_*.md"


def test_config_default_file_pattern(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    # Write config without file_pattern to test default
    write_yaml(
        store_path(tmp_path) / "config.yaml",
        {"prompt_dir": "./prompts"},
    )
    result = read_config(tmp_path)
    assert result.file_pattern == "PROMPT_*.md"


def test_config_custom_file_pattern(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    config = ConfigData(prompt_dir="./src", file_pattern="*.md")
    write_config(tmp_path, config)
    result = read_config(tmp_path)
    assert result.file_pattern == "*.md"
    assert result.prompt_dir == "./src"


# ── read_index / write_index ────────────────────────────────────────────────


def test_write_and_read_empty_index(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    index = IndexData(current_version=None, versions=[])
    write_index(tmp_path, index)
    result = read_index(tmp_path)
    assert result.current_version is None
    assert result.versions == []


def test_write_and_read_index_with_version(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    v1 = VersionMeta(
        version="v1",
        hash="abc123",
        message="Initial version",
        timestamp="2026-03-24T15:00:00+09:00",
        files={"PROMPT_system.md": "def456"},
        parent=None,
    )
    index = IndexData(current_version="v1", versions=[v1])
    write_index(tmp_path, index)
    result = read_index(tmp_path)
    assert result.current_version == "v1"
    assert len(result.versions) == 1
    r = result.versions[0]
    assert r.version == "v1"
    assert r.hash == "abc123"
    assert r.message == "Initial version"
    assert r.files == {"PROMPT_system.md": "def456"}
    assert r.parent is None


def test_write_and_read_index_with_multiple_versions(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    v1 = VersionMeta(
        version="v1",
        hash="aaa",
        message="First",
        timestamp="2026-03-24T10:00:00+09:00",
        files={"PROMPT_system.md": "h1"},
        parent=None,
    )
    v2 = VersionMeta(
        version="v2",
        hash="bbb",
        message="Second",
        timestamp="2026-03-24T11:00:00+09:00",
        files={"PROMPT_system.md": "h2"},
        parent="v1",
    )
    index = IndexData(current_version="v2", versions=[v1, v2])
    write_index(tmp_path, index)
    result = read_index(tmp_path)
    assert result.current_version == "v2"
    assert len(result.versions) == 2
    assert result.versions[1].parent == "v1"


def test_index_version_meta_files_dict_round_trip(tmp_path: Path) -> None:
    ensure_store(tmp_path)
    files = {
        "PROMPT_system.md": "sha1",
        "PROMPT_user.md": "sha2",
        "PROMPT_tools.md": "sha3",
    }
    v1 = VersionMeta(
        version="v1",
        hash="xxx",
        message="Multi-file",
        timestamp="2026-03-24T12:00:00+09:00",
        files=files,
        parent=None,
    )
    write_index(tmp_path, IndexData(current_version="v1", versions=[v1]))
    result = read_index(tmp_path)
    assert result.versions[0].files == files


# ── discover_prompts ────────────────────────────────────────────────────────


def test_discover_prompts_returns_matching_files(tmp_path: Path) -> None:
    (tmp_path / "PROMPT_system.md").write_text("system")
    (tmp_path / "PROMPT_user.md").write_text("user")
    (tmp_path / "README.md").write_text("readme")
    found = discover_prompts(tmp_path, "PROMPT_*.md")
    names = [p.name for p in found]
    assert "PROMPT_system.md" in names
    assert "PROMPT_user.md" in names
    assert "README.md" not in names


def test_discover_prompts_returns_sorted(tmp_path: Path) -> None:
    (tmp_path / "PROMPT_z.md").write_text("z")
    (tmp_path / "PROMPT_a.md").write_text("a")
    (tmp_path / "PROMPT_m.md").write_text("m")
    found = discover_prompts(tmp_path, "PROMPT_*.md")
    names = [p.name for p in found]
    assert names == sorted(names)


def test_discover_prompts_empty_dir_returns_empty(tmp_path: Path) -> None:
    assert discover_prompts(tmp_path, "PROMPT_*.md") == []


def test_discover_prompts_custom_pattern(tmp_path: Path) -> None:
    (tmp_path / "system.txt").write_text("txt")
    (tmp_path / "user.md").write_text("md")
    found = discover_prompts(tmp_path, "*.txt")
    assert len(found) == 1
    assert found[0].name == "system.txt"


# ── copy_snapshot ───────────────────────────────────────────────────────────


def test_copy_snapshot_creates_destination_dir(tmp_path: Path) -> None:
    src_dir = tmp_path / "prompts"
    src_dir.mkdir()
    f = src_dir / "PROMPT_system.md"
    f.write_text("hello")
    dst_dir = tmp_path / ".prompt-vc" / "snapshots" / "v1"
    copy_snapshot([f], dst_dir)
    assert dst_dir.is_dir()


def test_copy_snapshot_preserves_content(tmp_path: Path) -> None:
    src_dir = tmp_path / "prompts"
    src_dir.mkdir()
    content = "# System Prompt\n\nDo the thing.\n"
    f = src_dir / "PROMPT_system.md"
    f.write_text(content, encoding="utf-8")
    dst_dir = tmp_path / ".prompt-vc" / "snapshots" / "v1"
    copy_snapshot([f], dst_dir)
    assert (dst_dir / "PROMPT_system.md").read_text(encoding="utf-8") == content


def test_copy_snapshot_multiple_files(tmp_path: Path) -> None:
    src_dir = tmp_path / "prompts"
    src_dir.mkdir()
    files = []
    for name in ["PROMPT_system.md", "PROMPT_user.md", "PROMPT_tools.md"]:
        p = src_dir / name
        p.write_text(f"content of {name}")
        files.append(p)
    dst_dir = tmp_path / "snap"
    copy_snapshot(files, dst_dir)
    for name in ["PROMPT_system.md", "PROMPT_user.md", "PROMPT_tools.md"]:
        assert (dst_dir / name).exists()


def test_copy_snapshot_does_not_modify_source(tmp_path: Path) -> None:
    src_dir = tmp_path / "prompts"
    src_dir.mkdir()
    f = src_dir / "PROMPT_system.md"
    original = "original content"
    f.write_text(original)
    copy_snapshot([f], tmp_path / "snap")
    assert f.read_text() == original


def test_copy_snapshot_unicode_content(tmp_path: Path) -> None:
    src_dir = tmp_path / "prompts"
    src_dir.mkdir()
    content = "Socratic 질문 개선\n✅ Done\n"
    f = src_dir / "PROMPT_system.md"
    f.write_text(content, encoding="utf-8")
    dst_dir = tmp_path / "snap"
    copy_snapshot([f], dst_dir)
    assert (dst_dir / "PROMPT_system.md").read_text(encoding="utf-8") == content
