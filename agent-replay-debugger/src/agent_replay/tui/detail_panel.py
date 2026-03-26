"""TUI widget: detail panel with 4 tabs for the right panel.

Tab 1 (Overview): phase, model, tokens in/out, cost, duration, metrics, items completed
Tab 2 (Progress): progress.txt session block for the iteration's time range
Tab 3 (Git Diff): git commits with ``git show --stat`` output
Tab 4 (Cost Chart): cumulative cost sparkline across all iterations

Tabs switch via number keys 1-4 (delegated from app).

Clarity resolutions applied:
- Round 5: git commits matched by timestamp range
- Round 7: MetricsEntry 4-field format in overview
- Round 11: Textual Sparkline widget for cost chart, no extra dependencies
"""
from __future__ import annotations

import subprocess
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Sparkline, Static

from agent_replay.models import (
    CostEntry,
    Iteration,
    MetricsEntry,
    SessionBlock,
)

_TAB_NAMES: dict[int, str] = {
    1: "Overview",
    2: "Progress",
    3: "Git",
    4: "Cost Chart",
}


def _format_duration(td: timedelta) -> str:
    """Format a timedelta as Xh Ym Zs, omitting zero leading components."""
    total_seconds = int(td.total_seconds())
    if total_seconds <= 0:
        return "0s"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


