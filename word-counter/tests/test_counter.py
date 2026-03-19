"""Tests for counter module."""
from word_counter.counter import CountResult, count_words


# ---------------------------------------------------------------------------
# Basic counting
# ---------------------------------------------------------------------------


def test_basic_two_words():
    result = count_words(["the", "a", "the"])
    assert result.frequencies == [("the", 2), ("a", 1)]
    assert result.total == 3
    assert result.unique == 2


def test_single_word():
    result = count_words(["hello"])
    assert result.frequencies == [("hello", 1)]
    assert result.total == 1
    assert result.unique == 1


def test_all_same_word():
    result = count_words(["word", "word", "word"])
    assert result.frequencies == [("word", 3)]
    assert result.total == 3
    assert result.unique == 1


def test_all_distinct():
    result = count_words(["a", "b", "c"])
    assert result.total == 3
    assert result.unique == 3


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_empty_input():
    result = count_words([])
    assert result.frequencies == []
    assert result.total == 0
    assert result.unique == 0


# ---------------------------------------------------------------------------
# Sorting order
# ---------------------------------------------------------------------------


def test_sort_by_count_descending():
    result = count_words(["b", "a", "a", "a", "b", "c"])
    # a:3, b:2, c:1
    assert result.frequencies[0] == ("a", 3)
    assert result.frequencies[1] == ("b", 2)
    assert result.frequencies[2] == ("c", 1)


def test_tiebreak_alphabetical_ascending():
    # "the" and "and" both appear twice — alphabetical order: "and" < "the"
    result = count_words(["the", "and", "the", "and"])
    assert result.frequencies == [("and", 2), ("the", 2)]


def test_tiebreak_three_words_same_count():
    result = count_words(["zebra", "apple", "mango"])
    assert result.frequencies == [("apple", 1), ("mango", 1), ("zebra", 1)]


def test_tiebreak_mixed_counts():
    words = ["c", "b", "a", "b", "a", "b"]
    # b:3, a:2, c:1
    result = count_words(words)
    assert result.frequencies == [("b", 3), ("a", 2), ("c", 1)]


def test_tiebreak_unicode_alphabetical():
    # All count=1; ordering by Unicode code points for letters
    result = count_words(["ñ", "a", "z"])
    # Python sorts by code-point: 'a' < 'z' < 'ñ'
    words_in_order = [w for w, _ in result.frequencies]
    assert words_in_order == sorted(["ñ", "a", "z"])


# ---------------------------------------------------------------------------
# ignore_case
# ---------------------------------------------------------------------------


def test_ignore_case_merges_variants():
    result = count_words(["Hello", "hello"], ignore_case=True)
    assert result.frequencies == [("hello", 2)]
    assert result.total == 2
    assert result.unique == 1


def test_ignore_case_returns_lowercase_keys():
    result = count_words(["THE", "The", "the"], ignore_case=True)
    assert result.frequencies == [("the", 3)]


def test_ignore_case_false_preserves_case():
    result = count_words(["Hello", "hello"], ignore_case=False)
    # two distinct words, each count=1
    words = {w for w, _ in result.frequencies}
    assert words == {"Hello", "hello"}
    assert result.total == 2
    assert result.unique == 2


def test_ignore_case_mixed_case_tiebreak():
    # After lowercasing: "apple":2, "banana":1 → sorted by (-count, alpha)
    result = count_words(["Apple", "apple", "Banana"], ignore_case=True)
    assert result.frequencies == [("apple", 2), ("banana", 1)]


def test_ignore_case_empty_input():
    result = count_words([], ignore_case=True)
    assert result.frequencies == []
    assert result.total == 0
    assert result.unique == 0


# ---------------------------------------------------------------------------
# Total and unique accuracy
# ---------------------------------------------------------------------------


def test_total_equals_sum_of_counts():
    words = ["a", "b", "a", "c", "b", "a"]
    result = count_words(words)
    assert result.total == len(words)
    assert result.total == sum(c for _, c in result.frequencies)


def test_unique_equals_distinct_word_count():
    words = ["x", "y", "z", "x", "y"]
    result = count_words(words)
    assert result.unique == 3


def test_unique_single_distinct():
    result = count_words(["same"] * 100)
    assert result.unique == 1
    assert result.total == 100


# ---------------------------------------------------------------------------
# CountResult dataclass
# ---------------------------------------------------------------------------


def test_count_result_is_dataclass():
    r = CountResult(frequencies=[("hello", 1)], total=1, unique=1)
    assert r.frequencies == [("hello", 1)]
    assert r.total == 1
    assert r.unique == 1


def test_count_result_equality():
    r1 = CountResult(frequencies=[("a", 2)], total=2, unique=1)
    r2 = CountResult(frequencies=[("a", 2)], total=2, unique=1)
    assert r1 == r2
