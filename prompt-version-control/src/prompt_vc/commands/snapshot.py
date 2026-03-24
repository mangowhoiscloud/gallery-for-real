"""snapshot command: create a versioned snapshot of prompt files."""

from datetime import datetime, timezone
from pathlib import Path

from prompt_vc.hashing import hash_file, hash_version
from prompt_vc.models import VersionMeta
from prompt_vc.storage import (
    copy_snapshot,
    discover_prompts,
    is_initialized,
    read_config,
    read_index,
    store_path,
    write_index,
    write_yaml,
)


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


class NoChangesError(Exception):
    """Raised when no file content changed since the last snapshot."""


def snapshot(cwd: Path, message: str) -> VersionMeta:
    """Create a new snapshot of all prompt files.

    Args:
        cwd: Working directory containing .prompt-vc/ store.
        message: Descriptive message for this snapshot.

    Returns:
        VersionMeta for the newly created snapshot.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
        NoChangesError: If file content is identical to the last snapshot.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    config = read_config(cwd)
    index = read_index(cwd)

    prompt_dir = Path(config.prompt_dir)
    if not prompt_dir.is_absolute():
        prompt_dir = cwd / prompt_dir

    files = discover_prompts(prompt_dir, config.file_pattern)
    file_hashes: dict[str, str] = {f.name: hash_file(f) for f in files}
    version_hash = hash_version(file_hashes)

    if index.versions and index.versions[-1].hash == version_hash:
        raise NoChangesError(
            "No changes detected since last snapshot. Nothing to commit."
        )

    version_num = len(index.versions) + 1
    version_id = f"v{version_num}"
    parent = index.versions[-1].version if index.versions else None
    timestamp = datetime.now(timezone.utc).isoformat()

    snap_dir = store_path(cwd) / "snapshots" / version_id
    copy_snapshot(files, snap_dir)

    meta = VersionMeta(
        version=version_id,
        hash=version_hash,
        message=message,
        timestamp=timestamp,
        files=file_hashes,
        parent=parent,
    )

    write_yaml(
        snap_dir / "metadata.yaml",
        {
            "version": meta.version,
            "hash": meta.hash,
            "message": meta.message,
            "timestamp": meta.timestamp,
            "files": meta.files,
            "parent": meta.parent,
        },
    )

    index.versions.append(meta)
    index.current_version = version_id
    write_index(cwd, index)

    return meta
