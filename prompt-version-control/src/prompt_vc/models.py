"""Data models for prompt-version-control."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class VersionMeta:
    """Metadata for a single snapshot version."""

    version: str
    hash: str
    message: str
    timestamp: str
    files: dict[str, str]  # filename -> sha256 hash
    parent: Optional[str] = None


@dataclass
class BindingMeta:
    """Binding of a prompt version to benchmark run results."""

    version: str
    benchmark: str
    agent: str
    timestamp: str
    metrics: dict  # flexible metrics (success, test_pass_rate, etc.)


@dataclass
class IndexData:
    """Top-level index tracking all versions."""

    current_version: Optional[str]
    versions: list[VersionMeta] = field(default_factory=list)


@dataclass
class ConfigData:
    """Repository configuration stored in config.yaml."""

    prompt_dir: str
    file_pattern: str = "PROMPT_*.md"
