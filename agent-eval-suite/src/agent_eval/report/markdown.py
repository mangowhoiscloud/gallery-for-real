"""Markdown report generation."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from agent_eval.models import RunResult


def _winner(results: list[RunResult]) -> RunResult:
    """Return the best result: highest test_pass_rate, ties broken by lowest cost."""
    return max(results, key=lambda r: (r.test_pass_rate, -r.estimated_cost))


def generate_markdown_report(results: list[RunResult], output_path: Path | str) -> None:
    """Write a Markdown comparison report to output_path."""
    output_path = Path(output_path)
    lines: list[str] = []

    # ── Comparison table ──────────────────────────────────────────────────────
    lines.append("# Agent Evaluation Report\n")
    lines.append("## Comparison Table\n")

    header = "| Agent | Benchmark | Success | Pass Rate | Time (s) | Cost ($) | Items Done |"
    sep = "|-------|-----------|---------|-----------|----------|----------|------------|"
    lines.append(header)
    lines.append(sep)

    for r in results:
        success_str = "✓" if r.success else "✗"
        items_str = f"{r.items_completed}/{r.items_total}"
        row = (
            f"| {r.agent} | {r.benchmark} | {success_str} "
            f"| {r.test_pass_rate:.2%} | {r.total_time_seconds:.1f} "
            f"| ${r.estimated_cost:.4f} | {items_str} |"
        )
        lines.append(row)

    lines.append("")

    # ── Winner summary ────────────────────────────────────────────────────────
    lines.append("## Winners by Benchmark\n")

    by_benchmark: dict[str, list[RunResult]] = defaultdict(list)
    for r in results:
        by_benchmark[r.benchmark].append(r)

    if not results:
        lines.append("_No results._\n")
    else:
        for benchmark, bench_results in sorted(by_benchmark.items()):
            w = _winner(bench_results)
            if len(bench_results) == 1:
                lines.append(f"- **{benchmark}**: {w.agent} (sole entry)")
            else:
                lines.append(
                    f"- **{benchmark}**: **{w.agent}** "
                    f"(pass rate {w.test_pass_rate:.2%}, cost ${w.estimated_cost:.4f})"
                )
        lines.append("")

    # ── Detailed per-run metrics ──────────────────────────────────────────────
    lines.append("## Detailed Metrics\n")

    for r in results:
        lines.append(f"### {r.agent} on {r.benchmark}\n")
        lines.append(f"- **Success**: {r.success}")
        lines.append(f"- **Build success**: {r.build_success}")
        lines.append(f"- **Tests**: {r.test_passed}/{r.test_total} passed ({r.test_pass_rate:.2%})")
        lines.append(f"- **Time**: {r.total_time_seconds:.1f}s")
        lines.append(f"- **Iterations**: {r.total_iterations}")
        lines.append(f"- **Tokens in/out**: {r.total_tokens_in}/{r.total_tokens_out}")
        lines.append(f"- **Cost**: ${r.estimated_cost:.4f}")
        lines.append(f"- **Items**: {r.items_completed}/{r.items_total}")
        lines.append(f"- **Stuck count**: {r.stuck_count}")
        lines.append(f"- **Circuit breakers**: {r.circuit_breaker_count}")
        if r.error:
            lines.append(f"- **Error**: {r.error}")
        if r.phase_times:
            lines.append("- **Phase times**:")
            for phase, t in sorted(r.phase_times.items()):
                lines.append(f"  - {phase}: {t:.1f}s")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
