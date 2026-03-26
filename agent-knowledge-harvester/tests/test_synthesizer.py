"""Tests for synthesizer.synthesize_single, _select_unstable_files, and synthesize_cross."""

from __future__ import annotations

from agent_harvest.models import ClarityEntry, FileChurn, HarvestResult, HarvestRule, LearningEntry
from agent_harvest.synthesizer import (
    _jaccard,
    _rules_match,
    _select_unstable_files,
    _tokenize,
    synthesize_cross,
    synthesize_single,
)
from agent_harvest.utils import slugify


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_learning(
    description: str = "Use pytest fixtures for setup",
    category: str = "testing",
    stacks: list[str] | None = None,
    context: str = "",
    source_project: str = "proj",
    source_file: str = "LEARNINGS.md",
) -> LearningEntry:
    return LearningEntry(
        id=slugify(description),
        category=category,
        description=description,
        context=context,
        applicable_stacks=stacks if stacks is not None else ["python"],
        source_project=source_project,
        source_file=source_file,
    )


def make_churn(
    path: str = "src/main.py",
    modify_count: int = 0,
    revert_count: int = 0,
    add_count: int = 1,
    delete_count: int = 0,
    net_changes: int = 0,
) -> FileChurn:
    return FileChurn(
        path=path,
        add_count=add_count,
        modify_count=modify_count,
        delete_count=delete_count,
        revert_count=revert_count,
        net_changes=net_changes,
    )


# ---------------------------------------------------------------------------
# Empty inputs
# ---------------------------------------------------------------------------


def test_empty_learnings_produces_empty_rules() -> None:
    rules, _ = synthesize_single([], [], [], "proj")
    assert rules == []


def test_empty_learnings_produces_zero_counts() -> None:
    _, result = synthesize_single([], [], [], "proj")
    assert result.total_learnings == 0
    assert result.total_rules == 0


def test_empty_learnings_produces_empty_distributions() -> None:
    _, result = synthesize_single([], [], [], "proj")
    assert result.categories == {}
    assert result.stacks == {}


def test_empty_learnings_projects_analyzed_is_one() -> None:
    _, result = synthesize_single([], [], [], "proj")
    assert result.projects_analyzed == 1


def test_empty_learnings_high_confidence_is_zero() -> None:
    _, result = synthesize_single([], [], [], "proj")
    assert result.high_confidence_rules == 0


def test_empty_learnings_unstable_files_is_empty() -> None:
    _, result = synthesize_single([], [], [], "proj")
    assert result.unstable_files == []


def test_empty_file_churns_produces_empty_unstable() -> None:
    entry = make_learning()
    _, result = synthesize_single([entry], [], [], "proj")
    assert result.unstable_files == []


# ---------------------------------------------------------------------------
# 1:1 mapping
# ---------------------------------------------------------------------------


def test_single_learning_produces_single_rule() -> None:
    rules, _ = synthesize_single([make_learning()], [], [], "proj")
    assert len(rules) == 1


def test_five_learnings_produce_five_rules() -> None:
    entries = [make_learning(description=f"Rule number {i}") for i in range(5)]
    rules, result = synthesize_single(entries, [], [], "proj")
    assert len(rules) == 5
    assert result.total_learnings == 5
    assert result.total_rules == 5


def test_rule_id_is_slugified_description() -> None:
    entry = make_learning(description="Use ruff for linting!")
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].id == "use-ruff-for-linting"


def test_rule_category_matches_learning() -> None:
    entry = make_learning(category="error-recovery")
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].category == "error-recovery"


def test_rule_text_matches_description() -> None:
    entry = make_learning(description="Always validate input at boundary")
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].rule == "Always validate input at boundary"


def test_rule_confidence_is_always_low() -> None:
    entries = [make_learning(description=f"Rule {i}") for i in range(3)]
    rules, _ = synthesize_single(entries, [], [], "proj")
    for rule in rules:
        assert rule.confidence == "low"


def test_rule_source_projects_contains_project_name() -> None:
    entry = make_learning()
    rules, _ = synthesize_single([entry], [], [], "my-project")
    assert rules[0].source_projects == ["my-project"]


