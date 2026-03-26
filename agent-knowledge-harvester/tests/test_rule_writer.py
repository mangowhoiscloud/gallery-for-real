from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent_harvest.models import HarvestRule
from agent_harvest.rule_writer import write_rules


def _make_rule(
    id: str = "test-rule",
    category: str = "pattern",
    stacks: list[str] | None = None,
    confidence: str = "low",
    source_projects: list[str] | None = None,
    rule: str = "some rule text",
    applicable_to: str = "all",
) -> HarvestRule:
    return HarvestRule(
        id=id,
        category=category,
        stacks=stacks if stacks is not None else ["python"],
        confidence=confidence,
        source_projects=source_projects or ["proj-a"],
        rule=rule,
        applicable_to=applicable_to,
    )


# ---------------------------------------------------------------------------
# YAML output
# ---------------------------------------------------------------------------


class TestWriteRulesYaml:
    def test_creates_rules_directory(self, tmp_path: Path) -> None:
        write_rules([_make_rule()], tmp_path)
        assert (tmp_path / "rules").is_dir()

    def test_three_rules_produce_three_files(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="rule-one"),
            _make_rule(id="rule-two"),
            _make_rule(id="rule-three"),
        ]
        written = write_rules(rules, tmp_path)
        assert len(written) == 3
        assert all(f.exists() for f in written)

    def test_yaml_filename_is_rule_id(self, tmp_path: Path) -> None:
        write_rules([_make_rule(id="python-datetime")], tmp_path)
        assert (tmp_path / "rules" / "python-datetime.yaml").exists()

    def test_yaml_content_is_valid(self, tmp_path: Path) -> None:
        rule = _make_rule(id="my-rule")
        write_rules([rule], tmp_path)
        content = (tmp_path / "rules" / "my-rule.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)
        assert parsed["id"] == "my-rule"
        assert parsed["category"] == "pattern"

    def test_yaml_roundtrip_safe(self, tmp_path: Path) -> None:
        rule = _make_rule(id="roundtrip")
        write_rules([rule], tmp_path)
        content = (tmp_path / "rules" / "roundtrip.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        dumped = yaml.safe_dump(parsed, allow_unicode=True, default_flow_style=False)
        reparsed = yaml.safe_load(dumped)
        assert parsed == reparsed

    def test_korean_text_preserved(self, tmp_path: Path) -> None:
        korean = "Python 3.11+에서 timezone-aware ISO 8601을 지원"
        rule = _make_rule(id="korean-rule", rule=korean)
        write_rules([rule], tmp_path)
        content = (tmp_path / "rules" / "korean-rule.yaml").read_text(encoding="utf-8")
        assert korean in content

    def test_korean_text_not_escaped_in_yaml(self, tmp_path: Path) -> None:
        rule = _make_rule(id="korean-rule", rule="안녕하세요")
        write_rules([rule], tmp_path)
        content = (tmp_path / "rules" / "korean-rule.yaml").read_text(encoding="utf-8")
        assert "\\u" not in content

    def test_returns_written_paths(self, tmp_path: Path) -> None:
        rules = [_make_rule(id="one"), _make_rule(id="two")]
        written = write_rules(rules, tmp_path)
        assert len(written) == 2
        assert all(isinstance(p, Path) for p in written)

    def test_default_format_is_yaml(self, tmp_path: Path) -> None:
        write_rules([_make_rule(id="default")], tmp_path)
        assert (tmp_path / "rules" / "default.yaml").exists()
        assert not (tmp_path / "rules" / "default.json").exists()

    def test_all_fields_present_in_yaml(self, tmp_path: Path) -> None:
        rule = HarvestRule(
            id="full-rule",
            category="library-quirk",
            stacks=["python", "django"],
            confidence="high",
            source_projects=["proj-a", "proj-b"],
            rule="Always use select_related for FK traversal",
            applicable_to="Django ORM queries",
        )
        write_rules([rule], tmp_path)
        parsed = yaml.safe_load(
            (tmp_path / "rules" / "full-rule.yaml").read_text(encoding="utf-8")
        )
        assert parsed["stacks"] == ["python", "django"]
        assert parsed["source_projects"] == ["proj-a", "proj-b"]
        assert parsed["confidence"] == "high"
        assert parsed["applicable_to"] == "Django ORM queries"

    def test_empty_rules_list_returns_empty(self, tmp_path: Path) -> None:
        written = write_rules([], tmp_path)
        assert written == []

    def test_output_dir_created_if_not_exists(self, tmp_path: Path) -> None:
        nested = tmp_path / "deep" / "output"
        write_rules([_make_rule()], nested)
        assert (nested / "rules").is_dir()

    def test_multiline_rule_text_preserved(self, tmp_path: Path) -> None:
        rule = _make_rule(
            id="multiline",
            rule="Line one.\nLine two.\nLine three.",
        )
        write_rules([rule], tmp_path)
        content = (tmp_path / "rules" / "multiline.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert "Line one." in parsed["rule"]
        assert "Line two." in parsed["rule"]

    def test_stacks_list_serialized_correctly(self, tmp_path: Path) -> None:
        rule = _make_rule(id="multi-stack", stacks=["python", "django", "celery"])
        write_rules([rule], tmp_path)
        parsed = yaml.safe_load(
            (tmp_path / "rules" / "multi-stack.yaml").read_text(encoding="utf-8")
        )
        assert parsed["stacks"] == ["python", "django", "celery"]

    def test_source_projects_list_serialized_correctly(self, tmp_path: Path) -> None:
        rule = _make_rule(
            id="multi-proj", source_projects=["proj-a", "proj-b", "proj-c"]
        )
        write_rules([rule], tmp_path)
        parsed = yaml.safe_load(
            (tmp_path / "rules" / "multi-proj.yaml").read_text(encoding="utf-8")
        )
        assert parsed["source_projects"] == ["proj-a", "proj-b", "proj-c"]


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


class TestWriteRulesJson:
    def test_json_format_produces_json_file(self, tmp_path: Path) -> None:
        write_rules([_make_rule(id="json-rule")], tmp_path, format="json")
        assert (tmp_path / "rules" / "json-rule.json").exists()

    def test_no_yaml_file_in_json_mode(self, tmp_path: Path) -> None:
        write_rules([_make_rule(id="json-rule")], tmp_path, format="json")
        assert not (tmp_path / "rules" / "json-rule.yaml").exists()

    def test_json_content_is_valid(self, tmp_path: Path) -> None:
        rule = _make_rule(id="json-content")
        write_rules([rule], tmp_path, format="json")
        content = (tmp_path / "rules" / "json-content.json").read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert parsed["id"] == "json-content"
        assert parsed["category"] == "pattern"

    def test_json_indented(self, tmp_path: Path) -> None:
        write_rules([_make_rule(id="indented")], tmp_path, format="json")
        content = (tmp_path / "rules" / "indented.json").read_text(encoding="utf-8")
        assert "\n" in content

    def test_json_korean_not_escaped(self, tmp_path: Path) -> None:
        rule = _make_rule(id="korean-json", rule="한국어 텍스트")
        write_rules([rule], tmp_path, format="json")
        content = (tmp_path / "rules" / "korean-json.json").read_text(encoding="utf-8")
        assert "한국어 텍스트" in content
        assert "\\u" not in content

    def test_json_three_rules(self, tmp_path: Path) -> None:
        rules = [_make_rule(id=f"r{i}") for i in range(3)]
        written = write_rules(rules, tmp_path, format="json")
        assert len(written) == 3

    def test_json_all_fields_present(self, tmp_path: Path) -> None:
        rule = HarvestRule(
            id="full-json",
            category="error-recovery",
            stacks=["java"],
            confidence="medium",
            source_projects=["svc-a"],
            rule="Use try-with-resources for AutoCloseable",
            applicable_to="all Java projects",
        )
        write_rules([rule], tmp_path, format="json")
        parsed = json.loads(
            (tmp_path / "rules" / "full-json.json").read_text(encoding="utf-8")
        )
        assert parsed["stacks"] == ["java"]
        assert parsed["confidence"] == "medium"
        assert parsed["rule"] == "Use try-with-resources for AutoCloseable"

    def test_json_returns_path_list(self, tmp_path: Path) -> None:
        written = write_rules([_make_rule(id="j1")], tmp_path, format="json")
        assert len(written) == 1
        assert written[0].suffix == ".json"


# ---------------------------------------------------------------------------
# Confidence filtering
# ---------------------------------------------------------------------------


class TestConfidenceFilter:
    def test_min_confidence_low_includes_all(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="low-r", confidence="low"),
            _make_rule(id="med-r", confidence="medium"),
            _make_rule(id="high-r", confidence="high"),
        ]
        written = write_rules(rules, tmp_path, min_confidence="low")
        assert len(written) == 3

    def test_min_confidence_medium_excludes_low(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="low-r", confidence="low"),
            _make_rule(id="med-r", confidence="medium"),
            _make_rule(id="high-r", confidence="high"),
        ]
        written = write_rules(rules, tmp_path, min_confidence="medium")
        ids = [p.stem for p in written]
        assert "low-r" not in ids
        assert "med-r" in ids
        assert "high-r" in ids

    def test_min_confidence_high_only_high(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="low-r", confidence="low"),
            _make_rule(id="med-r", confidence="medium"),
            _make_rule(id="high-r", confidence="high"),
        ]
        written = write_rules(rules, tmp_path, min_confidence="high")
        assert len(written) == 1
        assert written[0].stem == "high-r"

    def test_min_confidence_high_excludes_all_lower(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="low-r", confidence="low"),
            _make_rule(id="med-r", confidence="medium"),
        ]
        written = write_rules(rules, tmp_path, min_confidence="high")
        assert written == []

    def test_default_min_confidence_is_low(self, tmp_path: Path) -> None:
        rules = [_make_rule(id="low-r", confidence="low")]
        written = write_rules(rules, tmp_path)
        assert len(written) == 1

    def test_medium_included_with_medium_threshold(self, tmp_path: Path) -> None:
        rule = _make_rule(id="med", confidence="medium")
        written = write_rules([rule], tmp_path, min_confidence="medium")
        assert len(written) == 1

    def test_high_included_with_medium_threshold(self, tmp_path: Path) -> None:
        rule = _make_rule(id="high", confidence="high")
        written = write_rules([rule], tmp_path, min_confidence="medium")
        assert len(written) == 1


