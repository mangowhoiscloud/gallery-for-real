"""word_counter - CLI tool for word frequency analysis."""

from word_counter.counter import CountResult, count_words
from word_counter.formatter import format_table
from word_counter.tokenizer import tokenize

__all__ = ["tokenize", "count_words", "CountResult", "format_table"]