def test_rule_stacks_match_applicable_stacks() -> None:
    entry = make_learning(stacks=["python", "nodejs"])
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].stacks == ["python", "nodejs"]


def test_rule_applicable_to_is_stacks_joined() -> None:
    entry = make_learning(stacks=["python", "java"])
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].applicable_to == "python, java"


def test_rule_applicable_to_is_all_when_no_stacks() -> None:
    entry = make_learning(stacks=[])
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].applicable_to == "all"


def test_rule_applicable_to_single_stack() -> None:
    entry = make_learning(stacks=["rust"])
    rules, _ = synthesize_single([entry], [], [], "proj")
    assert rules[0].applicable_to == "rust"


# ---------------------------------------------------------------------------
# Unique IDs for duplicate descriptions
# ---------------------------------------------------------------------------


def test_duplicate_descriptions_produce_unique_ids() -> None:
    entries = [make_learning(description="same description") for _ in range(3)]
    rules, _ = synthesize_single(entries, [], [], "proj")
    ids = [r.id for r in rules]
    assert len(set(ids)) == 3
    assert ids[0] == "same-description"
    assert ids[1] == "same-description-2"
    assert ids[2] == "same-description-3"


def test_all_rule_ids_are_unique() -> None:
    entries = [make_learning(description=f"Distinct rule text {i}") for i in range(10)]
    rules, _ = synthesize_single(entries, [], [], "proj")
    ids = [r.id for r in rules]
    assert len(set(ids)) == 10


# ---------------------------------------------------------------------------
# HarvestResult summary
# ---------------------------------------------------------------------------


def test_harvest_result_projects_analyzed_is_one() -> None:
    _, result = synthesize_single([make_learning()], [], [], "proj")
    assert result.projects_analyzed == 1


def test_harvest_result_high_confidence_is_zero_for_multiple_rules() -> None:
    entries = [make_learning(description=f"Rule {i}") for i in range(5)]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.high_confidence_rules == 0


def test_category_distribution_single_category() -> None:
    entries = [make_learning(description=f"R{i}", category="testing") for i in range(3)]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.categories == {"testing": 3}


def test_category_distribution_multiple_categories() -> None:
    entries = [
        make_learning(description="A", category="testing"),
        make_learning(description="B", category="testing"),
        make_learning(description="C", category="error-recovery"),
    ]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.categories == {"testing": 2, "error-recovery": 1}


def test_stack_distribution_single_stack() -> None:
    entries = [make_learning(description=f"R{i}", stacks=["python"]) for i in range(3)]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.stacks == {"python": 3}


def test_stack_distribution_multiple_stacks() -> None:
    entries = [
        make_learning(description="A", stacks=["python"]),
        make_learning(description="B", stacks=["python", "nodejs"]),
        make_learning(description="C", stacks=["nodejs"]),
    ]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.stacks == {"python": 2, "nodejs": 2}


def test_stack_distribution_empty_stacks_not_counted() -> None:
    entries = [make_learning(description=f"R{i}", stacks=[]) for i in range(3)]
    _, result = synthesize_single(entries, [], [], "proj")
    assert result.stacks == {}


def test_clarity_entries_accepted_and_ignored() -> None:
    entries = [make_learning()]
    clarities = [ClarityEntry(round=1, question="Q", answer="A", decision="D")]
    rules, result = synthesize_single(entries, clarities, [], "proj")
    assert len(rules) == 1
    assert result.total_rules == 1


# ---------------------------------------------------------------------------
# _select_unstable_files — unit tests
# ---------------------------------------------------------------------------


def test_empty_churns_returns_empty() -> None:
    assert _select_unstable_files([]) == []


def test_revert_count_triggers_unstable() -> None:
    churns = [make_churn(path="a.py", revert_count=1, modify_count=0)]
    assert any(f.path == "a.py" for f in _select_unstable_files(churns))


def test_modify_count_gte_5_triggers_unstable() -> None:
    churns = [make_churn(path="b.py", modify_count=5)]
    assert any(f.path == "b.py" for f in _select_unstable_files(churns))


def test_modify_count_exactly_5_is_included() -> None:
    churns = [make_churn(path="exact.py", modify_count=5)]
    assert any(f.path == "exact.py" for f in _select_unstable_files(churns))


