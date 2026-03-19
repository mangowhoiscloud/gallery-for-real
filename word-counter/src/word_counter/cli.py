"""CLI: wc-freq entry point.

Orchestrates tokenizer → counter → formatter pipeline.
Reads one or more files, or stdin when no files are given.
"""
from __future__ import annotations

import argparse
import sys

from word_counter.counter import count_words
from word_counter.formatter import format_table
from word_counter.tokenizer import tokenize


def _positive_int(value: str) -> int:
    """Argparse type that accepts only positive integers (>0)."""
    try:
        n = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid integer")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {n}")
    return n


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wc-freq",
        description="Analyze word frequency in text files.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="FILE",
        help="Text files to analyze. Reads from stdin if none given.",
    )
    parser.add_argument(
        "--top",
        type=_positive_int,
        default=10,
        metavar="N",
        help="Show top N most frequent words (default: 10).",
    )
    parser.add_argument(
        "--ignore-case",
        action="store_true",
        help="Treat words case-insensitively.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    all_words: list[str] = []
    had_valid_input = False

    for path in args.files:
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            all_words.extend(tokenize(text))
            had_valid_input = True
        except OSError as exc:
            print(f"wc-freq: {path}: {exc.strerror}", file=sys.stderr)

    # Read stdin when no file arguments given and stdin is not a TTY
    if not args.files:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
            all_words.extend(tokenize(text))
            had_valid_input = True

    if not had_valid_input:
        sys.exit(1)

    result = count_words(all_words, ignore_case=args.ignore_case)
    print(format_table(result.frequencies, result.total, result.unique, top_n=args.top))
