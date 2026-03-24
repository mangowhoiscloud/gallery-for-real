"""Tests for session JSONL log parser (Item 6)."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from agent_cost_analyzer.models import SessionError
from agent_cost_analyzer.parser.build_log import parse_session_logs


# ── helpers ─────────────────────────────────────────────────────────────────

def _write_jsonl(path: Path, lines: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(d) for d in lines) + "\n")


# ── fixture dir helpers ──────────────────────────────────────────────────────

@pytest.fixture
def logs_dir(tmp_path: Path) -> Path:
    """Return a temp directory acting as .harness-logs/."""
    return tmp_path / ".harness-logs"


# ── missing directory ────────────────────────────────────────────────────────

def test_missing_directory_returns_empty_list(tmp_path: Path) -> None:
    result = parse_session_logs(tmp_path / "nonexistent")
    assert result == []


def test_empty_directory_returns_empty_list(logs_dir: Path) -> None:
    logs_dir.mkdir()
    result = parse_session_logs(logs_dir)
    assert result == []


# ── exclusion of special files ───────────────────────────────────────────────

def test_excludes_cost_log(logs_dir: Path) -> None:
    """cost.log must not be parsed as session JSONL."""
    logs_dir.mkdir()
    # cost.log has non-JSONL content; if parsed it would produce warnings/errors
    (logs_dir / "cost.log").write_text(
        "2026-03-19T10:00:00+09:00 phase=build iter=1 model=sonnet "
        "in=100 out=200 cost=$0.10 cumulative=$0.10 item=1\n"
    )
    result = parse_session_logs(logs_dir)
    assert result == []


def test_excludes_phase_log(logs_dir: Path) -> None:
    logs_dir.mkdir()
    (logs_dir / "phase.log").write_text(
        "2026-03-19T10:00:00+09:00 event=START phase=socratic\n"
    )
    result = parse_session_logs(logs_dir)
    assert result == []


def test_excludes_metrics_log(logs_dir: Path) -> None:
    logs_dir.mkdir()
    (logs_dir / "metrics.log").write_text(
        "2026-03-19T10:00:00+09:00 metric=error_count context=build value=1 detail=2\n"
    )
    result = parse_session_logs(logs_dir)
    assert result == []


# ── is_error extraction ──────────────────────────────────────────────────────

def test_extracts_is_error_tool_result(logs_dir: Path) -> None:
    """type=user with is_error=true in tool result produces SessionError."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": True,
                        "content": [{"type": "text", "text": "AssertionError: expected 42 got None"}],
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 1
    err = result[0]
    assert isinstance(err, SessionError)
    assert "AssertionError" in err.message
    assert err.is_recovery is False
    assert err.file == "build_iter0_20260319.log"
    assert err.line_num == 1


def test_no_errors_for_successful_tool_result(logs_dir: Path) -> None:
    """is_error=false tool results do not produce SessionError."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": False,
                        "content": [{"type": "text", "text": "ok"}],
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert result == []


# ── stderr extraction ────────────────────────────────────────────────────────

def test_extracts_stderr_from_tool_result(logs_dir: Path) -> None:
    """Bash tool results with non-empty stderr produce SessionError."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01def",
                        "is_error": False,
                        "content": [{"type": "text", "text": ""}],
                        "stderr": "warning: deprecated function used in cost_log.py:42",
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:04+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter1_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 1
    err = result[0]
    assert "warning" in err.message.lower() or "deprecated" in err.message.lower()
    assert err.is_recovery is False


def test_empty_stderr_not_extracted(logs_dir: Path) -> None:
    """Empty stderr string does not produce SessionError."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01def",
                        "is_error": False,
                        "content": [{"type": "text", "text": "success"}],
                        "stderr": "",
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:04+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert result == []


# ── recovery file tagging ────────────────────────────────────────────────────

def test_recovery_file_tagged_is_recovery_true(logs_dir: Path) -> None:
    """Files matching recovery_*.log produce errors with is_recovery=True."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": True,
                        "content": [{"type": "text", "text": "FAILED: recovery attempt also failed"}],
                    }
                ],
            },
            "timestamp": "2026-03-19T11:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "recovery_iter5_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 1
    assert result[0].is_recovery is True


def test_non_recovery_file_tagged_is_recovery_false(logs_dir: Path) -> None:
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": True,
                        "content": [{"type": "text", "text": "test FAILED"}],
                    }
                ],
            },
            "timestamp": "2026-03-19T11:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter2_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 1
    assert result[0].is_recovery is False


