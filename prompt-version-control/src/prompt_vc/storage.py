"""Storage layer: .prompt-vc/ directory management, YAML I/O, file discovery."""

import shutil
from pathlib import Path

import yaml

from prompt_vc.models import ConfigData, IndexData, VersionMeta

_STORE_DIR = ".prompt-vc"


def store_path(cwd: Path) -> Path:
    """Return the path to the .prompt-vc/ directory."""
    return cwd / _STORE_DIR


def is_initialized(cwd: Path) -> bool:
    """Return True if .prompt-vc/ exists in cwd."""
    return store_path(cwd).is_dir()


def ensure_store(cwd: Path) -> None:
    """Create .prompt-vc/ directory structure (snapshots/, bindings/).

    Idempotent — safe to call if already initialized.
    """
    store = store_path(cwd)
    store.mkdir(exist_ok=True)
    (store / "snapshots").mkdir(exist_ok=True)
    (store / "bindings").mkdir(exist_ok=True)


def read_yaml(path: Path) -> dict:
    """Read a YAML file and return its contents as a dict."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_yaml(path: Path, data: dict) -> None:
    """Write a dict to a YAML file."""
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def read_config(cwd: Path) -> ConfigData:
    """Read config.yaml and return a ConfigData instance."""
    data = read_yaml(store_path(cwd) / "config.yaml")
    return ConfigData(
        prompt_dir=data["prompt_dir"],
        file_pattern=data.get("file_pattern", "PROMPT_*.md"),
    )


def write_config(cwd: Path, config: ConfigData) -> None:
    """Write a ConfigData instance to config.yaml."""
    write_yaml(
        store_path(cwd) / "config.yaml",
        {
            "prompt_dir": config.prompt_dir,
            "file_pattern": config.file_pattern,
        },
    )


def _version_meta_to_dict(v: VersionMeta) -> dict:
    return {
        "version": v.version,
        "hash": v.hash,
        "message": v.message,
        "timestamp": v.timestamp,
        "files": v.files,
        "parent": v.parent,
    }


def _version_meta_from_dict(d: dict) -> VersionMeta:
    return VersionMeta(
        version=d["version"],
        hash=d["hash"],
        message=d["message"],
        timestamp=d["timestamp"],
        files=d.get("files") or {},
        parent=d.get("parent"),
    )


def read_index(cwd: Path) -> IndexData:
    """Read index.yaml and return an IndexData instance."""
    data = read_yaml(store_path(cwd) / "index.yaml")
    versions = [_version_meta_from_dict(v) for v in data.get("versions") or []]
    return IndexData(
        current_version=data.get("current_version"),
        versions=versions,
    )


def write_index(cwd: Path, index: IndexData) -> None:
    """Write an IndexData instance to index.yaml."""
    write_yaml(
        store_path(cwd) / "index.yaml",
        {
            "current_version": index.current_version,
            "versions": [_version_meta_to_dict(v) for v in index.versions],
        },
    )


def discover_prompts(prompt_dir: Path, file_pattern: str) -> list[Path]:
    """Return sorted list of files in prompt_dir matching file_pattern."""
    return sorted(prompt_dir.glob(file_pattern))


def copy_snapshot(src_files: list[Path], snapshot_dir: Path) -> None:
    """Copy src_files into snapshot_dir, preserving file contents.

    snapshot_dir is created if it does not exist.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for src in src_files:
        dst = snapshot_dir / src.name
        shutil.copy2(src, dst)
