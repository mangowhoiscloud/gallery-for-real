"""Tests for src/prompt_vc/hashing.py."""

import hashlib
from pathlib import Path

from prompt_vc.hashing import hash_file, hash_version


# ---------------------------------------------------------------------------
# hash_file
# ---------------------------------------------------------------------------


def test_hash_file_known_content(tmp_path: Path) -> None:
    """hash_file produces the correct SHA256 for known ASCII content."""
    f = tmp_path / "hello.txt"
    f.write_text("hello world", encoding="utf-8")
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert hash_file(f) == expected


def test_hash_file_empty_file(tmp_path: Path) -> None:
    """hash_file handles an empty file (SHA256 of zero bytes)."""
    f = tmp_path / "empty.txt"
    f.write_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert hash_file(f) == expected


def test_hash_file_unicode_content(tmp_path: Path) -> None:
    """hash_file hashes the raw bytes, so unicode content round-trips correctly."""
    content = "Привет мир 🌍"
    f = tmp_path / "unicode.txt"
    raw = content.encode("utf-8")
    f.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    assert hash_file(f) == expected


def test_hash_file_consistent(tmp_path: Path) -> None:
    """hash_file returns the same value on repeated calls."""
    f = tmp_path / "stable.txt"
    f.write_text("consistent", encoding="utf-8")
    assert hash_file(f) == hash_file(f)


def test_hash_file_different_content_different_hash(tmp_path: Path) -> None:
    """Different file content → different hash."""
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("foo", encoding="utf-8")
    b.write_text("bar", encoding="utf-8")
    assert hash_file(a) != hash_file(b)


def test_hash_file_returns_hex_string(tmp_path: Path) -> None:
    """hash_file returns a 64-character lowercase hex string."""
    f = tmp_path / "check.txt"
    f.write_text("x", encoding="utf-8")
    result = hash_file(f)
    assert len(result) == 64
    assert result == result.lower()
    assert all(c in "0123456789abcdef" for c in result)


# ---------------------------------------------------------------------------
# hash_version
# ---------------------------------------------------------------------------


def test_hash_version_deterministic() -> None:
    """Same files dict always produces the same hash."""
    files = {"PROMPT_a.md": "aaa", "PROMPT_b.md": "bbb"}
    assert hash_version(files) == hash_version(files)


def test_hash_version_order_independent() -> None:
    """Insertion order does not affect the result."""
    files_ab = {"PROMPT_a.md": "aaa", "PROMPT_b.md": "bbb"}
    files_ba = {"PROMPT_b.md": "bbb", "PROMPT_a.md": "aaa"}
    assert hash_version(files_ab) == hash_version(files_ba)


def test_hash_version_different_files_different_hash() -> None:
    """Different file sets produce different hashes."""
    files1 = {"PROMPT_a.md": "aaa"}
    files2 = {"PROMPT_a.md": "zzz"}
    assert hash_version(files1) != hash_version(files2)


def test_hash_version_empty_dict() -> None:
    """hash_version of an empty dict is the SHA256 of zero bytes."""
    expected = hashlib.sha256(b"").hexdigest()
    assert hash_version({}) == expected


def test_hash_version_single_file() -> None:
    """hash_version with one file matches manually computed digest."""
    files = {"PROMPT_x.md": "deadbeef"}
    h = hashlib.sha256()
    h.update(b"PROMPT_x.md:deadbeef\n")
    assert hash_version(files) == h.hexdigest()


def test_hash_version_multiple_files_known_value() -> None:
    """hash_version produces the correct digest for a two-file set."""
    files = {"b.md": "222", "a.md": "111"}
    h = hashlib.sha256()
    # sorted order: a.md, b.md
    h.update(b"a.md:111\n")
    h.update(b"b.md:222\n")
    assert hash_version(files) == h.hexdigest()


def test_hash_version_returns_hex_string() -> None:
    """hash_version returns a 64-character lowercase hex string."""
    result = hash_version({"f.md": "abc"})
    assert len(result) == 64
    assert result == result.lower()
    assert all(c in "0123456789abcdef" for c in result)
