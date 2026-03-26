"""Tests for clarity_parser.parse_clarity_log."""

from pathlib import Path

from agent_harvest.clarity_parser import parse_clarity_log
from agent_harvest.models import ClarityEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "CLARITY_LOG.md"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Non-existent / empty file
# ---------------------------------------------------------------------------


def test_nonexistent_file_returns_empty(tmp_path: Path) -> None:
    result = parse_clarity_log(tmp_path / "no_such_file.md")
    assert result == []


def test_empty_file_returns_empty(tmp_path: Path) -> None:
    p = _write(tmp_path, "")
    assert parse_clarity_log(p) == []


def test_whitespace_only_file_returns_empty(tmp_path: Path) -> None:
    p = _write(tmp_path, "   \n\n   ")
    assert parse_clarity_log(p) == []


# ---------------------------------------------------------------------------
# Realistic fixture
# ---------------------------------------------------------------------------


def test_fixture_returns_five_entries() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    assert len(entries) == 5


def test_fixture_entries_are_clarity_entry_instances() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    assert len(entries) > 0
    for e in entries:
        assert isinstance(e, ClarityEntry)


def test_fixture_round_numbers() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    rounds = [e.round for e in entries]
    assert rounds.count(1) == 3
    assert rounds.count(2) == 2


def test_fixture_question_non_empty() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    for e in entries:
        assert e.question.strip() != ""


def test_fixture_answer_non_empty() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    for e in entries:
        assert e.answer.strip() != ""


def test_fixture_decision_non_empty() -> None:
    entries = parse_clarity_log(FIXTURES_DIR / "CLARITY_LOG.md")
    for e in entries:
        assert e.decision.strip() != ""


# ---------------------------------------------------------------------------
# Single block — basic field extraction
# ---------------------------------------------------------------------------

_SINGLE_BLOCK = """\
# CLARITY_LOG

```
Round: 1
Spec: myspec.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: What is the format of the input file?
A: It uses YAML front-matter followed by Markdown body.
Confidence: 0.90
Remaining_Ambiguity: None.
Resolution: Parse front-matter with pyyaml, then extract body.
---
```
"""


