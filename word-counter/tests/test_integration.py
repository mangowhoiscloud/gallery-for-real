"""Integration tests: full pipeline from real fixture files to formatted output.

Covers all 11 clarity resolutions from CLARITY_LOG.md using actual text files
in tests/fixtures/. Each test class documents which resolution(s) it exercises.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import pytest

from word_counter.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Full pipeline — exact output verification
# ---------------------------------------------------------------------------


class TestFullPipeline:
    """End-to-end test: file → tokenize → count → format → exact output.

    simple.txt: "the quick brown fox / the lazy dog / the fox"
    Expected counts: the(3), fox(2), brown(1), dog(1), lazy(1), quick(1)
    Total: 9 words, 6 unique
    """

    def test_exact_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Full output matches expected table format precisely."""
        main([str(FIXTURES / "simple.txt")])
        out = capsys.readouterr().out
        expected = (
            "# | Word  | Count |     %\n"
            "--+-------+-------+------\n"
            "1 | the   |     3 | 33.3%\n"
            "2 | fox   |     2 | 22.2%\n"
            "3 | brown |     1 | 11.1%\n"
            "4 | dog   |     1 | 11.1%\n"
            "5 | lazy  |     1 | 11.1%\n"
            "6 | quick |     1 | 11.1%\n"
            "Total: 9 words, 6 unique words\n"
        )
        assert out == expected

    def test_no_stderr_for_valid_file(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Valid file produces no stderr output."""
        main([str(FIXTURES / "simple.txt")])
        assert capsys.readouterr().err == ""

    def test_summary_line_totals(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Summary line reports correct total and unique counts."""
        main([str(FIXTURES / "simple.txt")])
        assert "Total: 9 words, 6 unique words" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Clarity #3 — Multiple files aggregate into a single report
# ---------------------------------------------------------------------------


class TestMultipleFilesAggregation:
    """simple.txt (9 words, 6 unique) + second.txt (hello(2), world(1), 3 words, 2 unique).
    Combined: 12 words, 8 unique (hello and world are new).
    """

    def test_words_from_both_files_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Words from both files appear in the combined output."""
        main([str(FIXTURES / "simple.txt"), str(FIXTURES / "second.txt")])
        out = capsys.readouterr().out
        assert "the" in out
        assert "hello" in out

    def test_combined_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Total word count sums both files (9 + 3 = 12)."""
        main([str(FIXTURES / "simple.txt"), str(FIXTURES / "second.txt")])
        assert "Total: 12 words" in capsys.readouterr().out

    def test_combined_unique(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Unique count spans both files (6 + 2 new = 8 unique)."""
        main([str(FIXTURES / "simple.txt"), str(FIXTURES / "second.txt")])
        assert "8 unique words" in capsys.readouterr().out

    def test_single_table_produced(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Only one summary line is produced (not one per file)."""
        main([str(FIXTURES / "simple.txt"), str(FIXTURES / "second.txt")])
        assert capsys.readouterr().out.count("Total:") == 1


# ---------------------------------------------------------------------------
# Clarity #4 — --ignore-case displays words in lowercase
# ---------------------------------------------------------------------------


class TestIgnoreCase:
    """case_words.txt: "Hello hello HELLO world World"
    With --ignore-case: hello(3), world(2), total=5, unique=2.
    Without:           all 5 variants distinct, total=5, unique=5.
    """

    def test_merges_variants_into_lowercase(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Hello/hello/HELLO merged; display form is lowercase."""
        main(["--ignore-case", str(FIXTURES / "case_words.txt")])
        out = capsys.readouterr().out
        assert "hello" in out
        assert "Hello" not in out
        assert "HELLO" not in out

    def test_ignore_case_count_for_hello(self, capsys: pytest.CaptureFixture[str]) -> None:
        """With --ignore-case, hello appears with count 3."""
        main(["--ignore-case", str(FIXTURES / "case_words.txt")])
        out = capsys.readouterr().out
        hello_rows = [ln for ln in out.splitlines() if "hello" in ln and "|" in ln]
        assert len(hello_rows) == 1
        assert "3" in hello_rows[0]

    def test_ignore_case_unique_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        """With --ignore-case, only 2 unique words (hello, world)."""
        main(["--ignore-case", str(FIXTURES / "case_words.txt")])
        assert "2 unique words" in capsys.readouterr().out

    def test_without_ignore_case_all_distinct(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Without --ignore-case, all 5 case variants are distinct words."""
        main([str(FIXTURES / "case_words.txt")])
        assert "Total: 5 words, 5 unique words" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Clarity #8 — --top N requires a positive integer
# ---------------------------------------------------------------------------


class TestTopNFlag:
    def test_top_3_limits_to_three_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--top 3 produces exactly 3 data rows (header+sep+3rows+summary = 6 lines)."""
        main(["--top", "3", str(FIXTURES / "simple.txt")])
        lines = capsys.readouterr().out.splitlines()
        assert len(lines) == 6

    def test_top_2_shows_highest_frequency_words(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--top 2 shows 'the' and 'fox' but not 'brown'."""
        main(["--top", "2", str(FIXTURES / "simple.txt")])
        out = capsys.readouterr().out
        assert "the" in out
        assert "fox" in out
        assert "brown" not in out

    def test_top_zero_exits_with_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--top 0 is rejected by argparse (exit code 2)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--top", "0", str(FIXTURES / "simple.txt")])
        assert exc_info.value.code == 2

    def test_top_negative_exits_with_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--top -1 is rejected by argparse (exit code 2)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--top", "-1", str(FIXTURES / "simple.txt")])
        assert exc_info.value.code == 2

    def test_top_non_integer_exits_with_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--top abc is rejected by argparse (exit code 2)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--top", "abc", str(FIXTURES / "simple.txt")])
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Clarity #7 — Error handling: missing files, empty files, stdin
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_missing_file_exits_1(self, tmp_path: Path) -> None:
        """Single missing file → exit code 1."""
        with pytest.raises(SystemExit) as exc_info:
            main([str(tmp_path / "nonexistent.txt")])
        assert exc_info.value.code == 1

    def test_missing_file_error_on_stderr(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Error for missing file goes to stderr; stdout is empty."""
        with pytest.raises(SystemExit):
            main([str(tmp_path / "nonexistent.txt")])
        captured = capsys.readouterr()
        assert "nonexistent.txt" in captured.err
        assert captured.out == ""

    def test_missing_file_continues_with_valid(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Missing file error on stderr; valid file is still processed."""
        main([str(tmp_path / "nonexistent.txt"), str(FIXTURES / "simple.txt")])
        captured = capsys.readouterr()
        assert "nonexistent.txt" in captured.err
        assert "the" in captured.out
        assert "Total: 9 words" in captured.out

    def test_empty_file_is_valid_input(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty file is valid input (zero words), not an error (clarity #7)."""
        main([str(FIXTURES / "empty.txt")])
        assert "Total: 0 words, 0 unique words" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Clarity #7 — Stdin pipe (no file args given)
# ---------------------------------------------------------------------------


class TestStdinPipeline:
    def test_piped_stdin_produces_output(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Piped stdin (isatty=False) is read and counted correctly."""
        monkeypatch.setattr(sys, "stdin", io.StringIO("hello world hello\n"))
        main([])
        out = capsys.readouterr().out
        assert "hello" in out
        assert "world" in out
        assert "Total: 3 words" in out

    def test_piped_stdin_word_counts(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Stdin: 'hello world hello' → hello appears with count 2."""
        monkeypatch.setattr(sys, "stdin", io.StringIO("hello world hello\n"))
        main([])
        out = capsys.readouterr().out
        hello_rows = [ln for ln in out.splitlines() if "hello" in ln and "|" in ln]
        assert len(hello_rows) == 1
        assert "2" in hello_rows[0]


# ---------------------------------------------------------------------------
# Clarity #1 — Apostrophe boundaries
# ---------------------------------------------------------------------------


class TestApostropheBoundaries:
    """apostrophes.txt: "don't won't 'twas dogs'"
    Expected words: don't(1), won't(1), twas(1), dogs(1).
    """

    def test_leading_apostrophe_stripped(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'twas → twas (leading apostrophe stripped, not part of the word)."""
        main([str(FIXTURES / "apostrophes.txt")])
        out = capsys.readouterr().out
        assert "twas" in out
        assert "'twas" not in out

    def test_trailing_apostrophe_stripped(self, capsys: pytest.CaptureFixture[str]) -> None:
        """dogs' → dogs (trailing apostrophe stripped)."""
        main([str(FIXTURES / "apostrophes.txt")])
        assert "dogs" in capsys.readouterr().out

    def test_internal_apostrophe_kept(self, capsys: pytest.CaptureFixture[str]) -> None:
        """don't is one word with internal apostrophe kept."""
        main([str(FIXTURES / "apostrophes.txt")])
        assert "don't" in capsys.readouterr().out

    def test_apostrophes_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        """apostrophes.txt has 4 words, all unique."""
        main([str(FIXTURES / "apostrophes.txt")])
        assert "Total: 4 words, 4 unique words" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Clarity #2 — Tie-breaking: alphabetical ascending
# ---------------------------------------------------------------------------


class TestTieBreaking:
    """In simple.txt, words at rank 3-6 all have count=1.
    They must appear in alphabetical order: brown, dog, lazy, quick.
    """

    def test_tied_words_alphabetical_order(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Words with equal frequency are sorted alphabetically ascending."""
        main([str(FIXTURES / "simple.txt")])
        lines = capsys.readouterr().out.splitlines()
        # lines[0]=header, lines[1]=sep, lines[2]=the, lines[3]=fox, lines[4..7]=tied words
        tied_words = [ln.split("|")[1].strip() for ln in lines[4:8]]
        assert tied_words == ["brown", "dog", "lazy", "quick"]


# ---------------------------------------------------------------------------
# Clarity #6, #9 — Table format: one-decimal percentages, + separators
# ---------------------------------------------------------------------------


class TestTableFormat:
    def test_separator_uses_plus_signs(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Separator line uses + as column delimiter (clarity #9)."""
        main([str(FIXTURES / "simple.txt")])
        sep_line = capsys.readouterr().out.splitlines()[1]
        assert "+" in sep_line
        assert all(c in "-+" for c in sep_line)

    def test_header_column_names(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Header contains #, Word, Count, % (clarity #9)."""
        main([str(FIXTURES / "simple.txt")])
        header = capsys.readouterr().out.splitlines()[0]
        assert "#" in header
        assert "Word" in header
        assert "Count" in header
        assert "%" in header

    def test_percentages_one_decimal_place(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Percentages are formatted to exactly one decimal place (clarity #6)."""
        main([str(FIXTURES / "simple.txt")])
        out = capsys.readouterr().out
        pct_values = re.findall(r"\d+\.\d%", out)
        assert len(pct_values) > 0
        for pct in pct_values:
            assert re.match(r"^\d+\.\d%$", pct), f"unexpected format: {pct!r}"


# ---------------------------------------------------------------------------
# Clarity #10 — Multiple hyphens as separators
# Clarity #11 — Underscores as word separators
# ---------------------------------------------------------------------------


class TestHyphensAndUnderscores:
    """hyphens_underscores.txt: "well-known word--break my_variable"
    Expected words: break(1), known(1), my(1), variable(1), well(1), word(1).
    """

    def test_single_hyphen_splits(self, capsys: pytest.CaptureFixture[str]) -> None:
        """well-known → well and known as separate words (clarity #10)."""
        main([str(FIXTURES / "hyphens_underscores.txt")])
        out = capsys.readouterr().out
        assert "well" in out
        assert "known" in out

    def test_double_hyphen_splits(self, capsys: pytest.CaptureFixture[str]) -> None:
        """word--break → word and break as separate words (clarity #10)."""
        main([str(FIXTURES / "hyphens_underscores.txt")])
        out = capsys.readouterr().out
        assert "word" in out
        assert "break" in out

    def test_underscore_splits(self, capsys: pytest.CaptureFixture[str]) -> None:
        """my_variable → my and variable as separate words (clarity #11)."""
        main([str(FIXTURES / "hyphens_underscores.txt")])
        out = capsys.readouterr().out
        assert "my" in out
        assert "variable" in out

    def test_hyphens_underscores_total(self, capsys: pytest.CaptureFixture[str]) -> None:
        """All 6 component words are counted: 6 total, 6 unique."""
        main([str(FIXTURES / "hyphens_underscores.txt")])
        assert "Total: 6 words, 6 unique words" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Clarity #5 — Unicode letters are valid word characters
# ---------------------------------------------------------------------------


class TestUnicodeContent:
    """unicode_words.txt: "café naïve résumé"
    All three are single Unicode words; total=3, unique=3.
    """

    def test_unicode_words_appear_in_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """café, naïve, résumé each counted as a single word (clarity #5)."""
        main([str(FIXTURES / "unicode_words.txt")])
        out = capsys.readouterr().out
        assert "café" in out
        assert "naïve" in out
        assert "résumé" in out

    def test_unicode_total_count(self, capsys: pytest.CaptureFixture[str]) -> None:
        """3 Unicode words, all unique."""
        main([str(FIXTURES / "unicode_words.txt")])
        assert "Total: 3 words, 3 unique words" in capsys.readouterr().out
