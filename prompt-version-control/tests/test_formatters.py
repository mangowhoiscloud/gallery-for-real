"""Tests for src/prompt_vc/formatters.py."""

import pytest

from prompt_vc.formatters import (
    UnsupportedFormatError,
    apply_format,
    format_html,
    format_markdown,
    format_terminal,
)

# ---------------------------------------------------------------------------
# Shared sample outputs (mirrors real compare / trend terminal output)
# ---------------------------------------------------------------------------

COMPARE_TERMINAL = """\
=== Prompt A/B Comparison: v1 vs v2 ===

Benchmark: word-counter
Metric               v1             v2             Δ
----------------------------------------------------
latency              1.5000         2.0000         +0.5000 (+33.33%)
success              True           False          True→False

Winner: v2 (1/1 numeric metrics improved)
Key Change: "improved prompts"\
"""

TREND_TERMINAL = """\
=== Metric Trend ===

Benchmark: word-counter
Metric               v1             v2
----------------------------------------------------
latency              1.5000         2.0000        \
"""


# ---------------------------------------------------------------------------
# format_terminal
# ---------------------------------------------------------------------------


def test_format_terminal_passthrough_compare():
    assert format_terminal(COMPARE_TERMINAL) == COMPARE_TERMINAL


def test_format_terminal_passthrough_trend():
    assert format_terminal(TREND_TERMINAL) == TREND_TERMINAL


# ---------------------------------------------------------------------------
# format_html
# ---------------------------------------------------------------------------


def test_format_html_contains_doctype():
    result = format_html(COMPARE_TERMINAL)
    assert "<!DOCTYPE html>" in result


def test_format_html_contains_html_head_body_tags():
    result = format_html(COMPARE_TERMINAL)
    assert "<html" in result
    assert "<head>" in result
    assert "<body>" in result


def test_format_html_contains_pre_tag():
    result = format_html(COMPARE_TERMINAL)
    assert "<pre>" in result
    assert "</pre>" in result


def test_format_html_embeds_content():
    result = format_html(COMPARE_TERMINAL)
    assert "Prompt A/B Comparison" in result
    assert "latency" in result


def test_format_html_uses_custom_title():
    result = format_html(COMPARE_TERMINAL, title="My Report")
    assert "<title>My Report</title>" in result


def test_format_html_default_title():
    result = format_html(COMPARE_TERMINAL)
    assert "<title>prompt-vc report</title>" in result


def test_format_html_trend():
    result = format_html(TREND_TERMINAL, title="trend")
    assert "<!DOCTYPE html>" in result
    assert "Metric Trend" in result
    assert "<pre>" in result


def test_format_html_escapes_angle_brackets():
    result = format_html("output: <test>")
    assert "<test>" not in result
    assert "&lt;test&gt;" in result


# ---------------------------------------------------------------------------
# format_markdown
# ---------------------------------------------------------------------------


def test_format_markdown_converts_section_header():
    result = format_markdown(COMPARE_TERMINAL)
    assert "## Prompt A/B Comparison: v1 vs v2" in result
    # original === syntax should be gone
    assert "===" not in result


def test_format_markdown_trend_section_header():
    result = format_markdown(TREND_TERMINAL)
    assert "## Metric Trend" in result


def test_format_markdown_pipe_table_header_row():
    result = format_markdown(COMPARE_TERMINAL)
    assert "| Metric | v1 | v2 | Δ |" in result


def test_format_markdown_separator_row():
    result = format_markdown(COMPARE_TERMINAL)
    assert "| --- |" in result


def test_format_markdown_data_row_as_pipe():
    result = format_markdown(COMPARE_TERMINAL)
    assert "| latency |" in result
    assert "| 1.5000 |" in result


def test_format_markdown_no_raw_separator_line():
    """The ---- separator line should not appear in markdown output."""
    result = format_markdown(COMPARE_TERMINAL)
    for line in result.splitlines():
        assert not line.startswith("----"), f"raw separator found: {line!r}"


def test_format_markdown_winner_line_preserved():
    result = format_markdown(COMPARE_TERMINAL)
    assert "Winner: v2" in result


def test_format_markdown_key_change_preserved():
    result = format_markdown(COMPARE_TERMINAL)
    assert 'Key Change: "improved prompts"' in result


def test_format_markdown_benchmark_label_preserved():
    result = format_markdown(COMPARE_TERMINAL)
    assert "Benchmark: word-counter" in result


def test_format_markdown_trend_pipe_table():
    result = format_markdown(TREND_TERMINAL)
    assert "| Metric | v1 | v2 |" in result
    assert "| --- |" in result
    assert "| latency |" in result


def test_format_markdown_no_equals_signs():
    result = format_markdown(TREND_TERMINAL)
    assert "===" not in result


# ---------------------------------------------------------------------------
# apply_format dispatch
# ---------------------------------------------------------------------------


def test_apply_format_terminal():
    result = apply_format(COMPARE_TERMINAL, "terminal")
    assert result == COMPARE_TERMINAL


def test_apply_format_html():
    result = apply_format(COMPARE_TERMINAL, "html", title="test")
    assert "<!DOCTYPE html>" in result
    assert "<title>test</title>" in result


def test_apply_format_markdown():
    result = apply_format(COMPARE_TERMINAL, "markdown")
    assert "## Prompt A/B Comparison" in result
    assert "| Metric |" in result


def test_apply_format_unknown_raises():
    with pytest.raises(UnsupportedFormatError, match="Unknown format"):
        apply_format(COMPARE_TERMINAL, "pdf")


def test_apply_format_unknown_lists_supported():
    with pytest.raises(UnsupportedFormatError, match="html"):
        apply_format(COMPARE_TERMINAL, "pdf")