def test_modify_count_4_no_revert_excluded_when_not_top_20() -> None:
    # 10 files: file0 has modify=4, rest have modify=0 — file0 is top 20% (1 of 10)
    churns = [make_churn(path="f0.py", modify_count=4)] + [
        make_churn(path=f"f{i}.py", modify_count=0) for i in range(1, 10)
    ]
    unstable_paths = {f.path for f in _select_unstable_files(churns)}
    # f0.py is top 20%, others are not (modify=0, no revert, not top 20%)
    assert "f0.py" in unstable_paths
    assert "f9.py" not in unstable_paths


def test_top_20_pct_of_10_files_is_2() -> None:
    churns = [make_churn(path=f"f{i}.py", modify_count=1) for i in range(10)]
    unstable = _select_unstable_files(churns)
    # top 20% of 10 = ceil(2.0) = 2; all modify=1, no revert, none >= 5
    assert len(unstable) == 2


def test_top_20_pct_of_5_files_is_1() -> None:
    churns = [
        make_churn(path="hot.py", modify_count=10),
        make_churn(path="a.py", modify_count=1),
        make_churn(path="b.py", modify_count=1),
        make_churn(path="c.py", modify_count=1),
        make_churn(path="d.py", modify_count=1),
    ]
    unstable = _select_unstable_files(churns)
    # top 20% of 5 = ceil(1.0) = 1 → hot.py only (no modify>=5, no revert)
    assert any(f.path == "hot.py" for f in unstable)


def test_top_20_pct_minimum_one_when_single_file() -> None:
    churns = [make_churn(path="only.py", modify_count=0)]
    unstable = _select_unstable_files(churns)
    assert len(unstable) == 1
    assert unstable[0].path == "only.py"


def test_stable_file_below_all_thresholds_excluded() -> None:
    churns = [
        make_churn(path="hot.py", modify_count=10),
        make_churn(path="stable.py", modify_count=0, revert_count=0),
        make_churn(path="also.py", modify_count=0, revert_count=0),
        make_churn(path="more.py", modify_count=0, revert_count=0),
        make_churn(path="extra.py", modify_count=0, revert_count=0),
    ]
    unstable_paths = {f.path for f in _select_unstable_files(churns)}
    assert "hot.py" in unstable_paths
    assert "stable.py" not in unstable_paths


def test_union_of_all_three_conditions() -> None:
    # a.py: top 20% by modify_count (highest)
    # b.py: revert_count > 0
    # c.py: modify_count >= 5
    # d.py: none of the above
    churns = [
        make_churn(path="a.py", modify_count=8),
        make_churn(path="b.py", modify_count=0, revert_count=2),
        make_churn(path="c.py", modify_count=7),
        make_churn(path="d.py", modify_count=1),
    ]
    # top 20% of 4 = ceil(0.8) = 1 → a.py (modify=8 is highest)
    unstable_paths = {f.path for f in _select_unstable_files(churns)}
    assert "a.py" in unstable_paths  # top 20%
    assert "b.py" in unstable_paths  # revert > 0
    assert "c.py" in unstable_paths  # modify >= 5
    assert "d.py" not in unstable_paths  # none of the conditions


def test_result_unstable_files_populated_from_churns() -> None:
    churns = [make_churn(path="hot.py", revert_count=1)]
    _, result = synthesize_single([make_learning()], [], churns, "proj")
    assert any(f.path == "hot.py" for f in result.unstable_files)


def test_revert_zero_modify_below_5_not_top20_excluded() -> None:
    # 5 files; first has modify=3 (top 20%=1 file), rest have modify=0
    churns = [
        make_churn(path="top.py", modify_count=3),
        make_churn(path="x1.py", modify_count=0),
        make_churn(path="x2.py", modify_count=0),
        make_churn(path="x3.py", modify_count=0),
        make_churn(path="x4.py", modify_count=0),
    ]
    unstable_paths = {f.path for f in _select_unstable_files(churns)}
    assert "top.py" in unstable_paths
    assert "x1.py" not in unstable_paths
    assert "x4.py" not in unstable_paths


def test_multiple_conditions_on_same_file() -> None:
    # A file can satisfy multiple conditions at once — should appear once
    churns = [make_churn(path="multi.py", modify_count=10, revert_count=3)]
    unstable = _select_unstable_files(churns)
    assert len(unstable) == 1
    assert unstable[0].path == "multi.py"


