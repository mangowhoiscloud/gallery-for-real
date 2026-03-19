"""Tokenizer: extract words from text.

Word definition (from specs/word-definition.md + CLARITY_LOG.md):
- A word is a maximal sequence of Unicode alphanumeric characters, optionally
  joined by intra-word apostrophes (apostrophes flanked by alphanumeric chars
  on both sides).
- Hyphens (any number) split words; empty segments are discarded.
- Underscores are not alphanumeric and act as word separators.
- Leading/trailing apostrophes are stripped automatically by the regex.
- Unicode-aware: matches accented letters, non-ASCII digits, etc.
"""
import re

# Matches a maximal "word" token:
#   [^\W_']+          — one or more Unicode alphanumeric chars (no underscore, no apostrophe)
#   (?:'[^\W_']+)*    — zero or more groups of: apostrophe + alphanumeric chars
#
# This naturally handles:
#   - Leading apostrophes: the pattern must START with alphanumeric, so 'twas → twas
#   - Trailing apostrophes: the pattern must END with alphanumeric, so dogs' → dogs
#   - Intra-word apostrophes: don't → don't (apostrophe between alphanumerics)
#   - Multiple hyphens/underscores: act as separators, never captured
_WORD_RE = re.compile(r"[^\W_']+(?:'[^\W_']+)*")


def tokenize(text: str) -> list[str]:
    """Extract words from *text* according to the word-definition spec.

    Args:
        text: Arbitrary Unicode text.

    Returns:
        Ordered list of word tokens extracted from *text*.
    """
    return _WORD_RE.findall(text)