class DetailPanel(Widget):
    """Right-panel widget: shows details of the selected iteration.

    Compose yields a header Static and 4 tab-content Static widgets.
    Only the active tab is visible (controlled by CSS class ``active``).
    """

    DEFAULT_CSS = """
    DetailPanel {
        height: 1fr;
        layout: vertical;
    }
    DetailPanel #detail-tab-header {
        text-style: bold;
        height: auto;
        padding-bottom: 1;
    }
    DetailPanel .tab-content {
        display: none;
        height: 1fr;
        overflow-y: auto;
    }
    DetailPanel .tab-content.active {
        display: block;
    }
    DetailPanel #cost-sparkline {
        height: 1fr;
    }
    DetailPanel #cost-chart-label {
        height: auto;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        project_dir: Path,
        iterations: list[Iteration],
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._project_dir = project_dir
        self._iterations = iterations
        self._active_tab: int = 1
        self._iteration: Iteration | None = None

    def compose(self) -> ComposeResult:
        yield Static("[1] Overview", id="detail-tab-header")
        yield Static(
            "Select an iteration", id="detail-tab-1", classes="tab-content active"
        )
        yield Static("", id="detail-tab-2", classes="tab-content")
        yield Static("", id="detail-tab-3", classes="tab-content")
        with Vertical(id="detail-tab-4", classes="tab-content"):
            yield Sparkline(None, id="cost-sparkline", summary_function=max)
            yield Static("", id="cost-chart-label")

    def show_tab(self, tab_number: int) -> None:
        """Switch to the given tab (1-4). Out-of-range values are ignored."""
        if tab_number < 1 or tab_number > 4:
            return
        self._active_tab = tab_number
        for i in range(1, 5):
            widget = self.query_one(f"#detail-tab-{i}")
            if i == tab_number:
                widget.add_class("active")
            else:
                widget.remove_class("active")
        self._update_header()

    def update_iteration(self, iteration: Iteration) -> None:
        """Render all tab contents for the given iteration."""
        self._iteration = iteration
        self._render_overview()
        self._render_progress()
        self._render_git()
        self._render_cost_chart()
        self._update_header()

    # ------------------------------------------------------------------
    # Private rendering helpers
    # ------------------------------------------------------------------

    def _update_header(self) -> None:
        name = _TAB_NAMES[self._active_tab]
        if self._iteration:
            text = f"[{self._active_tab}] {name} — Iteration #{self._iteration.number}"
        else:
            text = f"[{self._active_tab}] {name}"
        self.query_one("#detail-tab-header", Static).update(text)

    def _render_overview(self) -> None:
        it = self._iteration
        if it is None:
            self.query_one("#detail-tab-1", Static).update("Select an iteration")
            return

        # Extract model names from cost events
        models: set[str] = set()
        for ev in it.events:
            if ev.event_type == "cost" and isinstance(ev.data, CostEntry):
                models.add(ev.data.model)
        model_str = ", ".join(sorted(models)) if models else "unknown"

        lines: list[str] = [
            f"Phase:    {it.phase}",
            f"Status:   {it.status}",
            f"Model:    {model_str}",
            f"Tokens:   {it.tokens_in:,} in / {it.tokens_out:,} out",
            f"Cost:     ${it.cost_total:.2f}",
            f"Duration: {_format_duration(it.duration)}",
        ]

        if it.items_done:
            lines.append("")
            lines.append("Items completed:")
            for item in it.items_done:
                lines.append(f"  {item}")

        # Extract metrics from events
        metrics_lines: list[str] = []
        for ev in it.events:
            if ev.event_type == "metrics" and isinstance(ev.data, MetricsEntry):
                m = ev.data
                metrics_lines.append(f"  {m.metric}: {m.value} ({m.detail})")

        if metrics_lines:
            lines.append("")
            lines.append("Metrics:")
            lines.extend(metrics_lines)

        self.query_one("#detail-tab-1", Static).update("\n".join(lines))

    def _render_progress(self) -> None:
        it = self._iteration
        if it is None:
            self.query_one("#detail-tab-2", Static).update("")
            return

        blocks: list[str] = []
        for ev in it.events:
            if ev.event_type == "session" and isinstance(ev.data, SessionBlock):
                blocks.append(ev.data.content)

        if blocks:
            self.query_one("#detail-tab-2", Static).update("\n\n".join(blocks))
        else:
            self.query_one("#detail-tab-2", Static).update(
                "No progress data for this iteration"
            )

    def _render_git(self) -> None:
        it = self._iteration
        if it is None or not it.git_commits:
            self.query_one("#detail-tab-3", Static).update(
                "No git commits for this iteration"
            )
            return

        parts: list[str] = []
        for commit in it.git_commits:
            stat = self._git_show_stat(commit.hash)
            parts.append(f"commit {commit.hash[:8]} — {commit.message}\n{stat}")

        self.query_one("#detail-tab-3", Static).update("\n\n".join(parts))

    def _git_show_stat(self, commit_hash: str) -> str:
        """Run ``git show --stat --format= <hash>`` and return stdout."""
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--format=", commit_hash],
                capture_output=True,
                text=True,
                cwd=self._project_dir,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return "(no file changes)"
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            return "(git not available)"

    def _render_cost_chart(self) -> None:
        """Render cumulative cost sparkline for Tab 4.

        Computes cumulative cost across all session iterations and updates
        the Sparkline widget. The label shows the selected iteration's cost
        and its position in the cumulative total.

        Clarity Round 11: use Textual's built-in Sparkline, no extra deps.
        """
        sparkline = self.query_one("#cost-sparkline", Sparkline)
        label = self.query_one("#cost-chart-label", Static)

        if not self._iterations:
            sparkline.data = []
            label.update("No iteration data")
            return

        # Cumulative cost per iteration (all iterations, not just selected)
        cumulative_costs: list[float] = []
        running = Decimal("0")
        for it in self._iterations:
            running += it.cost_total
            cumulative_costs.append(float(running))

        sparkline.data = cumulative_costs

        # Label: selected iteration info + position in cumulative total
        it = self._iteration
        total = len(self._iterations)
        plural = "iteration" if total == 1 else "iterations"
        if it is not None:
            idx = it.number - 1
            if 0 <= idx < len(cumulative_costs):
                cum = cumulative_costs[idx]
                label.update(
                    f"Iteration #{it.number}  Cost: ${it.cost_total:.2f}"
                    f"  Cumulative: ${cum:.2f}"
                    f"  ({total} {plural} total)"
                )
            else:
                label.update(f"({total} {plural} total)")
        else:
            label.update(f"({total} {plural} total)")
