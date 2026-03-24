"""Tests for the init command."""

import pytest

from prompt_vc.commands.init import AlreadyInitializedError, init
from prompt_vc.storage import (
    is_initialized,
    read_config,
    read_index,
    store_path,
)


def test_init_creates_store_directory(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert store_path(tmp_path).is_dir()


def test_init_creates_snapshots_subdir(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert (store_path(tmp_path) / "snapshots").is_dir()


def test_init_creates_bindings_subdir(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert (store_path(tmp_path) / "bindings").is_dir()


def test_init_writes_config_yaml(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert (store_path(tmp_path) / "config.yaml").is_file()


def test_init_writes_index_yaml(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert (store_path(tmp_path) / "index.yaml").is_file()


def test_init_config_has_correct_prompt_dir(tmp_path):
    prompt_dir = tmp_path / "my_prompts"
    init(tmp_path, prompt_dir)
    config = read_config(tmp_path)
    assert config.prompt_dir == str(prompt_dir)


def test_init_config_has_default_file_pattern(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    config = read_config(tmp_path)
    assert config.file_pattern == "PROMPT_*.md"


def test_init_index_has_null_current_version(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    index = read_index(tmp_path)
    assert index.current_version is None


def test_init_index_has_empty_versions_list(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    index = read_index(tmp_path)
    assert index.versions == []


def test_init_marks_as_initialized(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    assert is_initialized(tmp_path)


def test_init_twice_raises_already_initialized_error(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    with pytest.raises(AlreadyInitializedError):
        init(tmp_path, prompt_dir)


def test_init_error_message_mentions_prompt_vc(tmp_path):
    prompt_dir = tmp_path / "prompts"
    init(tmp_path, prompt_dir)
    with pytest.raises(AlreadyInitializedError, match=r"\.prompt-vc"):
        init(tmp_path, prompt_dir)


def test_init_prompt_dir_does_not_need_to_exist(tmp_path):
    """prompt_dir is stored in config but not required to exist at init time."""
    nonexistent_dir = tmp_path / "does_not_exist"
    init(tmp_path, nonexistent_dir)
    config = read_config(tmp_path)
    assert config.prompt_dir == str(nonexistent_dir)
