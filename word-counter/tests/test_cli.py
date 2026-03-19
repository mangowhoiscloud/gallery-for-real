"""Tests for the CLI module (wc-freq entry point)."""
from __future__ import annotations

import argparse
import io
import sys

import pytest

from word_counter.cli import _build_parser, _positive_int, main


# ---------------------------------------------------------------------------
# _positive_int type helper
# ---------------------------------------------------------------------------


def test_positive_int_valid():
    assert _positive_int("1") == 1
    assert _positive_int("10") == 10
    assert _positive_int("100") == 100


def test_positive_int_zero_raises():
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_int("0")


def test_positive_int_negative_raises():
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_int("-1")
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_int("-99")


def test_positive_int_non_integer_raises():
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_int("abc")
    with pytest.raises(argparse.ArgumentTypeError):
        _positive_int("1.5")


# ---------------------------------------------------------------------------
# Argument parser defaults
# ---------------------------------------------------------------------------


def test_parser_default_top():
    parser = _build_parser()
    args = parser.parse_args([])
    assert args.top == 10


def test_parser_ignore_case_default_false():
    parser = _build_parser()
    args = parser.parse_args([])
    assert args.ignore_case is False


def test_parser_ignore_case_flag():
    parser = _build_parser()
    args = parser.parse_args(["--ignore-case"])
    assert args.ignore_case is True


def test_parser_top_flag():
    parser = _build_parser()
    args = parser.parse_args(["--top", "5"])
    assert args.top == 5


def test_parser_files_positional():
    parser = _build_parser()
    args = parser.parse_args(["a.txt", "b.txt"])
    assert args.files == ["a.txt", "b.txt"]


# ---------------------------------------------------------------------------
# Invalid --top values cause SystemExit (argparse error)
# ---------------------------------------------------------------------------


def test_top_zero_exits(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main(["--top", "0"])
    assert exc.value.code != 0


def test_top_negative_exits(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main(["--top", "-1"])
    assert exc.value.code != 0


def test_top_non_integer_exits(capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main(["--top", "abc"])
    assert exc.value.code != 0


# ---------------------------------------------------------------------------
# Single file
# ---------------------------------------------------------------------------


def test_single_file(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "text.txt"
    f.write_text("hello world hello")
    main([str(f)])
    out, err = capsys.readouterr()
    assert "hello" in out
    assert "world" in out
    assert "Total: 3 words, 2 unique words" in out
    assert err == ""


def test_single_file_top_flag(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "text.txt"
    f.write_text("a b c d e f g h i j k")
    main(["--top", "3", str(f)])
    out, _ = capsys.readouterr()
    lines = [ln for ln in out.splitlines() if ln and not ln.startswith(("#", "-", "T"))]
    assert len(lines) == 3


def test_single_file_ignore_case(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "text.txt"
    f.write_text("Hello HELLO hello")
    main(["--ignore-case", str(f)])
    out, _ = capsys.readouterr()
    assert "hello" in out
    assert "Total: 3 words, 1 unique words" in out


def test_empty_file_is_valid_input(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "empty.txt"
    f.write_text("")
    # Should NOT exit 1; should succeed and print 0 totals
    main([str(f)])
    out, err = capsys.readouterr()
    assert "Total: 0 words, 0 unique words" in out
    assert err == ""


# ---------------------------------------------------------------------------
# Multiple files — aggregation
# ---------------------------------------------------------------------------


def test_multiple_files_aggregated(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("hello world")
    f2.write_text("hello again")
    main([str(f1), str(f2)])
    out, _ = capsys.readouterr()
    assert "Total: 4 words, 3 unique words" in out
    # "hello" appears twice, should be at rank 1
    lines = out.splitlines()
    data_lines = [ln for ln in lines if "|" in ln and "#" not in ln]
    assert "hello" in data_lines[0]


# ---------------------------------------------------------------------------
# Stdin handling
# ---------------------------------------------------------------------------


def test_stdin_read_when_no_files(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    fake_stdin = io.StringIO("hello world hello")
    monkeypatch.setattr(sys, "stdin", fake_stdin)
    main([])
    out, err = capsys.readouterr()
    assert "hello" in out
    assert "Total: 3 words, 2 unique words" in out
    assert err == ""


def test_empty_piped_stdin_is_valid(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    fake_stdin = io.StringIO("")
    monkeypatch.setattr(sys, "stdin", fake_stdin)
    main([])
    out, err = capsys.readouterr()
    assert "Total: 0 words, 0 unique words" in out
    assert err == ""


def test_tty_stdin_no_files_exits_1(monkeypatch: pytest.MonkeyPatch):
    # Simulate a TTY by making isatty() return True
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr(sys, "stdin", FakeTTY(""))
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Error handling — missing files
# ---------------------------------------------------------------------------


def test_missing_file_prints_stderr(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "nonexistent.txt")])
    _, err = capsys.readouterr()
    assert "nonexistent.txt" in err
    assert exc.value.code == 1


def test_missing_file_with_valid_continues(
    tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
):
    valid = tmp_path / "real.txt"
    valid.write_text("hello world")
    missing = str(tmp_path / "nope.txt")
    # Should NOT raise SystemExit — there is valid input
    main([missing, str(valid)])
    out, err = capsys.readouterr()
    assert "nope.txt" in err
    assert "Total: 2 words, 2 unique words" in out


def test_all_files_missing_exits_1(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path / "a.txt"), str(tmp_path / "b.txt")])
    _, err = capsys.readouterr()
    assert "a.txt" in err
    assert "b.txt" in err
    assert exc.value.code == 1


def test_each_missing_file_has_own_error(
    tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "x.txt"), str(tmp_path / "y.txt")])
    _, err = capsys.readouterr()
    assert err.count("wc-freq:") == 2


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------


def test_output_has_header(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "t.txt"
    f.write_text("a b c")
    main([str(f)])
    out, _ = capsys.readouterr()
    assert "Word" in out
    assert "Count" in out
    assert "#" in out


def test_output_has_summary_line(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "t.txt"
    f.write_text("hello world")
    main([str(f)])
    out, _ = capsys.readouterr()
    assert "Total: 2 words, 2 unique words" in out


def test_unicode_content(tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]):
    f = tmp_path / "unicode.txt"
    f.write_text("café naïve café")
    main([str(f)])
    out, err = capsys.readouterr()
    assert "café" in out
    assert "naïve" in out
    assert "Total: 3 words, 2 unique words" in out
    assert err == ""


def test_top_default_shows_at_most_10(
    tmp_path: pytest.TempPathFactory, capsys: pytest.CaptureFixture[str]
):
    # 15 distinct words
    words = " ".join(f"word{i}" for i in range(15))
    f = tmp_path / "many.txt"
    f.write_text(words)
    main([str(f)])
    out, _ = capsys.readouterr()
    # data lines have | but not the separator line
    data_lines = [ln for ln in out.splitlines() if "|" in ln and "#" not in ln]
    assert len(data_lines) == 10
