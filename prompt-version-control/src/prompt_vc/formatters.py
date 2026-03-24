"""Output formatters: terminal (default), HTML (jinja2), and markdown."""

import re

from jinja2 import BaseLoader, Environment

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <style>
        body { font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
        pre { background: #16213e; padding: 1rem; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <pre>{{ content | e }}</pre>
</body>
</html>
"""

SUPPORTED_FORMATS = frozenset({"terminal", "html", "markdown"})


class UnsupportedFormatError(ValueError):
    """Raised when an unknown output format is requested."""


def format_terminal(content: str) -> str:
    """Return content unchanged (terminal/plain-text format)."""
    return content


def format_html(content: str, title: str = "prompt-vc report") -> str:
    """Wrap plain-text content in a styled HTML page using Jinja2."""
    env = Environment(loader=BaseLoader(), autoescape=False)
    template = env.from_string(_HTML_TEMPLATE)
    return template.render(title=title, content=content)


def _split_fixed_cols(line: str) -> list[str]:
    """Split a fixed-width table line on runs of 2+ spaces, stripping empties."""
    cols = re.split(r"  +", line.rstrip())
    return [c.strip() for c in cols if c.strip()]


def format_markdown(content: str) -> str:
    """Convert terminal-formatted compare/trend output to markdown with pipe tables."""
    lines = content.splitlines()
    result: list[str] = []
    in_table = False

    for line in lines:
        # Section headers: === title === → ## title
        m = re.match(r"^=== (.+) ===$", line)
        if m:
            result.append(f"## {m.group(1)}")
            in_table = False
            continue

        # Separator line (e.g. "----...") → convert previous line to pipe header
        if re.match(r"^-{3,}\s*$", line):
            if result and not result[-1].startswith("|"):
                header = result.pop()
                cols = _split_fixed_cols(header)
                result.append("| " + " | ".join(cols) + " |")
                result.append("| " + " | ".join(["---"] * len(cols)) + " |")
                in_table = True
            continue

        # Data rows while inside a table (ends on blank line)
        if in_table:
            if not line.strip():
                in_table = False
                result.append(line)
            else:
                cols = _split_fixed_cols(line)
                result.append("| " + " | ".join(cols) + " |")
            continue

        result.append(line)

    return "\n".join(result)


def apply_format(content: str, fmt: str, title: str = "prompt-vc report") -> str:
    """Apply the requested output format to content.

    Args:
        content: Terminal-formatted string produced by compare() or trend().
        fmt: One of "terminal", "html", "markdown".
        title: Title used in HTML output.

    Returns:
        Formatted string.

    Raises:
        UnsupportedFormatError: If fmt is not in SUPPORTED_FORMATS.
    """
    if fmt == "terminal":
        return format_terminal(content)
    if fmt == "html":
        return format_html(content, title)
    if fmt == "markdown":
        return format_markdown(content)
    raise UnsupportedFormatError(
        f"Unknown format '{fmt}'. Supported: {sorted(SUPPORTED_FORMATS)}"
    )
