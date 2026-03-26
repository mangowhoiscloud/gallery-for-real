"""Tests for data models in models.py."""

from agent_harvest.models import (
    ClarityEntry,
    FileChurn,
    HarvestResult,
    HarvestRule,
    LearningEntry,
)


class TestLearningEntry:
    def test_instantiation_with_valid_data(self) -> None:
        entry = LearningEntry(
            id="python-datetime-parsing",
            category="library-quirk",
            description="datetime.fromisoformat timezone handling",
            context="Discovered when parsing API timestamps",
            applicable_stacks=["python"],
            source_project="tistory-migrator",
            source_file="LEARNINGS.md",
        )
        assert entry.id == "python-datetime-parsing"
        assert entry.category == "library-quirk"
        assert entry.description == "datetime.fromisoformat timezone handling"
        assert entry.context == "Discovered when parsing API timestamps"
        assert entry.applicable_stacks == ["python"]
        assert entry.source_project == "tistory-migrator"
        assert entry.source_file == "LEARNINGS.md"

    def test_applicable_stacks_is_list(self) -> None:
        entry = LearningEntry(
            id="multi-stack",
            category="pattern",
            description="shared pattern",
            context="ctx",
            applicable_stacks=["python", "java"],
            source_project="proj",
            source_file="LEARNINGS.md",
        )
        assert isinstance(entry.applicable_stacks, list)
        assert len(entry.applicable_stacks) == 2

    def test_empty_applicable_stacks(self) -> None:
        entry = LearningEntry(
            id="no-stack",
            category="pattern",
            description="desc",
            context="ctx",
            applicable_stacks=[],
            source_project="proj",
            source_file="progress.txt",
        )
        assert entry.applicable_stacks == []

    def test_equality(self) -> None:
        e1 = LearningEntry("id", "pattern", "desc", "ctx", ["python"], "proj", "LEARNINGS.md")
        e2 = LearningEntry("id", "pattern", "desc", "ctx", ["python"], "proj", "LEARNINGS.md")
        assert e1 == e2

    def test_inequality(self) -> None:
        e1 = LearningEntry("id1", "pattern", "desc", "ctx", [], "proj", "LEARNINGS.md")
        e2 = LearningEntry("id2", "pattern", "desc", "ctx", [], "proj", "LEARNINGS.md")
        assert e1 != e2

    def test_repr_contains_class_name(self) -> None:
        entry = LearningEntry("id", "pattern", "desc", "ctx", [], "proj", "LEARNINGS.md")
        assert "LearningEntry" in repr(entry)

    def test_all_fields_are_correct_types(self) -> None:
        entry = LearningEntry(
            id="test-id",
            category="testing",
            description="some desc",
            context="some ctx",
            applicable_stacks=["nodejs"],
            source_project="my-project",
            source_file="progress.txt",
        )
        assert isinstance(entry.id, str)
        assert isinstance(entry.category, str)
        assert isinstance(entry.description, str)
        assert isinstance(entry.context, str)
        assert isinstance(entry.applicable_stacks, list)
        assert isinstance(entry.source_project, str)
        assert isinstance(entry.source_file, str)


class TestClarityEntry:
    def test_instantiation_with_valid_data(self) -> None:
        entry = ClarityEntry(
            round=1,
            question="What format is LEARNINGS.md?",
            answer="H3 headers with sub-bullets",
            decision="Parse by splitting on ### Learning: headers",
        )
        assert entry.round == 1
        assert entry.question == "What format is LEARNINGS.md?"
        assert entry.answer == "H3 headers with sub-bullets"
        assert entry.decision == "Parse by splitting on ### Learning: headers"

    def test_round_is_int(self) -> None:
        entry = ClarityEntry(round=3, question="q", answer="a", decision="d")
        assert isinstance(entry.round, int)
        assert entry.round == 3

    def test_equality(self) -> None:
        e1 = ClarityEntry(1, "q", "a", "d")
        e2 = ClarityEntry(1, "q", "a", "d")
        assert e1 == e2

    def test_repr_contains_class_name(self) -> None:
        entry = ClarityEntry(1, "q", "a", "d")
        assert "ClarityEntry" in repr(entry)

    def test_all_fields_are_correct_types(self) -> None:
        entry = ClarityEntry(round=2, question="q?", answer="a.", decision="do x")
        assert isinstance(entry.round, int)
        assert isinstance(entry.question, str)
        assert isinstance(entry.answer, str)
        assert isinstance(entry.decision, str)