def test_single_block_produces_one_entry(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    entries = parse_clarity_log(p)
    assert len(entries) == 1


def test_single_block_round(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert parse_clarity_log(p)[0].round == 1


def test_single_block_question(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert parse_clarity_log(p)[0].question == "What is the format of the input file?"


def test_single_block_answer(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert "YAML front-matter" in parse_clarity_log(p)[0].answer


def test_single_block_decision(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert "pyyaml" in parse_clarity_log(p)[0].decision


# ---------------------------------------------------------------------------
# Multi-line field values
# ---------------------------------------------------------------------------

_MULTILINE_BLOCK = """\
```
Round: 2
Spec: spec.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: How should pagination work when the dataset is large?
The default page size is not defined anywhere.
Is it 10, 20, or 100?
A: After reviewing the existing API endpoints in the repository,
pagination defaults to 20 items per page.
The frontend uses hardcoded values that confirm this.
Confidence: 0.85
Remaining_Ambiguity: None significant.
Resolution: Default page size is 20. Expose as a configurable constant
PAGE_SIZE = 20 in settings.py. Document in API reference.
---
```
"""


def test_multiline_question_captured(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTILINE_BLOCK)
    q = parse_clarity_log(p)[0].question
    assert "How should pagination work" in q
    assert "Is it 10, 20, or 100?" in q


def test_multiline_answer_captured(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTILINE_BLOCK)
    a = parse_clarity_log(p)[0].answer
    assert "pagination defaults to 20" in a
    assert "frontend uses hardcoded values" in a


def test_multiline_resolution_captured(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTILINE_BLOCK)
    d = parse_clarity_log(p)[0].decision
    assert "PAGE_SIZE = 20" in d
    assert "Document in API reference" in d


def test_multiline_round(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTILINE_BLOCK)
    assert parse_clarity_log(p)[0].round == 2


# ---------------------------------------------------------------------------
# Multiple blocks in one file
# ---------------------------------------------------------------------------

_MULTI_BLOCKS = """\
```
Round: 1
Spec: a.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: Question one?
A: Answer one.
Confidence: 0.9
Remaining_Ambiguity: None.
Resolution: Decision one.
---
```

Some prose between blocks.

```
Round: 1
Spec: a.md
Category: EDGE_CASE
Severity: MINOR
Q: Question two?
A: Answer two.
Confidence: 0.8
Remaining_Ambiguity: None.
Resolution: Decision two.
---
```

```
Round: 2
Spec: b.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: Question three spanning
multiple lines.
A: Answer three.
Confidence: 0.7
Remaining_Ambiguity: None.
Resolution: Decision three.
---
```
"""


def test_multiple_blocks_count(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTI_BLOCKS)
    assert len(parse_clarity_log(p)) == 3


def test_multiple_blocks_round_values(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTI_BLOCKS)
    entries = parse_clarity_log(p)
    assert entries[0].round == 1
    assert entries[1].round == 1
    assert entries[2].round == 2


def test_multiple_blocks_questions(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTI_BLOCKS)
    entries = parse_clarity_log(p)
    assert entries[0].question == "Question one?"
    assert entries[1].question == "Question two?"
    assert "Question three spanning" in entries[2].question
    assert "multiple lines." in entries[2].question


def test_multiple_blocks_decisions(tmp_path: Path) -> None:
    p = _write(tmp_path, _MULTI_BLOCKS)
    entries = parse_clarity_log(p)
    assert entries[0].decision == "Decision one."
    assert entries[1].decision == "Decision two."
    assert entries[2].decision == "Decision three."


# ---------------------------------------------------------------------------
# Missing optional fields
# ---------------------------------------------------------------------------

_MISSING_ANSWER = """\
```
Round: 1
Spec: spec.md
Category: EDGE_CASE
Severity: MINOR
Q: Is fallback needed?
Confidence: 0.5
Remaining_Ambiguity: None.
Resolution: Not needed for v1.
---
```
"""


def test_missing_answer_defaults_to_empty_string(tmp_path: Path) -> None:
    p = _write(tmp_path, _MISSING_ANSWER)
    assert parse_clarity_log(p)[0].answer == ""


def test_missing_answer_does_not_raise(tmp_path: Path) -> None:
    p = _write(tmp_path, _MISSING_ANSWER)
    entries = parse_clarity_log(p)
    assert len(entries) == 1


_MISSING_RESOLUTION = """\
```
Round: 1
Spec: spec.md
Category: UNDEFINED_TERM
Severity: MAJOR
Q: What is X?
A: X is Y.
Confidence: 0.8
Remaining_Ambiguity: None.
---
```
"""


def test_missing_resolution_defaults_to_empty_string(tmp_path: Path) -> None:
    p = _write(tmp_path, _MISSING_RESOLUTION)
    assert parse_clarity_log(p)[0].decision == ""


# ---------------------------------------------------------------------------
# Invalid blocks — skipped gracefully
# ---------------------------------------------------------------------------

_NO_ROUND = """\
```
Spec: spec.md
Category: EDGE_CASE
Q: A question without round?
A: An answer.
Resolution: A decision.
---
```
"""


def test_block_without_round_skipped(tmp_path: Path) -> None:
    p = _write(tmp_path, _NO_ROUND)
    assert parse_clarity_log(p) == []


_NO_Q = """\
```
Round: 1
Spec: spec.md
Category: EDGE_CASE
A: An answer without question.
Resolution: A decision.
---
```
"""


def test_block_without_q_skipped(tmp_path: Path) -> None:
    p = _write(tmp_path, _NO_Q)
    assert parse_clarity_log(p) == []


_BAD_ROUND = """\
```
Round: alpha
Spec: spec.md
Category: EDGE_CASE
Q: Question?
A: Answer.
Resolution: Decision.
---
```
"""


def test_block_with_non_integer_round_skipped(tmp_path: Path) -> None:
    p = _write(tmp_path, _BAD_ROUND)
    assert parse_clarity_log(p) == []


_MIXED_VALID_INVALID = """\
```
Round: not-a-number
Q: Invalid block.
A: Ignored.
Resolution: Ignored.
---
```

```
Round: 3
Spec: good.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: Valid block?
A: Yes.
Resolution: Proceed.
---
```
"""


def test_mixed_blocks_only_valid_returned(tmp_path: Path) -> None:
    p = _write(tmp_path, _MIXED_VALID_INVALID)
    entries = parse_clarity_log(p)
    assert len(entries) == 1
    assert entries[0].round == 3


# ---------------------------------------------------------------------------
# Return type and field types
# ---------------------------------------------------------------------------


def test_return_type_is_list(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert isinstance(parse_clarity_log(p), list)


def test_entries_are_clarity_entry(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    for e in parse_clarity_log(p):
        assert isinstance(e, ClarityEntry)


def test_round_is_int(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert isinstance(parse_clarity_log(p)[0].round, int)


def test_question_is_str(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert isinstance(parse_clarity_log(p)[0].question, str)


def test_answer_is_str(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert isinstance(parse_clarity_log(p)[0].answer, str)


def test_decision_is_str(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    assert isinstance(parse_clarity_log(p)[0].decision, str)


# ---------------------------------------------------------------------------
# Path types accepted
# ---------------------------------------------------------------------------


def test_accepts_string_path(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    entries = parse_clarity_log(str(p))
    assert len(entries) == 1


def test_accepts_pathlib_path(tmp_path: Path) -> None:
    p = _write(tmp_path, _SINGLE_BLOCK)
    entries = parse_clarity_log(p)
    assert len(entries) == 1


# ---------------------------------------------------------------------------
# Block without --- terminator (unterminated)
# ---------------------------------------------------------------------------

_UNTERMINATED_BLOCK = """\
```
Round: 1
Spec: spec.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: Is unterminated block handled?
A: Yes, gracefully.
Resolution: Still parse it.
```
"""


def test_unterminated_block_parsed(tmp_path: Path) -> None:
    p = _write(tmp_path, _UNTERMINATED_BLOCK)
    entries = parse_clarity_log(p)
    assert len(entries) == 1
    assert "unterminated block" in entries[0].question


def test_unterminated_block_decision(tmp_path: Path) -> None:
    p = _write(tmp_path, _UNTERMINATED_BLOCK)
    assert "Still parse it" in parse_clarity_log(p)[0].decision
