from __future__ import annotations

from pathlib import Path

from agent_harvest.models import HarvestRule
from agent_harvest.skill_writer import write_skills


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rule(
    id: str,
    rule: str,
    stacks: list[str],
    confidence: str,
    source_projects: list[str] | None = None,
    category: str = "pattern",
    applicable_to: str = "all",
) -> HarvestRule:
    return HarvestRule(
        id=id,
        category=category,
        stacks=stacks,
        confidence=confidence,
        source_projects=source_projects or ["proj-a"],
        rule=rule,
        applicable_to=applicable_to,
    )


# ---------------------------------------------------------------------------
# Low-confidence exclusion
# ---------------------------------------------------------------------------

class TestLowConfidenceExclusion:
    def test_low_confidence_excluded(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "some rule", ["python"], "low")]
        result = write_skills(rules, tmp_path)
        assert result == []
        assert not (tmp_path / "skills").exists()

    def test_medium_included(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "some rule", ["python"], "medium")]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1

    def test_high_included(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "some rule", ["python"], "high")]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1

    def test_mixed_confidence_only_high_med_written(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high"),
            _rule("r2", "rule two", ["python"], "low"),
            _rule("r3", "rule three", ["python"], "medium"),
        ]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1
        content = result[0].read_text()
        assert "rule one" in content
        assert "rule three" in content
        assert "rule two" not in content

    def test_all_low_returns_empty(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "low"),
            _rule("r2", "rule two", ["java"], "low"),
        ]
        assert write_skills(rules, tmp_path) == []

    def test_empty_rules_returns_empty(self, tmp_path: Path) -> None:
        assert write_skills([], tmp_path) == []


# ---------------------------------------------------------------------------
# Grouping by primary stack
# ---------------------------------------------------------------------------

class TestGroupingByStack:
    def test_two_stacks_produce_two_files(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "python rule", ["python"], "high"),
            _rule("r2", "java rule", ["java"], "medium"),
        ]
        result = write_skills(rules, tmp_path)
        assert len(result) == 2
        names = {p.name for p in result}
        assert "python-common.md" in names
        assert "java-common.md" in names

    def test_single_stack_one_file(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high"),
            _rule("r2", "rule two", ["python"], "medium"),
        ]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1
        assert result[0].name == "python-common.md"

    def test_empty_stacks_grouped_as_all(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "universal rule", [], "high")]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1
        assert result[0].name == "all-common.md"

    def test_primary_stack_is_first_element(self, tmp_path: Path) -> None:
        # Rule has stacks=["rust", "python"] — should go into rust-common.md
        rules = [_rule("r1", "rust rule", ["rust", "python"], "high")]
        result = write_skills(rules, tmp_path)
        assert len(result) == 1
        assert result[0].name == "rust-common.md"

    def test_multi_stack_rules_split_by_primary(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule a", ["go", "docker"], "high"),
            _rule("r2", "rule b", ["python", "docker"], "medium"),
        ]
        result = write_skills(rules, tmp_path)
        assert len(result) == 2
        names = {p.name for p in result}
        assert "go-common.md" in names
        assert "python-common.md" in names

    def test_three_stacks_produce_three_files(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high"),
            _rule("r2", "rule two", ["java"], "medium"),
            _rule("r3", "rule three", ["rust"], "high"),
        ]
        result = write_skills(rules, tmp_path)
        assert len(result) == 3

    def test_output_in_skills_subdir(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["python"], "high")]
        result = write_skills(rules, tmp_path)
        assert result[0].parent == tmp_path / "skills"

    def test_skills_dir_created(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["python"], "high")]
        write_skills(rules, tmp_path)
        assert (tmp_path / "skills").is_dir()


# ---------------------------------------------------------------------------
# Markdown structure
# ---------------------------------------------------------------------------

class TestMarkdownStructure:
    def test_title_header(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "some rule", ["python"], "high")]
        written = write_skills(rules, tmp_path)
        content = written[0].read_text()
        assert content.startswith("# Python Common Rules")

    def test_all_title_capitalized(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "some rule", [], "high")]
        written = write_skills(rules, tmp_path)
        content = written[0].read_text()
        assert "# All Common Rules" in content

    def test_source_section_present(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["python"], "high", source_projects=["proj-x"])]
        content = write_skills(rules, tmp_path)[0].read_text()
        assert "## Source" in content

    def test_source_lists_projects(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high", source_projects=["alpha"]),
            _rule("r2", "rule two", ["python"], "medium", source_projects=["beta"]),
        ]
        content = write_skills(rules, tmp_path)[0].read_text()
        assert "- alpha" in content
        assert "- beta" in content

    def test_source_deduplicates_projects(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high", source_projects=["alpha"]),
            _rule("r2", "rule two", ["python"], "medium", source_projects=["alpha"]),
        ]
        content = write_skills(rules, tmp_path)[0].read_text()
        assert content.count("- alpha") == 1

    def test_rules_appear_as_bullets(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "use context managers", ["python"], "high"),
            _rule("r2", "prefer f-strings", ["python"], "medium"),
        ]
        content = write_skills(rules, tmp_path)[0].read_text()
        assert "- use context managers" in content
        assert "- prefer f-strings" in content

    def test_source_before_rules(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "some rule", ["python"], "high", source_projects=["proj-a"]),
        ]
        content = write_skills(rules, tmp_path)[0].read_text()
        source_pos = content.index("## Source")
        rule_pos = content.index("- some rule")
        assert source_pos < rule_pos

    def test_title_before_source(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["python"], "high")]
        content = write_skills(rules, tmp_path)[0].read_text()
        title_pos = content.index("# Python Common Rules")
        source_pos = content.index("## Source")
        assert title_pos < source_pos

    def test_multi_project_source_all_listed(self, tmp_path: Path) -> None:
        rules = [
            _rule(
                "r1",
                "a rule",
                ["python"],
                "high",
                source_projects=["proj-a", "proj-b", "proj-c"],
            )
        ]
        content = write_skills(rules, tmp_path)[0].read_text()
        assert "- proj-a" in content
        assert "- proj-b" in content
        assert "- proj-c" in content


# ---------------------------------------------------------------------------
# Output file naming
# ---------------------------------------------------------------------------

class TestOutputFileNaming:
    def test_filename_pattern(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["nodejs"], "high")]
        result = write_skills(rules, tmp_path)
        assert result[0].name == "nodejs-common.md"

    def test_all_filename(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", [], "medium")]
        result = write_skills(rules, tmp_path)
        assert result[0].name == "all-common.md"

    def test_returns_paths(self, tmp_path: Path) -> None:
        rules = [_rule("r1", "rule", ["python"], "high")]
        result = write_skills(rules, tmp_path)
        assert all(isinstance(p, Path) for p in result)

    def test_files_exist_after_write(self, tmp_path: Path) -> None:
        rules = [
            _rule("r1", "rule one", ["python"], "high"),
            _rule("r2", "rule two", ["java"], "medium"),
        ]
        result = write_skills(rules, tmp_path)
        for p in result:
            assert p.exists()

    def test_sorted_output(self, tmp_path: Path) -> None:
        # Output list is sorted by stack name alphabetically
        rules = [
            _rule("r1", "rule z", ["python"], "high"),
            _rule("r2", "rule a", ["java"], "medium"),
            _rule("r3", "rule m", ["go"], "high"),
        ]
        result = write_skills(rules, tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)
