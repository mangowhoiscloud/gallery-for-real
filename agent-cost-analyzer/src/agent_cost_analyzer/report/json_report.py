"""JSON report generator (Item 11)."""
from __future__ import annotations

import dataclasses
import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from agent_cost_analyzer.models import AnalysisResult, ComparisonResult


class _AnalysisEncoder(json.JSONEncoder):
    """Serialize Decimal → float, datetime → ISO string, dataclasses → dict."""

    def default(self, obj: object) -> object:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        return super().default(obj)


def _result_to_dict(result: AnalysisResult) -> dict:
    """Convert AnalysisResult to a JSON-serializable dict matching the spec structure."""
    cb = result.cost_breakdown
    ta = result.token_analysis
    fp = result.failure_patterns

    return {
        "project": dataclasses.asdict(result.project),
        "summary": result.summary,
        "cost_breakdown": {
            "by_phase": dict(cb.by_phase),
            "by_model": dict(cb.by_model),
            "by_item": {k: v for k, v in cb.by_item.items()},
            "total_cost": cb.total_cost,
            "total_iterations": cb.total_iterations,
        },
        "token_analysis": {
            "total_input": ta.total_input,
            "total_output": ta.total_output,
            "io_ratio": ta.io_ratio,
            "by_phase": {
                phase: dataclasses.asdict(data) for phase, data in ta.by_phase.items()
            },
            "by_model": {
                model: dataclasses.asdict(data) for model, data in ta.by_model.items()
            },
            "escalations": [dataclasses.asdict(e) for e in ta.escalations],
            "anomalies": [dataclasses.asdict(a) for a in ta.anomalies],
        },
        "failure_patterns": {
            "stuck_events": [dataclasses.asdict(s) for s in fp.stuck_events],
            "circuit_breakers": [dataclasses.asdict(c) for c in fp.circuit_breakers],
            "build_failure_rate": fp.build_failure_rate,
            "error_categories": dict(fp.error_categories),
            "recovery_times": {str(k): v for k, v in fp.recovery_times.items()},
        },
        "timeline": [
            {"timestamp": ts.isoformat(), "cumulative": cum}
            for ts, cum in result.timeline
        ],
    }


def _comparison_to_dict(result: ComparisonResult) -> dict:
    """Convert ComparisonResult to a JSON-serializable dict."""
    return {
        "summary_table": [dataclasses.asdict(row) for row in result.summary_table],
        "efficiency_ranking": [dataclasses.asdict(e) for e in result.efficiency_ranking],
        "stack_comparison": result.stack_comparison,
        "cost_comparison": result.cost_comparison,
    }


def generate_json_report(result: AnalysisResult, output_dir: Path) -> Path:
    """Write report.json to output_dir and return the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "report.json"
    data = _result_to_dict(result)
    output_path.write_text(
        json.dumps(data, cls=_AnalysisEncoder, indent=2), encoding="utf-8"
    )
    return output_path


def generate_comparison_json(result: ComparisonResult, output_dir: Path) -> Path:
    """Write comparison.json to output_dir and return the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "comparison.json"
    data = _comparison_to_dict(result)
    output_path.write_text(
        json.dumps(data, cls=_AnalysisEncoder, indent=2), encoding="utf-8"
    )
    return output_path
