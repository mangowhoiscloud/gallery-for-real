"""Markdown report generator (Item 12)."""
from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from agent_cost_analyzer.models import AnalysisResult, ComparisonResult


def _fmt_cost(d: Decimal) -> str:
    return f"${d:.4f}"


def generate_markdown_report(result: AnalysisResult, output_dir: Path) -> Path:
    """Write report.md to output_dir and return the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "report.md"
    output_path.write_text(_build_report(result), encoding="utf-8")
    return output_path


def _build_report(result: AnalysisResult) -> str:
    sections: list[str] = []

    cb = result.cost_breakdown
    ta = result.token_analysis
    fp = result.failure_patterns

    # 1. Project Summary
    project_type = result.project.project_type or "Unknown"
    total_cost = _fmt_cost(cb.total_cost)
    total_iter = cb.total_iterations

    # Duration from timeline
    duration_str = "N/A"
    if len(result.timeline) >= 2:
        delta = result.timeline[-1][0] - result.timeline[0][0]
        minutes = delta.total_seconds() / 60
        duration_str = f"{minutes:.1f} min"

    # Model split (top models by cost)
    model_split_parts = []
    total_model_cost = sum(cb.by_model.values()) or Decimal("1")
    for model, cost in sorted(cb.by_model.items(), key=lambda x: x[1], reverse=True):
        pct = float(cost / total_model_cost * 100)
        model_split_parts.append(f"{model}: {pct:.0f}%")
    model_split_str = ", ".join(model_split_parts) if model_split_parts else "N/A"

    sections.append(
        f"# Agent Cost Analysis Report\n\n"
        f"## Project Summary\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Project Type | {project_type} |\n"
        f"| Total Cost | {total_cost} |\n"
        f"| Total Iterations | {total_iter} |\n"
        f"| Duration | {duration_str} |\n"
        f"| Model Split | {model_split_str} |\n"
    )

    # 2. Cost by Phase
    phase_rows = []
    for phase, cost in sorted(cb.by_phase.items()):
        phase_rows.append(f"| {phase} | {_fmt_cost(cost)} |")
    if phase_rows:
        sections.append(
            "## Cost by Phase\n\n"
            "| Phase | Cost |\n"
            "|-------|------|\n"
            + "\n".join(phase_rows)
            + "\n"
        )

    # 3. Cost by Item (top 10 by cost)
    top_items = sorted(cb.by_item.items(), key=lambda x: x[1], reverse=True)[:10]
    if top_items:
        item_rows = [f"| {item} | {_fmt_cost(cost)} |" for item, cost in top_items]
        sections.append(
            "## Cost by Item (Top 10)\n\n"
            "| Item | Cost |\n"
            "|------|------|\n"
            + "\n".join(item_rows)
            + "\n"
        )

    # 4. Failure Patterns
    failure_lines = []
    if fp.stuck_events:
        for se in fp.stuck_events:
            failure_lines.append(
                f"- **Stuck**: Item {se.item} at iter {se.start_iteration}"
                f" ({se.count} repeats)"
            )
    if fp.circuit_breakers:
        failure_lines.append(f"- **Circuit breakers fired**: {len(fp.circuit_breakers)}")
    if fp.build_failure_rate > 0:
        failure_lines.append(
            f"- **Build failure rate**: {fp.build_failure_rate:.1%}"
        )
    if not failure_lines:
        failure_lines.append("- No failures detected")
    sections.append("## Failure Patterns\n\n" + "\n".join(failure_lines) + "\n")

    # 5. Key Metrics
    escalation_count = len(ta.escalations)
    anomaly_count = len(ta.anomalies)
    sections.append(
        "## Key Metrics\n\n"
        "| Metric | Value |\n"
        "|--------|-------|\n"
        f"| Input Tokens | {ta.total_input:,} |\n"
        f"| Output Tokens | {ta.total_output:,} |\n"
        f"| I/O Ratio | {ta.io_ratio:.2f} |\n"
        f"| Model Escalations | {escalation_count} |\n"
        f"| Token Anomalies | {anomaly_count} |\n"
    )

    return "\n".join(sections)


def generate_comparison_markdown(result: ComparisonResult, output_dir: Path) -> Path:
    """Write comparison.md to output_dir and return the output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "comparison.md"
    output_path.write_text(_build_comparison(result), encoding="utf-8")
    return output_path


def _build_comparison(result: ComparisonResult) -> str:
    sections: list[str] = []

    # Summary table
    header = "| Project | Cost | Iterations | Duration (min) | Stuck |\n"
    separator = "|---------|------|------------|----------------|-------|\n"
    rows = []
    for row in result.summary_table:
        rows.append(
            f"| {row.project_name} | {_fmt_cost(row.total_cost)}"
            f" | {row.total_iterations} | {row.duration_minutes:.1f}"
            f" | {row.stuck_count} |"
        )
    sections.append(
        "# Project Comparison Report\n\n"
        "## Summary\n\n"
        + header
        + separator
        + "\n".join(rows)
        + "\n"
    )

    # Efficiency ranking
    rank_rows = []
    for i, entry in enumerate(result.efficiency_ranking, 1):
        rank_rows.append(
            f"| {i} | {entry.project_name} | {_fmt_cost(entry.cost_per_iteration)} |"
        )
    if rank_rows:
        sections.append(
            "## Efficiency Ranking\n\n"
            "| Rank | Project | Cost/Iteration |\n"
            "|------|---------|---------------|\n"
            + "\n".join(rank_rows)
            + "\n"
        )

    # Stack comparison
    if result.stack_comparison:
        stack_rows = []
        for stack, data in sorted(result.stack_comparison.items()):
            avg_cost = data.get("avg_total_cost", 0)
            count = data.get("project_count", 0)
            stack_rows.append(f"| {stack} | {count} | ${avg_cost:.4f} |")
        sections.append(
            "## Stack Comparison\n\n"
            "| Stack | Projects | Avg Cost |\n"
            "|-------|----------|----------|\n"
            + "\n".join(stack_rows)
            + "\n"
        )

    return "\n".join(sections)
