"""Tests for the tokenizer module.

Covers all word-definition rules from specs/word-definition.md and all
clarity resolutions from CLARITY_LOG.md (Rounds 1, 5, 10, 11).
Target: ≥30 test cases.
"""
from word_counter.tokenizer import tokenize


# ---------------------------------------------------------------------------
# Acceptance criteria from IMPLEMENTATION_PLAN.md
# ---------------------------------------------------------------------------

def test_basic_punctuation_stripped():
    assert tokenize("hello, world!") == ["hello", "world"]


def test_intraword_apostrophe_kept():
    """CLARITY_LOG Round 1: apostrophe between two alphanumerics is kept."""
    assert tokenize("don't") == ["don't"]


def test_leading_apostrophe_stripped():
    """CLARITY_LOG Round 1: leading apostrophe stripped from 'twas."""
    assert tokenize("'twas dogs'") == ["twas", "dogs"]


def test_hyphen_splits_words():
    """specs/word-definition.md: hyphens split words."""
    assert tokenize("well-known") == ["well", "known"]


def test_multiple_hyphens_no_empty_tokens():
    """CLARITY_LOG Round 10: multiple consecutive hyphens produce no empty tokens."""
    assert tokenize("word--break") == ["word", "break"]


def test_numbers_are_words():
    """specs/word-definition.md: numbers count as words."""
    assert tokenize("42 is a number") == ["42", "is", "a", "number"]


def test_unicode_letters():
    """CLARITY_LOG Round 5: Unicode-aware matching."""
    assert tokenize("café naïve") == ["café", "naïve"]


def test_underscore_splits_words():
    """CLARITY_LOG Round 11: underscores are not alphanumeric; act as separators."""
    assert tokenize("my_variable") == ["my", "variable"]


def test_empty_string():
    assert tokenize("") == []


# ---------------------------------------------------------------------------
# Apostrophe edge cases (CLARITY_LOG Round 1)
# ---------------------------------------------------------------------------

def test_trailing_apostrophe_stripped():
    assert tokenize("trailing'") == ["trailing"]


def test_apostrophe_only():
    assert tokenize("'") == []


def test_double_apostrophe_only():
    assert tokenize("''") == []


def test_apostrophe_between_alphanumerics():
    assert tokenize("o'clock") == ["o'clock"]


def test_multiple_contractions():
    result = tokenize("can't won't don't")
    assert result == ["can't", "won't", "don't"]


def test_contraction_surrounded_by_punctuation():
    assert tokenize("(it's here)") == ["it's", "here"]


def test_word_with_apostrophe_and_punctuation():
    assert tokenize("she's, he'd, they're.") == ["she's", "he'd", "they're"]


# ---------------------------------------------------------------------------
# Hyphen edge cases (CLARITY_LOG Round 10)
# ---------------------------------------------------------------------------

def test_triple_hyphen_no_empty_tokens():
    assert tokenize("em---dash") == ["em", "dash"]


def test_leading_hyphen():
    assert tokenize("-hello") == ["hello"]


def test_trailing_hyphen():
    assert tokenize("hello-") == ["hello"]


def test_chain_of_hyphenated_words():
    assert tokenize("a-b-c-d") == ["a", "b", "c", "d"]


# ---------------------------------------------------------------------------
# Underscore edge cases (CLARITY_LOG Round 11)
# ---------------------------------------------------------------------------

def test_multiple_underscores():
    assert tokenize("under_score_test") == ["under", "score", "test"]


def test_leading_underscore():
    assert tokenize("_abc") == ["abc"]


def test_trailing_underscore():
    assert tokenize("abc_") == ["abc"]


def test_underscore_and_hyphen_together():
    assert tokenize("foo_bar-baz") == ["foo", "bar", "baz"]


# ---------------------------------------------------------------------------
# Unicode (CLARITY_LOG Round 5)
# ---------------------------------------------------------------------------

def test_accented_characters():
    assert tokenize("résumé naïveté") == ["résumé", "naïveté"]


def test_uppercase_unicode():
    assert tokenize("Ñoño") == ["Ñoño"]


def test_unicode_digits():
    assert tokenize("42abc") == ["42abc"]


# ---------------------------------------------------------------------------
# Whitespace variants
# ---------------------------------------------------------------------------

def test_newlines_split_words():
    assert tokenize("hello\nworld") == ["hello", "world"]


def test_tabs_split_words():
    assert tokenize("tab\there") == ["tab", "here"]


def test_whitespace_only():
    assert tokenize("   \t\n  ") == []


# ---------------------------------------------------------------------------
# Punctuation-only and mixed edge cases
# ---------------------------------------------------------------------------

def test_punctuation_only():
    assert tokenize("!!!???...") == []


def test_comma_separated():
    assert tokenize("a,b,c") == ["a", "b", "c"]


def test_parentheses_stripped():
    assert tokenize("(hello)") == ["hello"]


def test_dots_around_word():
    assert tokenize("...dots...") == ["dots"]


def test_mixed_numbers_and_words():
    assert tokenize("1st 2nd 3rd") == ["1st", "2nd", "3rd"]


def test_single_character_words():
    assert tokenize("a b c") == ["a", "b", "c"]


def test_single_digit():
    assert tokenize("0") == ["0"]


def test_repeated_apostrophe_in_word():
    """Double apostrophe is not intra-word; splits the candidate."""
    result = tokenize("o''clock")
    # 'o' then 'clock' — the double apostrophe is not a valid intra-word apostrophe
    assert result == ["o", "clock"]


def test_sentence_with_all_features():
    """Integration: punctuation, apostrophe, hyphen, unicode, number."""
    text = "It's a well-known café — 42 times over."
    assert tokenize(text) == ["It's", "a", "well", "known", "café", "42", "times", "over"]