class TestFileChurn:
    def test_instantiation_with_all_fields(self) -> None:
        churn = FileChurn(
            path="src/main.py",
            add_count=1,
            modify_count=5,
            delete_count=0,
            revert_count=1,
            net_changes=120,
        )
        assert churn.path == "src/main.py"
        assert churn.add_count == 1
        assert churn.modify_count == 5
        assert churn.delete_count == 0
        assert churn.revert_count == 1
        assert churn.net_changes == 120

    def test_default_values_are_zero(self) -> None:
        churn = FileChurn(path="src/utils.py")
        assert churn.add_count == 0
        assert churn.modify_count == 0
        assert churn.delete_count == 0
        assert churn.revert_count == 0
        assert churn.net_changes == 0

    def test_equality(self) -> None:
        c1 = FileChurn("a.py", 1, 2, 0, 0, 10)
        c2 = FileChurn("a.py", 1, 2, 0, 0, 10)
        assert c1 == c2

    def test_repr_contains_class_name(self) -> None:
        churn = FileChurn("a.py")
        assert "FileChurn" in repr(churn)

    def test_all_fields_are_correct_types(self) -> None:
        churn = FileChurn(path="x.py", add_count=1, modify_count=2, delete_count=3,
                          revert_count=0, net_changes=99)
        assert isinstance(churn.path, str)
        assert isinstance(churn.add_count, int)
        assert isinstance(churn.modify_count, int)
        assert isinstance(churn.delete_count, int)
        assert isinstance(churn.revert_count, int)
        assert isinstance(churn.net_changes, int)


class TestHarvestRule:
    def test_instantiation_with_valid_data(self) -> None:
        rule = HarvestRule(
            id="python-datetime-parsing",
            category="library-quirk",
            stacks=["python"],
            confidence="high",
            source_projects=["proj-a", "proj-b", "proj-c"],
            rule="Use datetime.fromisoformat() only on Python 3.11+",
            applicable_to="All Python projects that parse ISO dates",
        )
        assert rule.id == "python-datetime-parsing"
        assert rule.category == "library-quirk"
        assert rule.stacks == ["python"]
        assert rule.confidence == "high"
        assert rule.source_projects == ["proj-a", "proj-b", "proj-c"]
        assert rule.rule == "Use datetime.fromisoformat() only on Python 3.11+"
        assert rule.applicable_to == "All Python projects that parse ISO dates"

    def test_stacks_is_list(self) -> None:
        rule = HarvestRule("id", "pattern", ["python", "java"], "low", ["p"], "r", "a")
        assert isinstance(rule.stacks, list)

    def test_source_projects_is_list(self) -> None:
        rule = HarvestRule("id", "pattern", [], "medium", ["proj1", "proj2"], "r", "a")
        assert isinstance(rule.source_projects, list)
        assert len(rule.source_projects) == 2

    def test_equality(self) -> None:
        r1 = HarvestRule("id", "pattern", [], "low", [], "rule", "app")
        r2 = HarvestRule("id", "pattern", [], "low", [], "rule", "app")
        assert r1 == r2

    def test_repr_contains_class_name(self) -> None:
        rule = HarvestRule("id", "pattern", [], "low", [], "rule", "app")
        assert "HarvestRule" in repr(rule)

    def test_all_fields_are_correct_types(self) -> None:
        rule = HarvestRule(
            id="r",
            category="testing",
            stacks=["python"],
            confidence="medium",
            source_projects=["p1"],
            rule="some rule",
            applicable_to="Python test projects",
        )
        assert isinstance(rule.id, str)
        assert isinstance(rule.category, str)
        assert isinstance(rule.stacks, list)
        assert isinstance(rule.confidence, str)
        assert isinstance(rule.source_projects, list)
        assert isinstance(rule.rule, str)
        assert isinstance(rule.applicable_to, str)


