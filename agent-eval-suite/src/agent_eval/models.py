"""Data models for agent-eval-suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunResult:
    """Result of a single agent run against a benchmark."""

    agent: str
    benchmark: str
    success: bool
    build_success: bool
    test_total: int
    test_passed: int
    test_pass_rate: float
    total_iterations: int
    total_time_seconds: float
    phase_times: dict[str, float] = field(default_factory=dict)
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost: float = 0.0
    items_completed: int = 0
    items_total: int = 0
    stuck_count: int = 0
    circuit_breaker_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-serializable dict."""
        return {
            "agent": self.agent,
            "benchmark": self.benchmark,
            "success": self.success,
            "build_success": self.build_success,
            "test_total": self.test_total,
            "test_passed": self.test_passed,
            "test_pass_rate": self.test_pass_rate,
            "total_iterations": self.total_iterations,
            "total_time_seconds": self.total_time_seconds,
            "phase_times": self.phase_times,
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "estimated_cost": self.estimated_cost,
            "items_completed": self.items_completed,
            "items_total": self.items_total,
            "stuck_count": self.stuck_count,
            "circuit_breaker_count": self.circuit_breaker_count,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunResult:
        """Deserialize from a dict."""
        return cls(
            agent=data["agent"],
            benchmark=data["benchmark"],
            success=data["success"],
            build_success=data["build_success"],
            test_total=data["test_total"],
            test_passed=data["test_passed"],
            test_pass_rate=data["test_pass_rate"],
            total_iterations=data["total_iterations"],
            total_time_seconds=data["total_time_seconds"],
            phase_times=data.get("phase_times", {}),
            total_tokens_in=data.get("total_tokens_in", 0),
            total_tokens_out=data.get("total_tokens_out", 0),
            estimated_cost=data.get("estimated_cost", 0.0),
            items_completed=data.get("items_completed", 0),
            items_total=data.get("items_total", 0),
            stuck_count=data.get("stuck_count", 0),
            circuit_breaker_count=data.get("circuit_breaker_count", 0),
            error=data.get("error"),
        )


@dataclass
class BenchmarkConfig:
    """Metadata loaded from benchmark.yaml."""

    name: str
    language: str
    complexity: str
    expected_tests: int
    expected_items: int
    timeout: int


@dataclass
class BenchmarkRef:
    """Reference to a benchmark directory in a suite config."""

    path: str
    timeout: int | None = None


@dataclass
class AgentRef:
    """Reference to an agent in a suite config."""

    name: str
    model: str | None = None
    extra_args: dict[str, str] | None = None


@dataclass
class SuiteConfig:
    """Top-level eval suite configuration loaded from eval-config.yaml."""

    benchmarks: list[BenchmarkRef]
    agents: list[AgentRef]
    output: str
    timeout: int


# --- Parser intermediate types ---


@dataclass
class CostLogData:
    """Data parsed from .harness-logs/cost.log."""

    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost: float = 0.0
    phase_times: dict[str, float] = field(default_factory=dict)
    total_iterations: int = 0
    total_time_seconds: float = 0.0


@dataclass
class PlanData:
    """Data parsed from IMPLEMENTATION_PLAN.md."""

    items_completed: int = 0
    items_total: int = 0


@dataclass
class PhaseLogData:
    """Data parsed from .harness-logs/phase.log."""

    circuit_breaker_count: int = 0
    stuck_count: int = 0


@dataclass
class TestData:
    """Data parsed from test command output."""

    test_total: int = 0
    test_passed: int = 0
    test_failed: int = 0
