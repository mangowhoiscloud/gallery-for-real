"""Tests for src/agent_eval/config.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_eval.config import load_benchmark_config, load_harness_config, load_suite_config
from agent_eval.models import BenchmarkConfig, BenchmarkRef, AgentRef, SuiteConfig

FIXTURES = Path(__file__).parent / "fixtures"


class TestLoadBenchmarkConfig:
    def test_loads_fixture(self) -> None:
        cfg = load_benchmark_config(FIXTURES / "benchmark.yaml")
        assert isinstance(cfg, BenchmarkConfig)
        assert cfg.name == "word-counter"
        assert cfg.language == "python"
        assert cfg.complexity == "simple"
        assert cfg.expected_tests == 20
        assert cfg.expected_items == 5
        assert cfg.timeout == 3600

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_benchmark_config(tmp_path / "nonexistent.yaml")

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "benchmark.yaml"
        bad.write_text(":\tnot valid yaml: [\n")
        with pytest.raises(ValueError, match="Malformed YAML"):
            load_benchmark_config(bad)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        incomplete = tmp_path / "benchmark.yaml"
        incomplete.write_text("name: foo\nlanguage: python\n")
        with pytest.raises(ValueError, match="Missing required field"):
            load_benchmark_config(incomplete)

    def test_non_mapping_yaml_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "benchmark.yaml"
        bad.write_text("- item1\n- item2\n")
        with pytest.raises(ValueError, match="Expected mapping"):
            load_benchmark_config(bad)


class TestLoadSuiteConfig:
    def test_loads_fixture(self) -> None:
        cfg = load_suite_config(FIXTURES / "eval-config.yaml")
        assert isinstance(cfg, SuiteConfig)
        assert cfg.output == "results/"
        assert cfg.timeout == 3600

    def test_benchmarks_parsed(self) -> None:
        cfg = load_suite_config(FIXTURES / "eval-config.yaml")
        assert len(cfg.benchmarks) == 2
        b0 = cfg.benchmarks[0]
        assert isinstance(b0, BenchmarkRef)
        assert b0.path == "benchmarks/word-counter"
        assert b0.timeout == 3600
        b1 = cfg.benchmarks[1]
        assert b1.path == "benchmarks/employee-crud"
        assert b1.timeout == 7200

    def test_agents_parsed(self) -> None:
        cfg = load_suite_config(FIXTURES / "eval-config.yaml")
        assert len(cfg.agents) == 2
        a0 = cfg.agents[0]
        assert isinstance(a0, AgentRef)
        assert a0.name == "claude-opus"
        assert a0.model == "opus"
        assert a0.extra_args is None
        a1 = cfg.agents[1]
        assert a1.name == "claude-sonnet"
        assert a1.model == "sonnet"
        assert a1.extra_args == {"temperature": "0.0"}

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_suite_config(tmp_path / "nonexistent.yaml")

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "eval-config.yaml"
        bad.write_text(":\tnot valid yaml: [\n")
        with pytest.raises(ValueError, match="Malformed YAML"):
            load_suite_config(bad)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        incomplete = tmp_path / "eval-config.yaml"
        incomplete.write_text("benchmarks: []\nagents: []\noutput: out/\n")
        with pytest.raises(ValueError, match="Missing required field"):
            load_suite_config(incomplete)

    def test_non_mapping_yaml_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "eval-config.yaml"
        bad.write_text("- item\n")
        with pytest.raises(ValueError, match="Expected mapping"):
            load_suite_config(bad)


class TestLoadHarnessConfig:
    def test_loads_fixture(self) -> None:
        cfg = load_harness_config(FIXTURES / ".harness-config")
        assert isinstance(cfg, dict)
        assert cfg["PROJECT_TYPE"] == "python-uv"
        assert cfg["PKG_MGR"] == "uv"
        assert cfg["BUILD_CMD"] == "uv build"
        assert cfg["TEST_CMD"] == "uv run pytest"
        assert cfg["LINT_CMD"] == "uv run ruff check ."

    def test_quoted_values_stripped(self) -> None:
        cfg = load_harness_config(FIXTURES / ".harness-config")
        # SRC_DIRS has double-quoted value
        assert cfg["SRC_DIRS"] == "src/ lib/"

    def test_unquoted_numeric_value(self) -> None:
        cfg = load_harness_config(FIXTURES / ".harness-config")
        assert cfg["AMBIGUITY_THRESHOLD"] == "0.10"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_harness_config(tmp_path / ".harness-config")

    def test_comments_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / ".harness-config"
        f.write_text("# comment\nKEY=value\n# another comment\n")
        cfg = load_harness_config(f)
        assert cfg == {"KEY": "value"}

    def test_blank_lines_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / ".harness-config"
        f.write_text("\nKEY=value\n\n")
        cfg = load_harness_config(f)
        assert cfg == {"KEY": "value"}

    def test_single_quoted_value(self, tmp_path: Path) -> None:
        f = tmp_path / ".harness-config"
        f.write_text("KEY='single quoted'\n")
        cfg = load_harness_config(f)
        assert cfg["KEY"] == "single quoted"

    def test_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        f = tmp_path / ".harness-config"
        f.write_text("")
        cfg = load_harness_config(f)
        assert cfg == {}

    def test_invalid_lines_skipped(self, tmp_path: Path) -> None:
        f = tmp_path / ".harness-config"
        f.write_text("not_a_key_value\nKEY=valid\n=no_key\n")
        cfg = load_harness_config(f)
        assert cfg == {"KEY": "valid"}
