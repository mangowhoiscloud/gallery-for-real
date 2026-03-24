"""Data models for agent cost analyzer."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class CostEntry:
    """A single line parsed from cost.log."""

    timestamp: datetime
    phase: str
    iteration: int
    model: str
    input_tokens: int
    output_tokens: int
    cost: Decimal
    cumulative: Decimal
    item: Optional[int]


@dataclass
class PhaseEvent:
    """An event from phase.log."""

    timestamp: datetime
    event: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class MetricEntry:
    """A single metric line from metrics.log."""

    timestamp: datetime
    metric: str
    context: str
    value: int
    detail: int


@dataclass
class ProgressData:
    """Structured data extracted from progress.txt."""

    project_type: str = ""
    init_time: Optional[datetime] = None
    sessions: list[datetime] = field(default_factory=list)
    completed_items: list[tuple[int, str]] = field(default_factory=list)
    is_complete: bool = False


@dataclass
class SessionError:
    """An error extracted from a session log file."""

    file: str
    line_num: int
    error_type: str
    message: str
    is_recovery: bool = False


# --- Supporting dataclasses for analysis results ---


@dataclass
class PhaseTokenData:
    """Token totals for a single phase."""

    input_tokens: int = 0
    output_tokens: int = 0
    count: int = 0


@dataclass
class ModelTokenData:
    """Token totals for a single model."""

    input_tokens: int = 0
    output_tokens: int = 0
    count: int = 0


@dataclass
class EscalationEvent:
    """A model escalation event (cheaper → more expensive on same item)."""

    item: int
    iteration: int
    from_model: str
    to_model: str


@dataclass
class AnomalyEntry:
    """A per-phase token anomaly (>3σ from phase mean)."""

    phase: str
    iteration: int
    actual_tokens: int
    threshold: float


@dataclass
class StuckEvent:
    """A stuck-loop event where the same item repeats multiple iterations."""

    item: int
    start_iteration: int
    count: int


@dataclass
class CircuitBreakerEvent:
    """A CIRCUIT_BREAKER event from phase.log."""

    timestamp: datetime
    message: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ProjectSummaryRow:
    """One row in the comparison summary table."""

    project_name: str
    total_cost: Decimal
    total_iterations: int
    duration_minutes: float
    model_split: dict[str, float]
    stuck_count: int


@dataclass
class EfficiencyEntry:
    """A project entry ranked by cost-per-iteration."""

    project_name: str
    cost_per_iteration: Decimal


# --- Top-level analysis containers ---


@dataclass
class CostBreakdown:
    """Aggregated cost breakdown from cost.log entries."""

    by_phase: dict[str, Decimal] = field(default_factory=dict)
    by_model: dict[str, Decimal] = field(default_factory=dict)
    by_item: dict[int, Decimal] = field(default_factory=dict)
    timeline: list[tuple[datetime, Decimal]] = field(default_factory=list)
    total_cost: Decimal = field(default_factory=lambda: Decimal("0"))
    total_iterations: int = 0


@dataclass
class TokenAnalysis:
    """Aggregated token usage analysis."""

    total_input: int = 0
    total_output: int = 0
    io_ratio: float = 0.0
    by_phase: dict[str, PhaseTokenData] = field(default_factory=dict)
    by_model: dict[str, ModelTokenData] = field(default_factory=dict)
    escalations: list[EscalationEvent] = field(default_factory=list)
    anomalies: list[AnomalyEntry] = field(default_factory=list)


@dataclass
class FailurePatterns:
    """Failure pattern analysis results."""

    stuck_events: list[StuckEvent] = field(default_factory=list)
    circuit_breakers: list[CircuitBreakerEvent] = field(default_factory=list)
    build_failure_rate: float = 0.0
    error_categories: dict[str, int] = field(default_factory=dict)
    recovery_times: dict[int, int] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Multi-project comparison analysis."""

    summary_table: list[ProjectSummaryRow] = field(default_factory=list)
    efficiency_ranking: list[EfficiencyEntry] = field(default_factory=list)
    stack_comparison: dict[str, dict] = field(default_factory=dict)
    cost_comparison: list[dict] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Top-level container for a complete single-project analysis."""

    project: ProgressData = field(default_factory=ProgressData)
    summary: dict = field(default_factory=dict)
    cost_breakdown: CostBreakdown = field(default_factory=CostBreakdown)
    token_analysis: TokenAnalysis = field(default_factory=TokenAnalysis)
    failure_patterns: FailurePatterns = field(default_factory=FailurePatterns)
    timeline: list[tuple[datetime, Decimal]] = field(default_factory=list)
