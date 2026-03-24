"""log command: display version history."""

from pathlib import Path

from prompt_vc.storage import is_initialized, read_index


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


def log(cwd: Path) -> str:
    """Return formatted version history.

    Versions are listed in reverse chronological order (newest first).
    The current version is marked with an asterisk (*).

    Args:
        cwd: Working directory containing .prompt-vc/ store.

    Returns:
        Formatted string of version history, or "No versions yet." if empty.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)

    if not index.versions:
        return "No versions yet."

    lines: list[str] = []
    for version in reversed(index.versions):
        marker = "*" if version.version == index.current_version else " "
        short_hash = version.hash[:8]
        lines.append(
            f"{marker} {version.version:<4}  {version.timestamp}  {short_hash}  {version.message}"
        )

    return "\n".join(lines)
