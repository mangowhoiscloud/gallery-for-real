"""Abstract base class for agent backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agent_eval.models import RunResult


class AgentBackend(ABC):
    """Strategy interface for running an agent against a benchmark."""

    @abstractmethod
    def run(self, benchmark_dir: Path, output_dir: Path) -> RunResult:
        """Run the agent against benchmark_dir and write outputs to output_dir.

        Args:
            benchmark_dir: Path to the benchmark source directory.
            output_dir: Path where the run's working copy and artifacts are written.

        Returns:
            RunResult populated with metrics from this run.
        """