# ---------------------------------------------------------------------------
# Helpers for synthesize_cross tests
# ---------------------------------------------------------------------------


def make_rule(
    rule_text: str = "use pytest fixtures for setup",
    category: str = "testing",
    stacks: list[str] | None = None,
    confidence: str = "low",
    source_projects: list[str] | None = None,
) -> HarvestRule:
    stacks = stacks if stacks is not None else ["python"]
    source_projects = source_projects if source_projects is not None else ["proj"]
    applicable_to = ", ".join(stacks) if stacks else "all"
    return HarvestRule(
        id=slugify(rule_text),
        category=category,
        stacks=stacks,
        confidence=confidence,
        source_projects=source_projects,
        rule=rule_text,
        applicable_to=applicable_to,
    )


def make_project_result(
    rules: list[HarvestRule],
    total_learnings: int = 0,
    unstable_files: list[FileChurn] | None = None,
) -> tuple[list[HarvestRule], HarvestResult]:
    result = HarvestResult(
        projects_analyzed=1,
        total_learnings=total_learnings,
        total_rules=len(rules),
        categories={},
        stacks={},
        high_confidence_rules=0,
        unstable_files=unstable_files or [],
    )
    return rules, result


# ---------------------------------------------------------------------------
# _tokenize unit tests
# ---------------------------------------------------------------------------


def test_tokenize_lowercases_and_splits() -> None:
    tokens = _tokenize("Pytest Fixtures")
    assert "pytest" in tokens
    assert "fixtures" in tokens


def test_tokenize_removes_stopwords() -> None:
    tokens = _tokenize("use pytest for testing")
    assert "for" not in tokens
    assert "pytest" in tokens


def test_tokenize_empty_string() -> None:
    assert _tokenize("") == frozenset()


def test_tokenize_all_stopwords() -> None:
    assert _tokenize("and the a in") == frozenset()


# ---------------------------------------------------------------------------
# _jaccard unit tests
# ---------------------------------------------------------------------------


def test_jaccard_identical_sets() -> None:
    s = frozenset({"pytest", "fixture"})
    assert _jaccard(s, s) == 1.0


def test_jaccard_disjoint_sets() -> None:
    a = frozenset({"pytest"})
    b = frozenset({"ruff"})
    assert _jaccard(a, b) == 0.0


def test_jaccard_both_empty_returns_one() -> None:
    assert _jaccard(frozenset(), frozenset()) == 1.0


def test_jaccard_exactly_0_4() -> None:
    # |∩|=2, |∪|=5 → 2/5 = 0.4
    a = frozenset({"alpha", "beta"})
    b = frozenset({"alpha", "beta", "gamma", "delta", "epsilon"})
    assert _jaccard(a, b) == 0.4


def test_jaccard_below_0_4() -> None:
    # |∩|=2, |∪|=6 → 2/6 ≈ 0.333
    a = frozenset({"alpha", "beta"})
    b = frozenset({"alpha", "beta", "gamma", "delta", "epsilon", "zeta"})
    assert abs(_jaccard(a, b) - (2 / 6)) < 1e-9


# ---------------------------------------------------------------------------
# _rules_match unit tests
# ---------------------------------------------------------------------------


def test_rules_match_identical_rules() -> None:
    r1 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj2"])
    assert _rules_match(r1, r2) is True


def test_rules_match_different_category_no_match() -> None:
    r1 = make_rule("pytest fixtures setup", category="testing", stacks=["python"])
    r2 = make_rule("pytest fixtures setup", category="error-recovery", stacks=["python"])
    assert _rules_match(r1, r2) is False


def test_rules_match_no_shared_stack_no_match() -> None:
    r1 = make_rule("use fixtures for setup", category="testing", stacks=["python"])
    r2 = make_rule("use fixtures for setup", category="testing", stacks=["java"])
    assert _rules_match(r1, r2) is False


def test_rules_match_empty_stacks_match_any() -> None:
    # Empty stacks = "all" → should match regardless of other rule's stacks
    r1 = make_rule("use fixtures for setup", category="testing", stacks=[])
    r2 = make_rule("use fixtures for setup", category="testing", stacks=["java"])
    assert _rules_match(r1, r2) is True