class TestHarvestResult:
    def test_instantiation_with_valid_data(self) -> None:
        result = HarvestResult(
            projects_analyzed=3,
            total_learnings=12,
            total_rules=8,
            categories={"library-quirk": 4, "pattern": 4},
            stacks={"python": 6, "java": 2},
            high_confidence_rules=3,
            unstable_files=[FileChurn("src/main.py", modify_count=8)],
        )
        assert result.projects_analyzed == 3
        assert result.total_learnings == 12
        assert result.total_rules == 8
        assert result.categories == {"library-quirk": 4, "pattern": 4}
        assert result.stacks == {"python": 6, "java": 2}
        assert result.high_confidence_rules == 3
        assert len(result.unstable_files) == 1

    def test_categories_defaults_to_empty_dict(self) -> None:
        result = HarvestResult(projects_analyzed=1, total_learnings=0, total_rules=0)
        assert result.categories == {}
        assert isinstance(result.categories, dict)

    def test_stacks_defaults_to_empty_dict(self) -> None:
        result = HarvestResult(projects_analyzed=1, total_learnings=0, total_rules=0)
        assert result.stacks == {}
        assert isinstance(result.stacks, dict)

    def test_unstable_files_defaults_to_empty_list(self) -> None:
        result = HarvestResult(projects_analyzed=1, total_learnings=0, total_rules=0)
        assert result.unstable_files == []
        assert isinstance(result.unstable_files, list)

    def test_high_confidence_rules_defaults_to_zero(self) -> None:
        result = HarvestResult(projects_analyzed=1, total_learnings=0, total_rules=0)
        assert result.high_confidence_rules == 0

    def test_empty_factory_method(self) -> None:
        result = HarvestResult.empty()
        assert result.projects_analyzed == 0
        assert result.total_learnings == 0
        assert result.total_rules == 0
        assert result.categories == {}
        assert result.stacks == {}
        assert result.high_confidence_rules == 0
        assert result.unstable_files == []

    def test_empty_factory_returns_harvest_result(self) -> None:
        result = HarvestResult.empty()
        assert isinstance(result, HarvestResult)

    def test_default_dicts_are_independent_instances(self) -> None:
        """Ensure mutable defaults are not shared between instances."""
        r1 = HarvestResult(projects_analyzed=0, total_learnings=0, total_rules=0)
        r2 = HarvestResult(projects_analyzed=0, total_learnings=0, total_rules=0)
        r1.categories["python"] = 1
        assert "python" not in r2.categories

    def test_default_lists_are_independent_instances(self) -> None:
        """Ensure mutable defaults are not shared between instances."""
        r1 = HarvestResult(projects_analyzed=0, total_learnings=0, total_rules=0)
        r2 = HarvestResult(projects_analyzed=0, total_learnings=0, total_rules=0)
        r1.unstable_files.append(FileChurn("x.py"))
        assert len(r2.unstable_files) == 0

    def test_equality(self) -> None:
        r1 = HarvestResult(1, 5, 3, {"pattern": 3}, {"python": 3}, 1, [])
        r2 = HarvestResult(1, 5, 3, {"pattern": 3}, {"python": 3}, 1, [])
        assert r1 == r2

    def test_repr_contains_class_name(self) -> None:
        result = HarvestResult.empty()
        assert "HarvestResult" in repr(result)

    def test_all_fields_are_correct_types(self) -> None:
        result = HarvestResult(
            projects_analyzed=2,
            total_learnings=10,
            total_rules=5,
            categories={"pattern": 5},
            stacks={"python": 5},
            high_confidence_rules=2,
            unstable_files=[FileChurn("a.py")],
        )
        assert isinstance(result.projects_analyzed, int)
        assert isinstance(result.total_learnings, int)
        assert isinstance(result.total_rules, int)
        assert isinstance(result.categories, dict)
        assert isinstance(result.stacks, dict)
        assert isinstance(result.high_confidence_rules, int)
        assert isinstance(result.unstable_files, list)
