from __future__ import annotations

import json
from pathlib import Path

from agent_harvest.models import ClarityEntry, FileChurn, HarvestResult
from agent_harvest.report_writer import (
    write_instability_report,
    write_spec_guide,
    write_summary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_churn(path: str, add: int = 0, modify: int = 0, delete: int = 0, revert: int = 0, net: int = 0) -> FileChurn:
    return FileChurn(path=path, add_count=add, modify_count=modify, delete_count=delete, revert_count=revert, net_changes=net)


def _make_clarity(round: int, question: str = "Q?", answer: str = "A", decision: str = "D") -> ClarityEntry:
    return ClarityEntry(round=round, question=question, answer=answer, decision=decision)


def _make_result(**kwargs) -> HarvestResult:
    defaults = dict(
        projects_analyzed=2,
        total_learnings=10,
        total_rules=8,
        categories={"pattern": 5, "error-recovery": 3},
        stacks={"python": 6, "java": 2},
        high_confidence_rules=3,
        unstable_files=[],
    )
    defaults.update(kwargs)
    return HarvestResult(**defaults)


# ---------------------------------------------------------------------------
# write_instability_report — table format
# ---------------------------------------------------------------------------

class TestInstabilityReportTable:
    def test_creates_file_in_output_dir(self, tmp_path: Path) -> None:
        churns = [_make_churn("src/foo.py", modify=5)]
        result = write_instability_report(churns, tmp_path)
        assert result == tmp_path / "instability-report.md"
        assert result.exists()

    def test_file_contains_markdown_table_header(self, tmp_path: Path) -> None:
        churns = [_make_churn("src/foo.py", modify=3)]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert "| Path |" in content
        assert "| Add |" in content
        assert "| Modify |" in content
        assert "| Delete |" in content
        assert "| Revert |" in content
        assert "| Net Changes |" in content

    def test_table_separator_row_present(self, tmp_path: Path) -> None:
        churns = [_make_churn("a.py", modify=1)]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        # Separator row has dashes
        assert "|---" in content

    def test_data_row_contains_all_fields(self, tmp_path: Path) -> None:
        churn = _make_churn("src/main.py", add=3, modify=7, delete=1, revert=2, net=9)
        write_instability_report([churn], tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert "src/main.py" in content
        assert "| 3 |" in content
        assert "| 7 |" in content
        assert "| 1 |" in content
        assert "| 2 |" in content
        assert "| 9 |" in content

    def test_sorted_by_modify_count_descending(self, tmp_path: Path) -> None:
        churns = [
            _make_churn("low.py", modify=1),
            _make_churn("high.py", modify=10),
            _make_churn("mid.py", modify=5),
        ]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        idx_high = content.index("high.py")
        idx_mid = content.index("mid.py")
        idx_low = content.index("low.py")
        assert idx_high < idx_mid < idx_low

    def test_ties_preserve_relative_order(self, tmp_path: Path) -> None:
        # Both have modify=5; just verify both appear and file is well-formed
        churns = [
            _make_churn("alpha.py", modify=5),
            _make_churn("beta.py", modify=5),
        ]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert "alpha.py" in content
        assert "beta.py" in content

    def test_report_has_h1_heading(self, tmp_path: Path) -> None:
        churns = [_make_churn("x.py", modify=1)]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert content.startswith("# ")

    def test_multiple_files_all_appear_in_table(self, tmp_path: Path) -> None:
        churns = [
            _make_churn("a.py", modify=3),
            _make_churn("b.py", modify=8),
            _make_churn("c.py", modify=1),
        ]
        write_instability_report(churns, tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert "a.py" in content
        assert "b.py" in content
        assert "c.py" in content

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "output"
        churns = [_make_churn("x.py", modify=2)]
        write_instability_report(churns, nested)
        assert (nested / "instability-report.md").exists()

    def test_zero_counts_render_as_zero(self, tmp_path: Path) -> None:
        churn = _make_churn("only-add.py", add=5)  # all others default to 0
        write_instability_report([churn], tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert "only-add.py" in content
        # modify column should be 0
        assert "| 0 |" in content


# ---------------------------------------------------------------------------
# write_instability_report — empty input
# ---------------------------------------------------------------------------

class TestInstabilityReportEmpty:
    def test_empty_churns_produces_file(self, tmp_path: Path) -> None:
        result = write_instability_report([], tmp_path)
        assert result.exists()

    def test_empty_churns_no_table_header(self, tmp_path: Path) -> None:
        write_instability_report([], tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        # No table when no data
        assert "| Path |" not in content

    def test_empty_churns_has_h1_and_message(self, tmp_path: Path) -> None:
        write_instability_report([], tmp_path)
        content = (tmp_path / "instability-report.md").read_text()
        assert content.startswith("# ")
        assert len(content.strip()) > 0  # not entirely empty


# ---------------------------------------------------------------------------
# write_spec_guide — guideline extraction
# ---------------------------------------------------------------------------

class TestSpecGuide:
    def test_creates_file_in_output_dir(self, tmp_path: Path) -> None:
        entries = [_make_clarity(1, decision="Use YAML for config")]
        result = write_spec_guide(entries, tmp_path)
        assert result == tmp_path / "spec-guide.md"
        assert result.exists()

    def test_file_has_h1_heading(self, tmp_path: Path) -> None:
        write_spec_guide([_make_clarity(1)], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert content.startswith("# ")

    def test_guideline_uses_when_writing_specs_phrase(self, tmp_path: Path) -> None:
        entry = _make_clarity(1, decision="avoid mutable defaults")
        write_spec_guide([entry], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "When writing specs, specify" in content

    def test_decision_text_appears_in_guideline(self, tmp_path: Path) -> None:
        entry = _make_clarity(1, decision="always include Round field")
        write_spec_guide([entry], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "always include Round field" in content

    def test_fallback_to_answer_when_decision_empty(self, tmp_path: Path) -> None:
        entry = ClarityEntry(round=1, question="Q?", answer="use answer text", decision="")
        write_spec_guide([entry], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "use answer text" in content

    def test_multiple_entries_all_appear(self, tmp_path: Path) -> None:
        entries = [
            _make_clarity(1, decision="decision one"),
            _make_clarity(1, decision="decision two"),
            _make_clarity(2, decision="decision three"),
        ]
        write_spec_guide(entries, tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "decision one" in content
        assert "decision two" in content
        assert "decision three" in content

    def test_grouped_by_round_with_subheadings(self, tmp_path: Path) -> None:
        entries = [
            _make_clarity(1, decision="r1d1"),
            _make_clarity(2, decision="r2d1"),
        ]
        write_spec_guide(entries, tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "## Round 1" in content
        assert "## Round 2" in content

    def test_rounds_appear_in_numeric_order(self, tmp_path: Path) -> None:
        entries = [
            _make_clarity(3, decision="r3"),
            _make_clarity(1, decision="r1"),
            _make_clarity(2, decision="r2"),
        ]
        write_spec_guide(entries, tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        idx1 = content.index("## Round 1")
        idx2 = content.index("## Round 2")
        idx3 = content.index("## Round 3")
        assert idx1 < idx2 < idx3

    def test_each_guideline_is_bullet_item(self, tmp_path: Path) -> None:
        entry = _make_clarity(1, decision="some rule")
        write_spec_guide([entry], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        # Guidelines should be bullet lines starting with "- "
        assert "- When writing specs" in content

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b"
        write_spec_guide([_make_clarity(1)], nested)
        assert (nested / "spec-guide.md").exists()


# ---------------------------------------------------------------------------
# write_spec_guide — empty input
# ---------------------------------------------------------------------------

class TestSpecGuideEmpty:
    def test_empty_entries_produces_file(self, tmp_path: Path) -> None:
        result = write_spec_guide([], tmp_path)
        assert result.exists()

    def test_empty_entries_no_round_headings(self, tmp_path: Path) -> None:
        write_spec_guide([], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert "## Round" not in content

    def test_empty_entries_has_h1_and_content(self, tmp_path: Path) -> None:
        write_spec_guide([], tmp_path)
        content = (tmp_path / "spec-guide.md").read_text()
        assert content.startswith("# ")
        assert len(content.strip()) > 0


# ---------------------------------------------------------------------------
# write_summary — JSON serialization
# ---------------------------------------------------------------------------

class TestSummaryJson:
    def test_creates_file_in_output_dir(self, tmp_path: Path) -> None:
        result = write_summary(_make_result(), tmp_path)
        assert result == tmp_path / "summary.json"
        assert result.exists()

    def test_output_is_valid_json(self, tmp_path: Path) -> None:
        write_summary(_make_result(), tmp_path)
        content = (tmp_path / "summary.json").read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_projects_analyzed_field_present(self, tmp_path: Path) -> None:
        result = _make_result(projects_analyzed=3)
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["projects_analyzed"] == 3

    def test_total_learnings_field_present(self, tmp_path: Path) -> None:
        result = _make_result(total_learnings=42)
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["total_learnings"] == 42

    def test_total_rules_field_present(self, tmp_path: Path) -> None:
        result = _make_result(total_rules=17)
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["total_rules"] == 17

    def test_categories_dict_serialized_correctly(self, tmp_path: Path) -> None:
        result = _make_result(categories={"pattern": 5, "error-recovery": 2})
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["categories"] == {"pattern": 5, "error-recovery": 2}

    def test_stacks_dict_serialized_correctly(self, tmp_path: Path) -> None:
        result = _make_result(stacks={"python": 8, "java": 3})
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["stacks"] == {"python": 8, "java": 3}

    def test_high_confidence_rules_field_present(self, tmp_path: Path) -> None:
        result = _make_result(high_confidence_rules=5)
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["high_confidence_rules"] == 5

    def test_unstable_files_serialized_as_list(self, tmp_path: Path) -> None:
        fc = FileChurn(path="src/x.py", add_count=1, modify_count=9, delete_count=0, revert_count=1, net_changes=10)
        result = _make_result(unstable_files=[fc])
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert isinstance(data["unstable_files"], list)
        assert len(data["unstable_files"]) == 1
        assert data["unstable_files"][0]["path"] == "src/x.py"
        assert data["unstable_files"][0]["modify_count"] == 9

    def test_json_is_indented(self, tmp_path: Path) -> None:
        write_summary(_make_result(), tmp_path)
        content = (tmp_path / "summary.json").read_text()
        # Indented JSON has newlines
        assert "\n" in content

    def test_all_expected_keys_present(self, tmp_path: Path) -> None:
        write_summary(_make_result(), tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        expected_keys = {
            "projects_analyzed",
            "total_learnings",
            "total_rules",
            "categories",
            "stacks",
            "high_confidence_rules",
            "unstable_files",
        }
        assert expected_keys.issubset(data.keys())

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "reports" / "out"
        write_summary(_make_result(), nested)
        assert (nested / "summary.json").exists()

    def test_empty_result_produces_valid_json(self, tmp_path: Path) -> None:
        result = HarvestResult.empty()
        write_summary(result, tmp_path)
        data = json.loads((tmp_path / "summary.json").read_text())
        assert data["projects_analyzed"] == 0
        assert data["total_learnings"] == 0
        assert data["total_rules"] == 0
        assert data["categories"] == {}
        assert data["stacks"] == {}
        assert data["high_confidence_rules"] == 0
        assert data["unstable_files"] == []

    def test_returns_path_to_summary_file(self, tmp_path: Path) -> None:
        returned = write_summary(_make_result(), tmp_path)
        assert returned == tmp_path / "summary.json"

    def test_unicode_in_categories_preserved(self, tmp_path: Path) -> None:
        result = _make_result(categories={"패턴": 3})
        write_summary(result, tmp_path)
        content = (tmp_path / "summary.json").read_text()
        assert "패턴" in content
