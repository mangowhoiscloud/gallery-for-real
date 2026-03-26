# Learnings — Agent Replay Debugger

### Learning: Ruff E741 — ambiguous variable name in list comprehensions
- Context: Writing test_fixtures.py with list comprehensions over log file lines
- Discovery: ruff flags single-letter variable `l` as ambiguous (E741), even in list comprehensions
- Rule: Use `ln` (not `l`) for "line" loop variables in list comprehensions

### Learning: phase.log CIRCUIT_BREAKER format includes free text
- Context: Creating fixture phase.log based on CLARITY_LOG examples
- Discovery: CIRCUIT_BREAKER event lines mix free text with key=value: `event=CIRCUIT_BREAKER Stuck 1 iteration, phase=build`. The rest-of-line capture group in the parser regex `(?P<rest>.*)` handles this.
- Rule: phase.log fixtures must include this mixed-format CIRCUIT_BREAKER line to test parser robustness

### Learning: cost.log token counts are raw integers, not thousands
- Context: Verifying fixture cost.log values against actual harness-logs/cost.log
- Discovery: `in=15 out=8500` means 15 input tokens and 8500 output tokens (not 15K/8500K). Math: 15*$0.000015 + 8500*$0.000075 ≈ $0.6384 confirms raw counts.
- Rule: Generate fixture cost values with small `in` values (10-30 tokens) and larger `out` values (8000-12000 tokens) for opus; similar scale for sonnet with its lower prices.

### Learning: Textual pilot tests require pytest-asyncio
- Context: Writing TUI tests with Textual's run_test() async context manager
- Discovery: `async with app.run_test() as pilot:` requires pytest-asyncio for `@pytest.mark.asyncio`. Textual 8.1.1 is the installed version (pyproject.toml pins >=3.0.0 but uv resolves 8.1.1). Static widget text can be extracted via `widget.render().plain` for assertions.
- Rule: TUI tests need pytest-asyncio in dev deps. Use `app.run_test()` as the standard pattern. Assert rendered text via `.render().plain`.

### Learning: Textual ListView auto-selects first item on mount
- Context: Writing detail panel tests expecting initial "Select an iteration" placeholder
- Discovery: ListView auto-highlights item 0 on mount, which triggers `on_list_view_highlighted` → `SelectionChanged` → `update_iteration()` before any user interaction. The initial placeholder text is immediately overwritten.
- Rule: When testing initial TUI state with a non-empty iteration list, expect the first iteration's data to already be displayed. Don't test for placeholder text that gets auto-replaced.

### Learning: Avoid circular imports between TUI modules via local helpers
- Context: DetailPanel needs `_format_duration` defined in app.py, but app.py imports DetailPanel
- Discovery: Importing `_format_duration` from app.py in detail_panel.py creates a circular import since app.py imports DetailPanel at the top level.
- Rule: For small utility functions shared between TUI modules, duplicate them locally rather than creating a shared utils module or risking circular imports. Extract to a shared module only when 3+ consumers exist.

### Learning: Textual Input in compose intercepts all printable keypresses
- Context: Adding a search Input widget to ReplayApp.compose() for Item 19
- Discovery: In Textual 8.1.1, any Input widget in the DOM — even with CSS `display: none` or `widget.display = False` set in on_mount — intercepts printable character keypresses (digits 1-9, letters, "/") before App-level BINDINGS fire. This silently broke tab-switch bindings (1-4) and the slash search binding.
- Rule: For transient input widgets (dialogs, search bars) in Textual 8, use dynamic mount/unmount (`await self.mount(bar, before=footer)` / `bar.remove()`) rather than permanently composing them hidden. Only mount the Input when it's actually needed.

### Learning: async action_* methods work natively in Textual 8
- Context: action_search() needed to await self.mount() for dynamic Input mounting
- Discovery: Textual 8 BINDINGS call async action_* methods by awaiting them. Defining `async def action_search(self)` works transparently — no special registration needed. In tests, await `app.action_search()` directly instead of pilot.press() when the key binding is complex to simulate.
- Rule: Use async action methods whenever the action needs to await Textual APIs (mount, query, animations). Tests can call `await app.action_<name>()` directly to bypass key routing.
