"""bind command: attach benchmark run results to a prompt version."""

import json
from datetime import datetime, timezone
from pathlib import Path

from prompt_vc.models import BindingMeta
from prompt_vc.storage import is_initialized, read_index, store_path, write_yaml


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


class VersionNotFoundError(Exception):
    """Raised when the specified version does not exist."""


class InvalidResultError(Exception):
    """Raised when the result JSON is missing required fields or cannot be parsed."""


_REQUIRED_FIELDS = {"benchmark", "agent", "success", "test_pass_rate"}
_TOP_LEVEL_FIELDS = {"benchmark", "agent", "timestamp"}


def _next_run_id(bindings_dir: Path, version: str) -> int:
    """Return the next run number for a given version."""
    existing = list(bindings_dir.glob(f"{version}_run*.yaml"))
    if not existing:
        return 1
    run_nums = []
    for f in existing:
        try:
            run_num = int(f.stem.split("_run")[-1])
            run_nums.append(run_num)
        except (ValueError, IndexError):
            pass
    return max(run_nums) + 1 if run_nums else 1


def bind(cwd: Path, version: str, result_file: Path) -> BindingMeta:
    """Attach a benchmark run result to a prompt version.

    Args:
        cwd: Working directory containing .prompt-vc/ store.
        version: Version ID (e.g. "v1") to bind results to.
        result_file: Path to JSON file with benchmark run results.

    Returns:
        BindingMeta for the created binding.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
        VersionNotFoundError: If the version does not exist in the index.
        InvalidResultError: If the JSON file is missing required fields or cannot be parsed.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)
    version_ids = {v.version for v in index.versions}
    if version not in version_ids:
        raise VersionNotFoundError(f"Version '{version}' not found.")

    try:
        with open(result_file, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise InvalidResultError(f"Invalid JSON in {result_file}: {e}") from e

    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise InvalidResultError(
            f"Result JSON missing required fields: {sorted(missing)}"
        )

    timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()
    metrics = {k: v for k, v in data.items() if k not in _TOP_LEVEL_FIELDS}

    bindings_dir = store_path(cwd) / "bindings"
    run_num = _next_run_id(bindings_dir, version)

    meta = BindingMeta(
        version=version,
        benchmark=data["benchmark"],
        agent=data["agent"],
        timestamp=timestamp,
        metrics=metrics,
    )

    write_yaml(
        bindings_dir / f"{version}_run{run_num}.yaml",
        {
            "version": meta.version,
            "benchmark": meta.benchmark,
            "agent": meta.agent,
            "timestamp": meta.timestamp,
            "metrics": meta.metrics,
        },
    )

    return meta
