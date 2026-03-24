"""Session JSONL log parser for .harness-logs/*.log files."""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from agent_cost_analyzer.models import SessionError

logger = logging.getLogger(__name__)

# Files that live alongside session logs but are NOT session JSONL.
_EXCLUDED_NAMES = {"cost.log", "phase.log", "metrics.log"}

# Regex to classify error_type from message text.
_ERROR_TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AssertionError", re.I), "assertion_error"),
    (re.compile(r"ImportError|ModuleNotFoundError", re.I), "import_error"),
    (re.compile(r"SyntaxError", re.I), "syntax_error"),
    (re.compile(r"TypeError", re.I), "type_error"),
    (re.compile(r"AttributeError", re.I), "attribute_error"),
    (re.compile(r"NameError", re.I), "name_error"),
    (re.compile(r"ValueError", re.I), "value_error"),
    (re.compile(r"RuntimeError", re.I), "runtime_error"),
    (re.compile(r"FileNotFoundError|IOError|OSError", re.I), "io_error"),
    (re.compile(r"FAILED|fail", re.I), "test_failure"),
    (re.compile(r"warning", re.I), "warning"),
    (re.compile(r"error", re.I), "generic_error"),
]


def _classify_error_type(message: str) -> str:
    for pattern, name in _ERROR_TYPE_PATTERNS:
        if pattern.search(message):
            return name
    return "unknown"


def _extract_message(content_list: list) -> str:
    """Extract text from a tool_result content list."""
    parts: list[str] = []
    for item in content_list:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text", "")
            if text:
                parts.append(text)
    return " ".join(parts)[:500]  # truncate to 500 chars for sanity


def _is_recovery_file(filename: str) -> bool:
    return filename.startswith("recovery_")


def _parse_jsonl_file(log_path: Path, is_recovery: bool) -> list[SessionError]:
    """Parse a single JSONL session log file and extract SessionError entries."""
    errors: list[SessionError] = []
    filename = log_path.name

    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.warning("Cannot read %s: %s", log_path, exc)
        return errors

    for line_num, raw_line in enumerate(lines, start=1):
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON at %s line %d — skipping", filename, line_num)
            continue

        if entry.get("type") != "user":
            continue

        message_obj = entry.get("message", {})
        content_list = message_obj.get("content", [])

        for content_item in content_list:
            if not isinstance(content_item, dict):
                continue
            if content_item.get("type") != "tool_result":
                continue

            # (a) is_error=true tool results
            if content_item.get("is_error") is True:
                nested = content_item.get("content", [])
                message = _extract_message(nested)
                errors.append(
                    SessionError(
                        file=filename,
                        line_num=line_num,
                        error_type=_classify_error_type(message),
                        message=message,
                        is_recovery=is_recovery,
                    )
                )

            # (b) non-empty stderr content
            stderr = content_item.get("stderr", "")
            if stderr:
                errors.append(
                    SessionError(
                        file=filename,
                        line_num=line_num,
                        error_type=_classify_error_type(stderr),
                        message=stderr[:500],
                        is_recovery=is_recovery,
                    )
                )

    return errors


def parse_session_logs(logs_dir: Path) -> list[SessionError]:
    """Parse all session JSONL log files in logs_dir.

    Excludes cost.log, phase.log, and metrics.log.
    Returns empty list if logs_dir does not exist.
    """
    if not logs_dir.exists():
        return []

    errors: list[SessionError] = []
    for log_path in sorted(logs_dir.glob("*.log")):
        if log_path.name in _EXCLUDED_NAMES:
            continue
        is_recovery = _is_recovery_file(log_path.name)
        errors.extend(_parse_jsonl_file(log_path, is_recovery=is_recovery))

    return errors
