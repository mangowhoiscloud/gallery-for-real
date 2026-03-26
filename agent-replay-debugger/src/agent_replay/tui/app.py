"""Textual TUI application for agent session replay debugging.

Layout:
  - Header: project name, total iterations, total cost, total time
  - Left panel: iteration list (placeholder — implemented in Item 16)
  - Right panel: detail panel (placeholder — implemented in Item 17)
  - Footer: keybindings (q=quit, j/k=up/down, 1-4=tab switch, /=search)

Clarity resolutions applied:
- Round 10: flat chronological iteration list (no phase grouping)
- Round 14: empty session → "Empty session — no iteration data found"
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Input, Static

from agent_replay.models import Iteration, SessionBlock
from agent_replay.tui.detail_panel import DetailPanel
from agent_replay.tui.iteration_list import IterationList


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


class ReplayApp(App[None]):
    """Main TUI application for agent session replay debugging."""

    CSS = """
    #main-container {
        height: 1fr;
    }
    #left-panel {
        width: 1fr;
        min-width: 30;
        border-right: solid $accent;
        padding: 1;
    }
    #right-panel {
        width: 2fr;
        padding: 1;
    }
    #empty-message {
        width: 1fr;
        height: 1fr;
        content-align: center middle;
        text-style: italic;
        padding: 1;
    }
    #search-bar {
        height: auto;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("j", "cursor_down", "Down", show=True),
        Binding("k", "cursor_up", "Up", show=True),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("1", "tab_1", "Overview", show=True),
        Binding("2", "tab_2", "Progress", show=True),
        Binding("3", "tab_3", "Git", show=True),
        Binding("4", "tab_4", "Cost", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("escape", "close_search", "Close Search", show=False, priority=True),
    ]

    def __init__(
        self,
        project_dir: Path,
        iterations: list[Iteration],
    ) -> None:
        super().__init__()
        self.project_dir = project_dir
        self.iterations = iterations
        self._selected_iteration: Iteration | None = None
        self._search_matches: list[int] = []
        self._search_keyword: str = ""
        self._search_idx: int = 0

    @property
    def _total_cost(self) -> Decimal:
        return sum((it.cost_total for it in self.iterations), Decimal("0"))

    @property
    def _total_duration(self) -> timedelta:
        return sum((it.duration for it in self.iterations), timedelta())

    def on_mount(self) -> None:
        """Set title and subtitle with session stats once the app is mounted."""
        self.title = self.project_dir.name
        total = len(self.iterations)
        cost = f"${self._total_cost:.2f}"
        duration = _format_duration(self._total_duration)
        self.sub_title = f"{total} iterations | {cost} | {duration}"

    def compose(self) -> ComposeResult:
        yield Header()
        if not self.iterations:
            yield Static(
                "Empty session — no iteration data found", id="empty-message"
            )
        else:
            with Horizontal(id="main-container"):
                yield IterationList(self.iterations, id="left-panel")
                yield DetailPanel(
                    self.project_dir, self.iterations, id="right-panel"
                )
        yield Footer()

    def on_iteration_list_selection_changed(
        self, event: IterationList.SelectionChanged
    ) -> None:
        """Update detail panel when a different iteration is selected."""
        self._selected_iteration = event.iteration
        try:
            self.query_one(DetailPanel).update_iteration(event.iteration)
        except Exception:
            pass

    def action_cursor_down(self) -> None:
        """Move cursor down in iteration list."""
        try:
            self.query_one(IterationList).cursor_down()
        except Exception:
            pass

    def action_cursor_up(self) -> None:
        """Move cursor up in iteration list."""
        try:
            self.query_one(IterationList).cursor_up()
        except Exception:
            pass

    def action_tab_1(self) -> None:
        """Switch to Overview tab."""
        try:
            self.query_one(DetailPanel).show_tab(1)
        except Exception:
            pass

    def action_tab_2(self) -> None:
        """Switch to Progress tab."""
        try:
            self.query_one(DetailPanel).show_tab(2)
        except Exception:
            pass

    def action_tab_3(self) -> None:
        """Switch to Git tab."""
        try:
            self.query_one(DetailPanel).show_tab(3)
        except Exception:
            pass

    def action_tab_4(self) -> None:
        """Switch to Cost tab."""
        try:
            self.query_one(DetailPanel).show_tab(4)
        except Exception:
            pass

    async def action_search(self) -> None:
        """Mount and focus search bar for text input.

        If the bar is already mounted (user pressed / twice), just focus it.
        The bar is mounted dynamically to avoid DOM-level focus interference
        with numeric tab-switch bindings (1-4) when hidden.
        """
        try:
            bar = self.query_one("#search-bar", Input)
            bar.focus()
            return
        except Exception:
            pass
        bar = Input(
            placeholder="Search progress.txt... (Enter=jump, Esc=close)",
            id="search-bar",
        )
        await self.mount(bar, before=self.query_one(Footer))
        bar.focus()

    def action_close_search(self) -> None:
        """Remove search bar and return focus to iteration list."""
        try:
            self.query_one("#search-bar", Input).remove()
        except Exception:
            pass
        try:
            self.query_one(IterationList).focus()
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter in the search bar.

        If the keyword matches the previous search, cycle to the next match.
        Otherwise start a fresh search.

        Clarity Round 12: search scoped to progress.txt SessionBlock content.
        """
        if event.input.id != "search-bar":
            return
        keyword = event.value.strip()
        if not keyword:
            return
        if keyword == self._search_keyword and self._search_matches:
            # Same keyword: advance to next match (cycle)
            self._search_idx = (self._search_idx + 1) % len(self._search_matches)
            self._jump_to_match()
        else:
            # New keyword: find all matching iterations from scratch
            self._search_keyword = keyword
            self._search_matches = self._find_matches(keyword)
            self._search_idx = 0
            if not self._search_matches:
                self.notify(f"No matches for '{keyword}'", severity="warning")
            else:
                self._jump_to_match()

    def _find_matches(self, keyword: str) -> list[int]:
        """Return iteration numbers whose session block content contains keyword.

        Case-insensitive. Each iteration is included at most once.
        """
        kw = keyword.lower()
        matches: list[int] = []
        for it in self.iterations:
            for ev in it.events:
                if ev.event_type == "session" and isinstance(ev.data, SessionBlock):
                    if kw in ev.data.content.lower():
                        matches.append(it.number)
                        break
        return matches

    def _jump_to_match(self) -> None:
        """Jump iteration list cursor to the current match and notify user."""
        if not self._search_matches:
            return
        iter_num = self._search_matches[self._search_idx]
        try:
            self.query_one(IterationList).jump_to(iter_num)
        except Exception:
            pass
        total = len(self._search_matches)
        self.notify(
            f"Match {self._search_idx + 1}/{total} — iteration #{iter_num}",
            timeout=2,
        )
