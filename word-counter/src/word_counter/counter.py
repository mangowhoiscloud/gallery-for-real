"""Counter: compute word frequency statistics."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class CountResult:
    """Result of counting words.

    Attributes:
        frequencies: List of (word, count) tuples sorted by count descending,
                     then alphabetically ascending on ties.
        total:       Total number of word tokens (sum of all counts).
        unique:      Number of distinct words.
    """

    frequencies: list[tuple[str, int]]
    total: int
    unique: int


def count_words(words: list[str], ignore_case: bool = False) -> CountResult:
    """Count word frequencies.

    Args:
        words:       Ordered list of word tokens (e.g. from :func:`tokenize`).
        ignore_case: When *True*, all words are lowercased before counting
                     and the returned frequencies use the lowercased forms.

    Returns:
        A :class:`CountResult` with frequencies sorted by count (desc),
        then alphabetically (asc) on ties.
    """
    if ignore_case:
        words = [w.lower() for w in words]

    counts: Counter[str] = Counter(words)

    # Sort: primary = count descending, secondary = word ascending
    sorted_frequencies = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    return CountResult(
        frequencies=sorted_frequencies,
        total=sum(counts.values()),
        unique=len(counts),
    )
