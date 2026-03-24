"""init command: initialize a .prompt-vc/ store in the current directory."""

from pathlib import Path

from prompt_vc.models import ConfigData, IndexData
from prompt_vc.storage import ensure_store, is_initialized, write_config, write_index


class AlreadyInitializedError(Exception):
    """Raised when .prompt-vc/ already exists."""


def init(cwd: Path, prompt_dir: Path) -> None:
    """Initialize a new .prompt-vc/ store in cwd.

    Args:
        cwd: Directory in which to create the store.
        prompt_dir: Directory where prompt files live (stored in config.yaml).

    Raises:
        AlreadyInitializedError: If the store already exists.
    """
    if is_initialized(cwd):
        raise AlreadyInitializedError(
            f"{cwd / '.prompt-vc'} already exists. "
            "Run 'prompt-vc init' only once per project."
        )

    ensure_store(cwd)

    config = ConfigData(prompt_dir=str(prompt_dir), file_pattern="PROMPT_*.md")
    write_config(cwd, config)

    index = IndexData(current_version=None, versions=[])
    write_index(cwd, index)
