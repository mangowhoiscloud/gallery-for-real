"""Config loaders for benchmark.yaml, eval-config.yaml, and .harness-config."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from agent_eval.models import AgentRef, BenchmarkConfig, BenchmarkRef, SuiteConfig


def load_benchmark_config(path: str | Path) -> BenchmarkConfig:
    """Load BenchmarkConfig from a benchmark.yaml file.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if required fields are missing or YAML is malformed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"benchmark.yaml not found: {path}")
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data)}")
    required = ("name", "language", "complexity", "expected_tests", "expected_items", "timeout")
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in {path}")
    return BenchmarkConfig(
        name=str(data["name"]),
        language=str(data["language"]),
        complexity=str(data["complexity"]),
        expected_tests=int(data["expected_tests"]),
        expected_items=int(data["expected_items"]),
        timeout=int(data["timeout"]),
    )


def load_suite_config(path: str | Path) -> SuiteConfig:
    """Load SuiteConfig from an eval-config.yaml file.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if required fields are missing or YAML is malformed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"eval-config.yaml not found: {path}")
    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ValueError(f"Malformed YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data)}")
    required = ("benchmarks", "agents", "output", "timeout")
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field '{field}' in {path}")
    benchmarks = [
        BenchmarkRef(
            path=str(b["path"]),
            timeout=int(b["timeout"]) if "timeout" in b else None,
        )
        for b in data["benchmarks"]
    ]
    agents = [
        AgentRef(
            name=str(a["name"]),
            model=str(a["model"]) if "model" in a else None,
            extra_args=dict(a["extra_args"]) if "extra_args" in a else None,
        )
        for a in data["agents"]
    ]
    return SuiteConfig(
        benchmarks=benchmarks,
        agents=agents,
        output=str(data["output"]),
        timeout=int(data["timeout"]),
    )


_HARNESS_LINE = re.compile(r'^([A-Za-z_]\w*)=(.*)$')


def load_harness_config(path: str | Path) -> dict[str, str]:
    """Load .harness-config as a dict of KEY → VALUE.

    Lines in shell format: KEY="value", KEY='value', or KEY=value.
    Comments (#) and blank lines are ignored.

    Raises:
        FileNotFoundError: if the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f".harness-config not found: {path}")
    result: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _HARNESS_LINE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if len(value) >= 2 and (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
        ):
            value = value[1:-1]
        result[key] = value
    return result