def test_rules_match_jaccard_at_threshold() -> None:
    # J = 2/5 = 0.4 → match
    r1 = make_rule("alpha beta", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("alpha beta gamma delta epsilon", category="testing", stacks=["python"], source_projects=["proj2"])
    assert _rules_match(r1, r2) is True


def test_rules_match_jaccard_below_threshold() -> None:
    # J = 2/6 ≈ 0.333 → no match
    r1 = make_rule("alpha beta", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("alpha beta gamma delta epsilon zeta", category="testing", stacks=["python"], source_projects=["proj2"])
    assert _rules_match(r1, r2) is False


# ---------------------------------------------------------------------------
# synthesize_cross — empty and single project
# ---------------------------------------------------------------------------


def test_cross_empty_returns_empty_rules() -> None:
    rules, _ = synthesize_cross([])
    assert rules == []


def test_cross_empty_returns_empty_result() -> None:
    _, result = synthesize_cross([])
    assert result == HarvestResult.empty()


def test_cross_single_project_different_categories_stay_separate() -> None:
    r1 = make_rule("pytest fixture setup", category="testing", source_projects=["proj1"])
    r2 = make_rule("handle missing file error", category="error-recovery", source_projects=["proj1"])
    rules, _ = synthesize_cross([make_project_result([r1, r2])])
    assert len(rules) == 2


def test_cross_single_project_all_rules_confidence_low() -> None:
    r1 = make_rule("pytest fixture setup", category="testing", source_projects=["proj1"])
    r2 = make_rule("handle missing file error", category="error-recovery", source_projects=["proj1"])
    rules, _ = synthesize_cross([make_project_result([r1, r2])])
    for rule in rules:
        assert rule.confidence == "low"


# ---------------------------------------------------------------------------
# synthesize_cross — matching and merging
# ---------------------------------------------------------------------------


def test_cross_two_matching_rules_merge_into_one() -> None:
    r1 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 1


def test_cross_merged_rule_confidence_medium_for_two_projects() -> None:
    r1 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert rules[0].confidence == "medium"


def test_cross_merged_rule_source_projects_contains_both() -> None:
    r1 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert set(rules[0].source_projects) == {"proj1", "proj2"}


def test_cross_three_matching_rules_confidence_high() -> None:
    # Three rules with high Jaccard, same category and stack, from 3 different projects
    r1 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup test", category="testing", stacks=["python"], source_projects=["proj2"])
    r3 = make_rule("use pytest fixtures setup test config", category="testing", stacks=["python"], source_projects=["proj3"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
        make_project_result([r3]),
    ])
    assert len(rules) == 1
    assert rules[0].confidence == "high"


def test_cross_non_matching_rules_stay_separate() -> None:
    # Different categories → no merge
    r1 = make_rule("handle error retry fallback", category="error-recovery", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("handle error retry fallback", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 2
    for rule in rules:
        assert rule.confidence == "low"


def test_cross_no_shared_stack_no_merge() -> None:
    r1 = make_rule("use fixtures for setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use fixtures for setup", category="testing", stacks=["java"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 2


def test_cross_jaccard_at_threshold_merges() -> None:
    # J = 2/5 = 0.4 → merge
    r1 = make_rule("alpha beta", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("alpha beta gamma delta epsilon", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 1


def test_cross_jaccard_below_threshold_no_merge() -> None:
    # J = 2/6 ≈ 0.333 → no merge
    r1 = make_rule("alpha beta", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("alpha beta gamma delta epsilon zeta", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 2


def test_cross_merged_rule_picks_longest_text() -> None:
    # Both rules share tokens "pytest fixtures setup" (3/5 and 3/7 overlap)
    # J = 3/5 = 0.6 → merge; longer text wins
    short_rule = make_rule("pytest fixtures setup mock", category="testing", stacks=["python"], source_projects=["proj1"])
    long_rule = make_rule("pytest fixtures setup mock timeout retry", category="testing", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([short_rule]),
        make_project_result([long_rule]),
    ])
    assert len(rules) == 1
    assert rules[0].rule == "pytest fixtures setup mock timeout retry"


def test_cross_merged_stacks_are_union() -> None:
    r1 = make_rule("use fixtures for setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r3 = make_rule("use fixtures for setup", category="testing", stacks=["python", "nodejs"], source_projects=["proj3"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r3]),
    ])
    assert len(rules) == 1
    assert set(rules[0].stacks) == {"python", "nodejs"}


def test_cross_rule_ids_are_unique() -> None:
    # Two non-matching rules with the same text slug should still get unique IDs
    r1 = make_rule("same description text", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("same description text", category="error-recovery", stacks=["python"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 2
    ids = [r.id for r in rules]
    assert len(set(ids)) == 2


def test_cross_empty_stacks_match_any_stack() -> None:
    r1 = make_rule("use pytest for setup", category="testing", stacks=[], source_projects=["proj1"])
    r2 = make_rule("use pytest for setup", category="testing", stacks=["java"], source_projects=["proj2"])
    rules, _ = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
    ])
    assert len(rules) == 1


# ---------------------------------------------------------------------------
# synthesize_cross — HarvestResult
# ---------------------------------------------------------------------------


def test_cross_harvest_result_projects_analyzed() -> None:
    r1 = make_rule("ruff linting python code", category="testing", source_projects=["proj1"])
    r2 = make_rule("handle missing file errors", category="error-recovery", source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1], total_learnings=3),
        make_project_result([r2], total_learnings=5),
    ])
    assert result.projects_analyzed == 2


def test_cross_harvest_result_total_learnings_is_sum() -> None:
    r1 = make_rule("ruff linting python code", category="testing", source_projects=["proj1"])
    r2 = make_rule("handle missing file errors", category="error-recovery", source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1], total_learnings=3),
        make_project_result([r2], total_learnings=5),
    ])
    assert result.total_learnings == 8


def test_cross_harvest_result_total_rules_is_merged_count() -> None:
    r1 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj2"])
    r3 = make_rule("handle missing error retry", category="error-recovery", stacks=["python"], source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2, r3]),
    ])
    # r1 and r2 merge → 1 rule; r3 stays → total 2 rules
    assert result.total_rules == 2


