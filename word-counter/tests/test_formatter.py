"""Tests for src/word_counter/formatter.py."""
from __future__ import annotations

from word_counter.formatter import format_table


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def lines(output: str) -> list[str]:
    return output.split("\n")


# ---------------------------------------------------------------------------
# Basic structure
# ---------------------------------------------------------------------------


def test_output_has_header_separator_summary_for_nonempty():
    out = format_table([("hello", 3), ("world", 1)], total=4, unique=2)
    ls = lines(out)
    # header, separator, 2 data rows, summary = 5 lines
    assert len(ls) == 5


def test_output_has_header_separator_summary_for_empty():
    out = format_table([], total=0, unique=0)
    ls = lines(out)
    # header, separator, summary (no data rows) = 3 lines
    assert len(ls) == 3


def test_header_row_contains_column_labels():
    out = format_table([("the", 5)], total=5, unique=1)
    header = lines(out)[0]
    assert "#" in header
    assert "Word" in header
    assert "Count" in header
    assert "%" in header


def test_separator_row_uses_plus_sign():
    out = format_table([("the", 5)], total=5, unique=1)
    sep = lines(out)[1]
    assert "+" in sep
    assert all(c in "-+" for c in sep)


def test_summary_line_format():
    out = format_table([("the", 5)], total=5, unique=1)
    summary = lines(out)[-1]
    assert summary == "Total: 5 words, 1 unique words"


def test_summary_uses_passed_totals_not_derived():
    # total and unique come from the caller, not recomputed from frequencies
    out = format_table([("a", 2)], total=100, unique=50)
    summary = lines(out)[-1]
    assert summary == "Total: 100 words, 50 unique words"


# ---------------------------------------------------------------------------
# Ranks
# ---------------------------------------------------------------------------


def test_rank_column_right_aligned():
    out = format_table([("a", 3), ("b", 2), ("c", 1)], total=6, unique=3)
    data_rows = lines(out)[2:-1]
    # First data row should start with "1"
    assert data_rows[0].startswith("1")
    assert data_rows[1].startswith("2")
    assert data_rows[2].startswith("3")


def test_rank_width_adapts_to_number_of_entries():
    # 10 entries → max rank = 10, rank_w = max(1, 2) = 2
    freq = [(f"word{i}", 11 - i) for i in range(10)]
    total = sum(c for _, c in freq)
    out = format_table(freq, total=total, unique=10)
    header = lines(out)[0]
    # Header "#" must be right-aligned in at least 2 chars → starts with " #"
    assert header.startswith(" #")


# ---------------------------------------------------------------------------
# top_n limiting
# ---------------------------------------------------------------------------


def test_top_n_limits_rows():
    freq = [("a", 5), ("b", 4), ("c", 3), ("d", 2), ("e", 1)]
    out = format_table(freq, total=15, unique=5, top_n=3)
    data_rows = lines(out)[2:-1]
    assert len(data_rows) == 3


def test_top_n_takes_first_entries():
    freq = [("a", 5), ("b", 4), ("c", 3)]
    out = format_table(freq, total=12, unique=3, top_n=2)
    data_rows = lines(out)[2:-1]
    assert "a" in data_rows[0]
    assert "b" in data_rows[1]


def test_top_n_larger_than_entries_shows_all():
    freq = [("hello", 2), ("world", 1)]
    out = format_table(freq, total=3, unique=2, top_n=100)
    data_rows = lines(out)[2:-1]
    assert len(data_rows) == 2


# ---------------------------------------------------------------------------
# Percentages
# ---------------------------------------------------------------------------


def test_percentage_one_decimal_place():
    out = format_table([("the", 1)], total=3, unique=1)
    data_rows = lines(out)[2:-1]
    # 1/3 * 100 = 33.333… → "33.3%"
    assert "33.3%" in data_rows[0]


def test_percentage_exactly_100():
    out = format_table([("only", 7)], total=7, unique=1)
    data_rows = lines(out)[2:-1]
    assert "100.0%" in data_rows[0]


def test_percentage_rounds_correctly():
    # 2/3 * 100 = 66.666… → "66.7%"
    out = format_table([("a", 2)], total=3, unique=1)
    data_rows = lines(out)[2:-1]
    assert "66.7%" in data_rows[0]


def test_zero_total_shows_zero_percent():
    # Defensive: total=0 but non-empty frequencies shouldn't happen in practice;
    # if it does, formatter should not crash and shows 0.0%
    out = format_table([("ghost", 0)], total=0, unique=1)
    data_rows = lines(out)[2:-1]
    assert "0.0%" in data_rows[0]


# ---------------------------------------------------------------------------
# Column widths adapt to content
# ---------------------------------------------------------------------------


def test_word_column_adapts_to_long_word():
    long_word = "antidisestablishmentarianism"
    out = format_table([(long_word, 1)], total=1, unique=1)
    data_rows = lines(out)[2:-1]
    assert long_word in data_rows[0]
    # separator should be at least as wide as the long word + surrounding chars
    sep = lines(out)[1]
    assert len(sep) >= len(long_word)


def test_count_column_adapts_to_large_count():
    out = format_table([("the", 1_000_000)], total=1_000_000, unique=1)
    data_rows = lines(out)[2:-1]
    assert "1000000" in data_rows[0]


def test_columns_consistent_width_across_rows():
    freq = [("hi", 10), ("superlongword", 1)]
    out = format_table(freq, total=11, unique=2)
    ls = lines(out)
    header, sep, row1, row2, _summary = ls
    # All content lines (header, sep, data) should have same total width
    assert len(header) == len(sep) == len(row1) == len(row2)


# ---------------------------------------------------------------------------
# Zero-word edge case
# ---------------------------------------------------------------------------


def test_zero_words_has_correct_summary():
    out = format_table([], total=0, unique=0)
    assert "Total: 0 words, 0 unique words" in out


def test_zero_words_has_no_data_rows():
    out = format_table([], total=0, unique=0)
    ls = lines(out)
    assert len(ls) == 3  # header, sep, summary only


# ---------------------------------------------------------------------------
# Alignment
# ---------------------------------------------------------------------------


def test_number_columns_right_aligned():
    # Count column: "3" should be right-aligned under "Count" (5 chars)
    out = format_table([("a", 3)], total=3, unique=1)
    header = lines(out)[0]
    row = lines(out)[2]
    # Find position of "Count" header and "3" data — they should end at same column
    # Split on " | " and check third field has uniform width
    header_fields = header.split(" | ")
    row_fields = row.split(" | ")
    assert len(header_fields[2]) == len(row_fields[2])
