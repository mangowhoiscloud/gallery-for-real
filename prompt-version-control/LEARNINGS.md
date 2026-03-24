# LEARNINGS

Runtime discoveries from implementation iterations. Read this before starting each session.

### Learning: ruff F401 — don't import pytest unless decorators/fixtures used directly
- Context: Writing test files
- Discovery: ruff flags `import pytest` as unused if no `@pytest.mark.*` decorators or direct fixture refs appear. tmp_path fixture works without importing pytest.
- Rule: Only `import pytest` when using `pytest.raises`, `pytest.mark.*`, or `pytest.fixture` directly. Otherwise omit.

### Learning: ensure_store should be idempotent; init command owns "already initialized" error
- Context: Designing storage.py vs init command boundary
- Discovery: Naming a function "ensure_X" implies idempotent creation. The init command checks `is_initialized()` and raises a user-friendly error. Keeping storage layer dumb and reusable is cleaner.
- Rule: Storage primitives use exist_ok=True. Command layer owns validation/error messages.

### Learning: YAML null deserialization requires defensive `.get() or {}`
- Context: Deserializing VersionMeta from YAML
- Discovery: YAML `null` deserializes to Python `None`. Using `d.get("files", {})` still returns None if the key exists with value null. Use `d.get("files") or {}` instead.
- Rule: For dict/list fields from YAML, use `data.get("key") or default` not `data.get("key", default)`.

### Learning: Python bool is subclass of int — check bool BEFORE int/float in type dispatch
- Context: Formatting metric deltas in compare command
- Discovery: `isinstance(True, (int, float))` returns True. If you check `isinstance(val, (int, float))` first, booleans get treated as 1/0 for arithmetic, giving wrong deltas (e.g. "True - True = 0" shown as "+0" instead of "—").
- Rule: In type dispatch, always guard `isinstance(val, bool)` before `isinstance(val, (int, float))` to correctly handle boolean metrics separately from numeric ones.

### Learning: bind test data must be flat — no nested "metrics" key
- Context: Writing tests for trend/compare commands that use bind()
- Discovery: bind() puts all fields except benchmark/agent/timestamp into the "metrics" dict. If test data has `"metrics": {"latency": 1.5}`, that creates `metrics.metrics = {"latency": 1.5}` (a dict-valued metric) instead of `metrics.latency = 1.5`. The stored YAML shows `metrics: {metrics: {latency: 1.5}}`.
- Rule: When writing result JSON for bind tests, put custom metrics at the top level (e.g., `"latency": 1.5`, not `"metrics": {"latency": 1.5}`). The compare command tests follow this pattern correctly.

### Learning: Jinja2 autoescape is off by default with BaseLoader — use | e explicitly
- Context: Writing format_html with Jinja2 template
- Discovery: `Environment(loader=BaseLoader(), autoescape=False)` is the default. HTML chars in content (< > &) are not escaped unless you use `{{ content | e }}` in the template.
- Rule: Either set autoescape=True (auto-escapes all {{ }} vars) or use `{{ content | e }}` explicitly. Always choose one of these when rendering user content into HTML.

### Learning: Split fixed-width table on 2+ spaces to extract columns reliably
- Context: Writing format_markdown that converts terminal table output to markdown pipe tables
- Discovery: `re.split(r"  +", line.rstrip())` splits on 2 or more consecutive spaces. Fixed-width table columns always have at least 2 spaces between them (padding + separator) unless a value fills its entire column. For typical metric names/values this is reliable.
- Rule: For parsing fixed-width terminal table output back to columns, use `re.split(r"  +", line.rstrip())` and filter empty strings. Filter with `[c.strip() for c in cols if c.strip()]`.
