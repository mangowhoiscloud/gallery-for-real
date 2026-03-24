"""Tests for prompt_vc data models."""

from prompt_vc.models import BindingMeta, ConfigData, IndexData, VersionMeta


# ---------------------------------------------------------------------------
# VersionMeta
# ---------------------------------------------------------------------------


def test_version_meta_all_fields() -> None:
    vm = VersionMeta(
        version="v1",
        hash="abc123def456",
        message="Initial version",
        timestamp="2026-03-20T14:30:00+09:00",
        files={"PROMPT_system.md": "e5f6a7b8", "PROMPT_user.md": "c1d2e3f4"},
        parent=None,
    )
    assert vm.version == "v1"
    assert vm.hash == "abc123def456"
    assert vm.message == "Initial version"
    assert vm.timestamp == "2026-03-20T14:30:00+09:00"
    assert vm.files == {"PROMPT_system.md": "e5f6a7b8", "PROMPT_user.md": "c1d2e3f4"}
    assert vm.parent is None


def test_version_meta_parent_optional_defaults_none() -> None:
    vm = VersionMeta(
        version="v1",
        hash="aaa",
        message="msg",
        timestamp="ts",
        files={},
    )
    assert vm.parent is None


def test_version_meta_with_parent() -> None:
    vm = VersionMeta(
        version="v2",
        hash="bbb",
        message="second",
        timestamp="ts2",
        files={"PROMPT_system.md": "hash2"},
        parent="v1",
    )
    assert vm.parent == "v1"


def test_version_meta_empty_files() -> None:
    vm = VersionMeta(version="v1", hash="h", message="m", timestamp="t", files={})
    assert vm.files == {}


def test_version_meta_multiple_files() -> None:
    files = {
        "PROMPT_system.md": "hash1",
        "PROMPT_user.md": "hash2",
        "PROMPT_tools.md": "hash3",
    }
    vm = VersionMeta(version="v1", hash="combined", message="m", timestamp="t", files=files)
    assert len(vm.files) == 3
    assert vm.files["PROMPT_tools.md"] == "hash3"


# ---------------------------------------------------------------------------
# BindingMeta
# ---------------------------------------------------------------------------


def test_binding_meta_all_fields() -> None:
    bm = BindingMeta(
        version="v3",
        benchmark="word-counter",
        agent="claude",
        timestamp="2026-03-20T15:00:00+09:00",
        metrics={
            "success": True,
            "test_pass_rate": 1.0,
            "total_tests": 144,
            "total_iterations": 11,
            "total_time_seconds": 2220,
            "estimated_cost": 3.06,
        },
    )
    assert bm.version == "v3"
    assert bm.benchmark == "word-counter"
    assert bm.agent == "claude"
    assert bm.timestamp == "2026-03-20T15:00:00+09:00"
    assert bm.metrics["success"] is True
    assert bm.metrics["test_pass_rate"] == 1.0
    assert bm.metrics["total_tests"] == 144


def test_binding_meta_minimal_metrics() -> None:
    bm = BindingMeta(
        version="v1",
        benchmark="bench",
        agent="agent",
        timestamp="ts",
        metrics={"success": False, "test_pass_rate": 0.0},
    )
    assert bm.metrics["success"] is False


def test_binding_meta_extra_metrics_preserved() -> None:
    """Any extra fields in metrics dict are preserved (no schema enforcement)."""
    bm = BindingMeta(
        version="v1",
        benchmark="b",
        agent="a",
        timestamp="t",
        metrics={"success": True, "test_pass_rate": 0.8, "custom_field": "hello"},
    )
    assert bm.metrics["custom_field"] == "hello"


# ---------------------------------------------------------------------------
# IndexData
# ---------------------------------------------------------------------------


def test_index_data_empty() -> None:
    idx = IndexData(current_version=None)
    assert idx.current_version is None
    assert idx.versions == []


def test_index_data_with_versions() -> None:
    vm = VersionMeta(version="v1", hash="h", message="m", timestamp="t", files={})
    idx = IndexData(current_version="v1", versions=[vm])
    assert idx.current_version == "v1"
    assert len(idx.versions) == 1
    assert idx.versions[0].version == "v1"


def test_index_data_versions_ordered() -> None:
    v1 = VersionMeta(version="v1", hash="h1", message="m1", timestamp="t1", files={})
    v2 = VersionMeta(version="v2", hash="h2", message="m2", timestamp="t2", files={}, parent="v1")
    idx = IndexData(current_version="v2", versions=[v1, v2])
    assert idx.versions[0].version == "v1"
    assert idx.versions[1].version == "v2"


def test_index_data_current_version_none_means_empty() -> None:
    idx = IndexData(current_version=None, versions=[])
    assert idx.current_version is None
    assert idx.versions == []


# ---------------------------------------------------------------------------
# ConfigData
# ---------------------------------------------------------------------------


def test_config_data_defaults() -> None:
    cfg = ConfigData(prompt_dir="./prompts")
    assert cfg.prompt_dir == "./prompts"
    assert cfg.file_pattern == "PROMPT_*.md"


def test_config_data_custom_file_pattern() -> None:
    cfg = ConfigData(prompt_dir="/abs/path", file_pattern="*.md")
    assert cfg.prompt_dir == "/abs/path"
    assert cfg.file_pattern == "*.md"


def test_config_data_prompt_dir_stored_as_given() -> None:
    """prompt_dir is stored verbatim — no normalization in the model."""
    cfg = ConfigData(prompt_dir="../relative/path")
    assert cfg.prompt_dir == "../relative/path"