def test_cross_harvest_result_high_confidence_counted() -> None:
    r1 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for setup test", category="testing", stacks=["python"], source_projects=["proj2"])
    r3 = make_rule("use pytest fixtures setup test config", category="testing", stacks=["python"], source_projects=["proj3"])
    _, result = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2]),
        make_project_result([r3]),
    ])
    assert result.high_confidence_rules == 1


def test_cross_harvest_result_categories_from_merged_rules() -> None:
    r1 = make_rule("use pytest fixtures for setup", category="testing", stacks=["python"], source_projects=["proj1"])
    r2 = make_rule("use pytest fixtures for test setup", category="testing", stacks=["python"], source_projects=["proj2"])
    r3 = make_rule("handle missing error retry", category="error-recovery", stacks=["python"], source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1]),
        make_project_result([r2, r3]),
    ])
    # r1 and r2 merge → 1 testing; r3 stays → 1 error-recovery
    assert result.categories == {"testing": 1, "error-recovery": 1}


def test_cross_harvest_result_unstable_files_union() -> None:
    churn1 = make_churn(path="src/parser.py", modify_count=10)
    churn2 = make_churn(path="src/writer.py", revert_count=2)
    r1 = make_rule("fixture setup", category="testing", source_projects=["proj1"])
    r2 = make_rule("error handling", category="error-recovery", source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1], unstable_files=[churn1]),
        make_project_result([r2], unstable_files=[churn2]),
    ])
    paths = {f.path for f in result.unstable_files}
    assert paths == {"src/parser.py", "src/writer.py"}


def test_cross_harvest_result_unstable_files_deduped_by_path() -> None:
    churn = make_churn(path="shared.py", modify_count=10)
    r1 = make_rule("fixture setup", category="testing", source_projects=["proj1"])
    r2 = make_rule("error handling", category="error-recovery", source_projects=["proj2"])
    _, result = synthesize_cross([
        make_project_result([r1], unstable_files=[churn]),
        make_project_result([r2], unstable_files=[churn]),
    ])
    assert len(result.unstable_files) == 1
