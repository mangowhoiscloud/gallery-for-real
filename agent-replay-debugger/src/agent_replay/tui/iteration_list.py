"""TUI widget: iteration list for the left panel.

Displays each iteration as a flat chronological row:
  icon  #N  phase  $cost

Keyboard navigation: j/k (delegated from app) or up/down arrows (native
when the widget has focus). Enter selects the current item.

Emits IterationList.SelectionChanged when the highlighted iteration changes.

Clarity resolution Round 10: flat chronological list (no phase grouping).
"""
from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ListItem, ListView, Static

from agent_replay.models import Iteration

_STATUS_ICONS: dict[str, str] = {
    "OK": "✓",
    "FAIL": "✗",
    "STUCK": "⚡",
}


def _format_row(it: Iteration) -> str:
    """Format one iteration as a fixed-width display row.

    Example: "✓ #  1  build        $0.50"
    """
    icon = _STATUS_ICONS.get(it.status, "?")
    cost = f"${it.cost_total:.2f}"
    return f"{icon} #{it.number:<3}  {it.phase:<12}  {cost}"


class IterationList(Widget):
    """Left-panel widget: flat chronological list of all iterations.

    Wraps a Textual ListView to handle selection tracking and emit
    IterationList.SelectionChanged when the highlighted row changes.
    """

    DEFAULT_CSS = """
    IterationList ListView {
        height: 1fr;
        border: none;
    }
    """

    class SelectionChanged(Message):
        """Posted when the highlighted iteration changes.

        Consumers handle this via on_iteration_list_selection_changed.
        """

        def __init__(self, iteration: Iteration) -> None:
            super().__init__()
            self.iteration = iteration

    def __init__(self, iterations: list[Iteration], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._iterations = iterations
        # Map item CSS id → Iteration for O(1) lookup in message handler
        self._iter_map: dict[str, Iteration] = {
            f"iter-{it.number}": it for it in iterations
        }

    def compose(self) -> ComposeResult:
        items: list[ListItem] = []
        for it in self._iterations:
            item_id = f"iter-{it.number}"
            items.append(ListItem(Static(_format_row(it)), id=item_id))
        yield ListView(*items, id="iteration-listview")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Translate inner ListView highlight into SelectionChanged message."""
        event.stop()
        if event.item is not None and event.item.id:
            iteration = self._iter_map.get(event.item.id)
            if iteration is not None:
                self.post_message(IterationList.SelectionChanged(iteration))

    def cursor_down(self) -> None:
        """Move cursor down one row.

        Called by ReplayApp.action_cursor_down (j / down-arrow bindings).
        """
        if self._iterations:
            self.query_one(ListView).action_cursor_down()

    def cursor_up(self) -> None:
        """Move cursor up one row.

        Called by ReplayApp.action_cursor_up (k / up-arrow bindings).
        """
        if self._iterations:
            self.query_one(ListView).action_cursor_up()

    def jump_to(self, iteration_number: int) -> bool:
        """Move cursor to the iteration with the given number.

        Sets ListView.index so the existing on_list_view_highlighted handler
        fires and emits SelectionChanged, updating the detail panel.

        Returns True if the iteration was found and jumped to, False otherwise.
        """
        for idx, it in enumerate(self._iterations):
            if it.number == iteration_number:
                self.query_one(ListView).index = idx
                return True
        return False

    @property
    def selected_iteration(self) -> Iteration | None:
        """The currently highlighted iteration, or None if the list is empty."""
        try:
            lv = self.query_one(ListView)
            idx = lv.index
            if idx is not None and 0 <= idx < len(self._iterations):
                return self._iterations[idx]
        except Exception:
            pass
        return None
