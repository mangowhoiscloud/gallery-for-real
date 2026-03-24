"""HTML dashboard report generator (Item 13)."""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from agent_cost_analyzer.models import AnalysisResult, ComparisonResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"


class _AnalysisEncoder(json.JSONEncoder):
    """Serialize Decimal → float, datetime → ISO string."""

    def default(self, obj: object) -> object:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def _analysis_to_dict(result: AnalysisResult) -> dict:
    """Convert AnalysisResult to a JSON-serializable dict."""
    cb = result.cost_breakdown
    ta = result.token_analysis
    fp = result.failure_patterns

    return {
        "total_cost": float(cb.total_cost),
        "total_iterations": cb.total_iterations,
        "avg_iteration_cost": float(cb.total_cost / cb.total_iterations) if cb.total_iterations else 0.0,
        "summary": {
            k: float(v) if isinstance(v, Decimal) else v
            for k, v in result.summary.items()
        },
        "cost_breakdown": {
            "by_phase": {k: float(v) for k, v in cb.by_phase.items()},
            "by_model": {k: float(v) for k, v in cb.by_model.items()},
            "by_item": {str(k): float(v) for k, v in cb.by_item.items()},
            "timeline": [
                {"ts": ts.isoformat(), "cumulative": float(cum)}
                for ts, cum in cb.timeline
            ],
        },
        "token_analysis": {
            "total_input": ta.total_input,
            "total_output": ta.total_output,
            "io_ratio": ta.io_ratio,
            "by_phase": {
                phase: {
                    "input_tokens": d.input_tokens,
                    "output_tokens": d.output_tokens,
                    "count": d.count,
                }
                for phase, d in ta.by_phase.items()
            },
            "by_model": {
                model: {
                    "input_tokens": d.input_tokens,
                    "output_tokens": d.output_tokens,
                    "count": d.count,
                }
                for model, d in ta.by_model.items()
            },
            "escalations": [
                {
                    "item": e.item,
                    "iteration": e.iteration,
                    "from_model": e.from_model,
                    "to_model": e.to_model,
                }
                for e in ta.escalations
            ],
            "anomalies": [
                {
                    "phase": a.phase,
                    "iteration": a.iteration,
                    "actual_tokens": a.actual_tokens,
                    "threshold": a.threshold,
                }
                for a in ta.anomalies
            ],
        },
        "failure_patterns": {
            "stuck_events": [
                {"item": s.item, "start_iteration": s.start_iteration, "count": s.count}
                for s in fp.stuck_events
            ],
            "circuit_breakers": [
                {
                    "timestamp": cb_ev.timestamp.isoformat(),
                    "message": cb_ev.message,
                    "metadata": cb_ev.metadata,
                }
                for cb_ev in fp.circuit_breakers
            ],
            "build_failure_rate": fp.build_failure_rate,
            "error_categories": fp.error_categories,
            "recovery_times": {str(k): v for k, v in fp.recovery_times.items()},
        },
        "project": {
            "project_type": result.project.project_type,
            "is_complete": result.project.is_complete,
            "completed_items_count": len(result.project.completed_items),
        },
    }


def _comparison_to_dict(result: ComparisonResult) -> dict:
    return {
        "summary_table": [
            {
                "project_name": row.project_name,
                "total_cost": float(row.total_cost),
                "total_iterations": row.total_iterations,
                "duration_minutes": row.duration_minutes,
                "model_split": row.model_split,
                "stuck_count": row.stuck_count,
            }
            for row in result.summary_table
        ],
        "efficiency_ranking": [
            {"project_name": e.project_name, "cost_per_iteration": float(e.cost_per_iteration)}
            for e in result.efficiency_ranking
        ],
        "stack_comparison": result.stack_comparison,
        "cost_comparison": result.cost_comparison,
    }


def _render(template_name: str, context: dict) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


def generate_html_report(result: AnalysisResult, output_dir: Path) -> Path:
    """Generate a self-contained HTML dashboard at output_dir/report.html."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = _analysis_to_dict(result)
    data_json = json.dumps(data, cls=_AnalysisEncoder)
    html = _render("dashboard.html", {"data_json": data_json, "data": data})
    out = output_dir / "report.html"
    out.write_text(html, encoding="utf-8")
    return out


def generate_comparison_html(result: ComparisonResult, output_dir: Path) -> Path:
    """Generate a self-contained comparison HTML at output_dir/comparison.html."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = _comparison_to_dict(result)
    data_json = json.dumps(data, cls=_AnalysisEncoder)
    html = _render("comparison.html", {"data_json": data_json, "data": data})
    out = output_dir / "comparison.html"
    out.write_text(html, encoding="utf-8")
    return out
