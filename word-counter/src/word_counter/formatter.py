"""Formatter: render word-frequency results as a table."""
from __future__ import annotations


def format_table(
    frequencies: list[tuple[str, int]],
    total: int,
    unique: int,
    top_n: int = 10,
) -> str:
    """Render a frequency table with a summary line.

    Args:
        frequencies: Pre-sorted list of (word, count) tuples.
        total:       Total word count (used for percentage calculation and summary).
        unique:      Unique word count (used for summary line only).
        top_n:       Maximum number of rows to display.

    Returns:
        A multi-line string: header, separator, up to top_n data rows, summary.
    """
    entries = frequencies[:top_n]
    n = len(entries)

    # --- compute percentage strings before measuring widths ---
    pct_strs: list[str] = []
    for _word, count in entries:
        pct = (count / total * 100) if total > 0 else 0.0
        pct_strs.append(f"{pct:.1f}%")

    # --- adaptive column widths ---
    rank_w = max(len("#"), len(str(n)) if n > 0 else 1)
    word_w = max(len("Word"), max((len(w) for w, _ in entries), default=0))
    count_w = max(len("Count"), max((len(str(c)) for _, c in entries), default=0))
    pct_w = max(len("%"), max((len(p) for p in pct_strs), default=0))

    # --- header ---
    header = (
        f"{'#':>{rank_w}} | {'Word':<{word_w}} | {'Count':>{count_w}} | {'%':>{pct_w}}"
    )

    # --- separator ---
    # Each column section in data/header: A chars + ` | ` → separator replaces with dashes+`+`
    # Pattern: {rank_w+1 dashes}+{word_w+2 dashes}+{count_w+2 dashes}+{pct_w+1 dashes}
    sep = (
        f"{'-' * (rank_w + 1)}"
        f"+{'-' * (word_w + 2)}"
        f"+{'-' * (count_w + 2)}"
        f"+{'-' * (pct_w + 1)}"
    )

    # --- data rows ---
    rows: list[str] = []
    for i, ((word, count), pct_str) in enumerate(zip(entries, pct_strs), 1):
        rows.append(
            f"{i:>{rank_w}} | {word:<{word_w}} | {count:>{count_w}} | {pct_str:>{pct_w}}"
        )

    # --- summary ---
    summary = f"Total: {total} words, {unique} unique words"

    return "\n".join([header, sep, *rows, summary])
