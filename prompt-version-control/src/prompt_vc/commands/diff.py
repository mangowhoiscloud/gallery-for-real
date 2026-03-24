"""diff command: show unified diff between two snapshot versions."""

import difflib
from pathlib import Path

from prompt_vc.storage import is_initialized, read_index, store_path


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


class VersionNotFoundError(Exception):
    """Raised when a requested version does not exist."""


def diff(cwd: Path, v1: str, v2: str) -> str:
    """Return unified diff between two snapshot versions.

    Files added in v2 are labeled 'new file: <name>'.
    Files removed in v2 are labeled 'deleted file: <name>'.
    Files with identical content in both versions are omitted.

    Args:
        cwd: Working directory containing .prompt-vc/ store.
        v1: First (from) version ID (e.g. "v1").
        v2: Second (to) version ID (e.g. "v2").

    Returns:
        Unified diff string. Empty string if no differences.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
        VersionNotFoundError: If v1 or v2 does not exist.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)
    versions_by_id = {v.version: v for v in index.versions}

    if v1 not in versions_by_id:
        raise VersionNotFoundError(f"Version '{v1}' not found.")
    if v2 not in versions_by_id:
        raise VersionNotFoundError(f"Version '{v2}' not found.")

    v1_meta = versions_by_id[v1]
    v2_meta = versions_by_id[v2]

    snap_dir = store_path(cwd) / "snapshots"
    v1_dir = snap_dir / v1
    v2_dir = snap_dir / v2

    v1_files = set(v1_meta.files.keys())
    v2_files = set(v2_meta.files.keys())
    all_files = sorted(v1_files | v2_files)

    output_parts: list[str] = []

    for filename in all_files:
        in_v1 = filename in v1_files
        in_v2 = filename in v2_files

        # Skip files with identical content
        if in_v1 and in_v2 and v1_meta.files[filename] == v2_meta.files[filename]:
            continue

        if in_v1:
            v1_lines = (v1_dir / filename).read_text(encoding="utf-8").splitlines(keepends=True)
            from_label = f"{v1}/{filename}"
        else:
            v1_lines = []
            from_label = "/dev/null"

        if in_v2:
            v2_lines = (v2_dir / filename).read_text(encoding="utf-8").splitlines(keepends=True)
            to_label = f"{v2}/{filename}"
        else:
            v2_lines = []
            to_label = "/dev/null"

        diff_lines = list(
            difflib.unified_diff(v1_lines, v2_lines, fromfile=from_label, tofile=to_label)
        )

        if not diff_lines:
            continue

        if not in_v1:
            output_parts.append(f"new file: {filename}")
        elif not in_v2:
            output_parts.append(f"deleted file: {filename}")

        output_parts.append("".join(diff_lines))

    return "\n".join(output_parts)