# ── invalid JSON handling ─────────────────────────────────────────────────────

def test_invalid_json_lines_skipped_with_warning(
    logs_dir: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Invalid JSON lines are skipped (no exception) and a warning is logged."""
    logs_dir.mkdir()
    content = (
        '{"type":"system","subtype":"hook_started","timestamp":"2026-03-19T10:00:00+09:00"}\n'
        "this is not json at all\n"
        '{"type":"user","message":{"role":"user","content":[{"type":"tool_result",'
        '"tool_use_id":"toolu_01abc","is_error":true,"content":[{"type":"text",'
        '"text":"error"}]}]},"timestamp":"2026-03-19T10:00:02+09:00"}\n'
    )
    (logs_dir / "build_iter0_20260319.log").write_text(content)
    with caplog.at_level(logging.WARNING):
        result = parse_session_logs(logs_dir)
    # Should still find the valid error entry
    assert len(result) == 1
    assert any("invalid" in r.message.lower() or "json" in r.message.lower()
               for r in caplog.records)


# ── multiple errors per file ─────────────────────────────────────────────────

def test_multiple_errors_extracted_from_single_file(logs_dir: Path) -> None:
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01",
                        "is_error": True,
                        "content": [{"type": "text", "text": "Error 1"}],
                    },
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_02",
                        "is_error": True,
                        "content": [{"type": "text", "text": "Error 2"}],
                    },
                ],
            },
            "timestamp": "2026-03-19T10:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 2


# ── multiple files ───────────────────────────────────────────────────────────

def test_multiple_log_files_all_parsed(logs_dir: Path) -> None:
    logs_dir.mkdir()
    for i, fname in enumerate(
        ["build_iter0_20260319.log", "build_iter1_20260319.log"]
    ):
        entries = [
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": f"toolu_0{i}",
                            "is_error": True,
                            "content": [{"type": "text", "text": f"Error in iter {i}"}],
                        }
                    ],
                },
                "timestamp": "2026-03-19T10:00:00+09:00",
            }
        ]
        _write_jsonl(logs_dir / fname, entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 2


# ── non-user type entries ignored ────────────────────────────────────────────

def test_assistant_and_system_entries_not_extracted(logs_dir: Path) -> None:
    """Only type=user entries are inspected for errors."""
    logs_dir.mkdir()
    entries = [
        {"type": "system", "subtype": "hook_started", "timestamp": "2026-03-19T10:00:00+09:00"},
        {
            "type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": "error: something"}]},
            "timestamp": "2026-03-19T10:00:01+09:00",
        },
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert result == []


# ── fixture integration ──────────────────────────────────────────────────────

def test_fixture_jsonl_produces_errors(tmp_path: Path, session_log_path: Path) -> None:
    """Parsing the session_build.jsonl fixture extracts the expected errors."""
    # Create a logs dir with the fixture content renamed to a .log file
    logs_dir = tmp_path / ".harness-logs"
    logs_dir.mkdir()
    content = session_log_path.read_text()
    (logs_dir / "build_iter0_20260319.log").write_text(content)

    result = parse_session_logs(logs_dir)
    # fixture has 1 is_error=true entry and 1 stderr entry
    assert len(result) >= 1
    messages = [e.message for e in result]
    assert any("AssertionError" in m or "test_cost_parser" in m for m in messages)


# ── error_type classification ────────────────────────────────────────────────

def test_error_type_field_is_non_empty_string(logs_dir: Path) -> None:
    """error_type is always a non-empty string."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": True,
                        "content": [{"type": "text", "text": "SyntaxError: unexpected token"}],
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert len(result) == 1
    assert result[0].error_type != ""


# ── message content truncation / extraction ──────────────────────────────────

def test_message_extracted_from_nested_content(logs_dir: Path) -> None:
    """Message text is extracted from nested content[].text field."""
    logs_dir.mkdir()
    entries = [
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_01abc",
                        "is_error": True,
                        "content": [
                            {"type": "text", "text": "ImportError: cannot import name 'Foo'"}
                        ],
                    }
                ],
            },
            "timestamp": "2026-03-19T10:00:00+09:00",
        }
    ]
    _write_jsonl(logs_dir / "build_iter0_20260319.log", entries)
    result = parse_session_logs(logs_dir)
    assert "ImportError" in result[0].message
