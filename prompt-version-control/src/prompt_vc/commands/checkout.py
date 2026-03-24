"""checkout command: restore prompt files from a snapshot version."""

import shutil
from pathlib import Path

from prompt_vc.hashing import hash_file
from prompt_vc.storage import (
    discover_prompts,
    is_initialized,
    read_config,
    read_index,
    store_path,
    write_index,
)


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


class VersionNotFoundError(Exception):
    """Raised when a requested version does not exist."""


class UnsavedChangesError(Exception):
    """Raised when working files differ from the current snapshot and --force is not set."""


def checkout(cwd: Path, version: str, force: bool = False) -> None:
    """Restore prompt files from a snapshot version.

    Compares current working files against the current version snapshot
    to detect unsaved changes. If changes exist and force is False, aborts.
    Otherwise copies snapshot files to prompt_dir and updates current_version.

    Args:
        cwd: Working directory containing .prompt-vc/ store.
        version: Version ID to check out (e.g. "v1").
        force: If True, overwrite working files even if unsaved changes exist.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
        VersionNotFoundError: If the requested version does not exist.
        UnsavedChangesError: If unsaved changes exist and force is False.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)
    versions_by_id = {v.version: v for v in index.versions}

    if version not in versions_by_id:
        raise VersionNotFoundError(f"Version '{version}' not found.")

    config = read_config(cwd)
    prompt_dir = Path(config.prompt_dir)
    if not prompt_dir.is_absolute():
        prompt_dir = cwd / prompt_dir

    # Detect unsaved changes: compare working files against current version snapshot
    if not force and index.current_version is not None:
        current_meta = versions_by_id.get(index.current_version)
        if current_meta is not None:
            working_files = discover_prompts(prompt_dir, config.file_pattern)
            working_hashes = {f.name: hash_file(f) for f in working_files}
            if working_hashes != current_meta.files:
                raise UnsavedChangesError(
                    "Unsaved changes detected in working directory. "
                    "Use --force to overwrite."
                )

    # Copy snapshot files to prompt_dir
    target_meta = versions_by_id[version]
    snap_dir = store_path(cwd) / "snapshots" / version

    # Remove files in prompt_dir that are no longer in the target snapshot
    for existing in discover_prompts(prompt_dir, config.file_pattern):
        if existing.name not in target_meta.files:
            existing.unlink()

    # Copy all files from snapshot to prompt_dir
    for filename in target_meta.files:
        src = snap_dir / filename
        dst = prompt_dir / filename
        shutil.copy2(src, dst)

    index.current_version = version
    write_index(cwd, index)
