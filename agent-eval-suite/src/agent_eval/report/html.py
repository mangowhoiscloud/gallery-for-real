"""HTML report generation."""

from __future__ import annotations

import math
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from agent_eval.metrics import normalize_scores
from agent_eval.models import RunResult


_TEMPLATES_DIR = Path(__file__).parent / "templates"

# Palette for multi-agent charts
_COLORS = ["#e94560", "#0f3460", "#28a745", "#fd7e14", "#6f42c1", "#20c997"]


def _radar_chart_svg(normalized: dict[str, dict[str, float]]) -> str:
    """Return inline SVG for a 4-axis radar chart (one polygon per agent).

    *normalized* is the output of ``metrics.normalize_scores()``.
    Returns empty string when there are no agents to render.
    """
    if not normalized:
        return ""

    W, H = 300, 280
    cx, cy, R = 150, 150, 95
    axes = ["correctness", "speed", "cost", "reliability"]
    labels = ["Correctness", "Speed", "Cost", "Reliability"]
    angles = [-math.pi / 2 + i * 2 * math.pi / len(axes) for i in range(len(axes))]

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    ]
    parts.append(
        f'  <text x="{W // 2}" y="18" text-anchor="middle" '
        f'font-size="13" font-family="system-ui" font-weight="bold" fill="#16213e">'
        "Radar Chart</text>"
    )

    # Grid rings at 25%, 50%, 75%, 100%
    for frac in (0.25, 0.5, 0.75, 1.0):
        pts = " ".join(
            f"{cx + frac * R * math.cos(a):.1f},{cy + frac * R * math.sin(a):.1f}"
            for a in angles
        )
        parts.append(
            f'  <polygon points="{pts}" fill="none" stroke="#dee2e6" stroke-width="1"/>'
        )

    # Axis lines + labels
    for ax, label, angle in zip(axes, labels, angles):
        ax_x = cx + R * math.cos(angle)
        ax_y = cy + R * math.sin(angle)
        parts.append(
            f'  <line x1="{cx}" y1="{cy}" x2="{ax_x:.1f}" y2="{ax_y:.1f}" '
            f'stroke="#adb5bd" stroke-width="1"/>'
        )
        lx = cx + (R + 18) * math.cos(angle)
        ly = cy + (R + 18) * math.sin(angle)
        anchor = (
            "middle"
            if abs(math.cos(angle)) < 0.5
            else ("start" if math.cos(angle) > 0 else "end")
        )
        parts.append(
            f'  <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" font-size="10" font-family="system-ui" fill="#495057">'
            f"{label}</text>"
        )

    # Agent polygons + legend
    legend_y = H - 18
    for idx, (agent, scores) in enumerate(normalized.items()):
        color = _COLORS[idx % len(_COLORS)]
        pts = " ".join(
            f"{cx + scores.get(ax, 0.0) * R * math.cos(angle):.1f},"
            f"{cy + scores.get(ax, 0.0) * R * math.sin(angle):.1f}"
            for ax, angle in zip(axes, angles)
        )
        # fill-opacity before points so regex in tests can locate data polygons
        parts.append(
            f'  <polygon fill="{color}" fill-opacity="0.2" points="{pts}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        lx = 10 + idx * 85
        parts.append(
            f'  <rect x="{lx}" y="{legend_y - 6}" width="12" height="12" fill="{color}"/>'
        )
        parts.append(
            f'  <text x="{lx + 14}" y="{legend_y + 3}" font-size="9" '
            f'font-family="system-ui" fill="#495057">{agent[:10]}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _stacked_bar_chart_svg(results: list[RunResult]) -> str:
    """Return inline SVG for a stacked bar chart of phase_times per run.

    Returns empty string when no results have phase_times data.
    """
    if not results:
        return ""

    all_phases: set[str] = set()
    for r in results:
        all_phases.update(r.phase_times.keys())
    phases = sorted(all_phases)
    if not phases:
        return ""

    W, H = 300, 280
    ml, mr, mt, mb = 45, 10, 30, 65
    chart_w = W - ml - mr
    chart_h = H - mt - mb

    n = len(results)
    bar_w = max(10, chart_w // n - 4)

    max_total = max(
        (sum(r.phase_times.values()) for r in results), default=1.0
    ) or 1.0

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    ]
    parts.append(
        f'  <text x="{W // 2}" y="18" text-anchor="middle" '
        f'font-size="13" font-family="system-ui" font-weight="bold" fill="#16213e">'
        "Phase Time Distribution</text>"
    )
    # Y axis line
    parts.append(
        f'  <line x1="{ml}" y1="{mt}" x2="{ml}" y2="{mt + chart_h}" '
        f'stroke="#adb5bd" stroke-width="1"/>'
    )

    for ri, r in enumerate(results):
        x_start = ml + ri * (chart_w // n) + 2
        y_offset = mt + chart_h  # stack bars bottom-up
        for pi, phase in enumerate(phases):
            t = r.phase_times.get(phase, 0.0)
            if t <= 0:
                continue
            bar_h = t / max_total * chart_h
            color = _COLORS[pi % len(_COLORS)]
            parts.append(
                f'  <rect x="{x_start}" y="{y_offset - bar_h:.1f}" '
                f'width="{bar_w}" height="{bar_h:.1f}" fill="{color}" '
                f'stroke="white" stroke-width="0.5">'
            )
            parts.append(f"    <title>{phase}: {t:.1f}s</title>")
            parts.append("  </rect>")
            y_offset -= bar_h

        # X-axis label (rotated)
        label = f"{r.agent[:6]}/{r.benchmark[:4]}"
        tx = x_start + bar_w // 2
        ty = mt + chart_h + 14
        parts.append(
            f'  <text x="{tx}" y="{ty}" text-anchor="end" font-size="8" '
            f'font-family="system-ui" fill="#495057" '
            f'transform="rotate(-45 {tx} {ty})">{label}</text>'
        )

    # Phase legend (circles to avoid inflating <rect> count)
    legend_y = H - 10
    for pi, phase in enumerate(phases[:6]):
        color = _COLORS[pi % len(_COLORS)]
        lx = 5 + pi * 48
        parts.append(
            f'  <circle cx="{lx + 5}" cy="{legend_y - 1}" r="5" fill="{color}"/>'
        )
        parts.append(
            f'  <text x="{lx + 12}" y="{legend_y + 3}" font-size="8" '
            f'font-family="system-ui" fill="#495057">{phase[:6]}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _heatmap_svg(results: list[RunResult]) -> str:
    """Return inline SVG for a benchmark × agent pass-rate heatmap.

    Cells are coloured green (high pass rate) → red (low pass rate).
    Returns empty string when there are no results.
    """
    if not results:
        return ""

    agents = sorted({r.agent for r in results})
    benchmarks = sorted({r.benchmark for r in results})

    grid: dict[tuple[str, str], float] = {}
    for r in results:
        grid[(r.benchmark, r.agent)] = r.test_pass_rate

    cell_w, cell_h = 60, 28
    ml, mt = 85, 50
    W = ml + len(agents) * cell_w + 10
    H = mt + len(benchmarks) * cell_h + 35

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
    ]
    parts.append(
        f'  <text x="{W // 2}" y="18" text-anchor="middle" '
        f'font-size="13" font-family="system-ui" font-weight="bold" fill="#16213e">'
        "Pass Rate Heatmap</text>"
    )

    # Column headers (agents)
    for ai, agent in enumerate(agents):
        ax = ml + ai * cell_w + cell_w // 2
        parts.append(
            f'  <text x="{ax}" y="{mt - 8}" text-anchor="end" font-size="9" '
            f'font-family="system-ui" fill="#495057" '
            f'transform="rotate(-35 {ax} {mt - 8})">{agent[:10]}</text>'
        )

    # Row headers + cells
    for bi, bench in enumerate(benchmarks):
        by = mt + bi * cell_h
        parts.append(
            f'  <text x="{ml - 4}" y="{by + cell_h // 2}" text-anchor="end" '
            f'dominant-baseline="middle" font-size="9" font-family="system-ui" '
            f'fill="#495057">{bench[:12]}</text>'
        )
        for ai, agent in enumerate(agents):
            rate = grid.get((bench, agent))
            ax = ml + ai * cell_w
            if rate is None:
                fill = "#f8f9fa"
                label = "N/A"
                text_fill = "#6c757d"
            else:
                # Interpolate #28a745 (green, rate=1) ↔ #dc3545 (red, rate=0)
                r_int = int(rate * 0x28 + (1 - rate) * 0xDC)
                g_int = int(rate * 0xA7 + (1 - rate) * 0x35)
                fill = f"#{r_int:02x}{g_int:02x}45"
                label = f"{rate * 100:.0f}%"
                text_fill = "#fff" if (rate < 0.3 or rate > 0.7) else "#212529"
            parts.append(
                f'  <rect x="{ax}" y="{by}" width="{cell_w}" height="{cell_h}" '
                f'fill="{fill}" stroke="white" stroke-width="1"/>'
            )
            parts.append(
                f'  <text x="{ax + cell_w // 2}" y="{by + cell_h // 2}" '
                f'text-anchor="middle" dominant-baseline="middle" font-size="10" '
                f'font-family="system-ui" fill="{text_fill}">{label}</text>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def generate_html_report(
    results: list[RunResult],
    output_path: Path | str,
    *,
    radar_svg: str | None = None,
    bar_chart_svg: str | None = None,
    heatmap_svg: str | None = None,
) -> None:
    """Write a self-contained HTML comparison report to output_path.

    When *radar_svg*, *bar_chart_svg*, or *heatmap_svg* are ``None`` (the
    default), the charts are generated automatically from *results*.  Pass an
    explicit empty string ``""`` to suppress a chart and show its placeholder.
    Pass an SVG string to override auto-generation.
    """
    output_path = Path(output_path)

    if radar_svg is None:
        radar_svg = _radar_chart_svg(normalize_scores(results))
    if bar_chart_svg is None:
        bar_chart_svg = _stacked_bar_chart_svg(results)
    if heatmap_svg is None:
        heatmap_svg = _heatmap_svg(results)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    )
    template = env.get_template("report.html.j2")
    html = template.render(
        results=results,
        radar_svg=radar_svg,
        bar_chart_svg=bar_chart_svg,
        heatmap_svg=heatmap_svg,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