# ---------------------------------------------------------------------------
# Stack filtering
# ---------------------------------------------------------------------------


class TestStackFilter:
    def test_no_stack_filter_writes_all(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="python-r", stacks=["python"]),
            _make_rule(id="java-r", stacks=["java"]),
        ]
        written = write_rules(rules, tmp_path)
        assert len(written) == 2

    def test_stack_filter_python_excludes_java(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="python-r", stacks=["python"]),
            _make_rule(id="java-r", stacks=["java"]),
        ]
        written = write_rules(rules, tmp_path, stack="python")
        assert len(written) == 1
        assert written[0].stem == "python-r"

    def test_stack_filter_includes_multi_stack_rule(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="multi-r", stacks=["python", "django"]),
        ]
        written = write_rules(rules, tmp_path, stack="django")
        assert len(written) == 1

    def test_stack_filter_excludes_non_matching(self, tmp_path: Path) -> None:
        rules = [_make_rule(id="go-r", stacks=["go"])]
        written = write_rules(rules, tmp_path, stack="python")
        assert written == []

    def test_stack_filter_none_means_no_filter(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="r1", stacks=["python"]),
            _make_rule(id="r2", stacks=["rust"]),
            _make_rule(id="r3", stacks=[]),
        ]
        written = write_rules(rules, tmp_path, stack=None)
        assert len(written) == 3

    def test_rule_with_empty_stacks_included_without_filter(self, tmp_path: Path) -> None:
        rule = _make_rule(id="all-stacks", stacks=[])
        written = write_rules([rule], tmp_path)
        assert len(written) == 1

    def test_rule_with_empty_stacks_included_even_when_stack_filter_set(
        self, tmp_path: Path
    ) -> None:
        # Empty stacks means "all" — rule applies to every stack, so always passes filter
        rule = _make_rule(id="all-stacks", stacks=[])
        written = write_rules([rule], tmp_path, stack="python")
        assert len(written) == 1

    def test_combined_confidence_and_stack_filter(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="py-high", stacks=["python"], confidence="high"),
            _make_rule(id="py-low", stacks=["python"], confidence="low"),
            _make_rule(id="go-high", stacks=["go"], confidence="high"),
        ]
        written = write_rules(rules, tmp_path, min_confidence="medium", stack="python")
        assert len(written) == 1
        assert written[0].stem == "py-high"

    def test_stack_filter_go(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="go-r", stacks=["go"]),
            _make_rule(id="py-r", stacks=["python"]),
        ]
        written = write_rules(rules, tmp_path, stack="go")
        assert len(written) == 1
        assert written[0].stem == "go-r"

    def test_stack_filter_multiple_matching_rules(self, tmp_path: Path) -> None:
        rules = [
            _make_rule(id="py-r1", stacks=["python"]),
            _make_rule(id="py-r2", stacks=["python", "django"]),
            _make_rule(id="java-r", stacks=["java"]),
        ]
        written = write_rules(rules, tmp_path, stack="python")
        ids = {p.stem for p in written}
        assert ids == {"py-r1", "py-r2"}
