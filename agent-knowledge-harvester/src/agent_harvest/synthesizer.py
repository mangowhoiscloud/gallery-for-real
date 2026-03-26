from __future__ import annotations

import math
import re

from .models import ClarityEntry, FileChurn, HarvestResult, HarvestRule, LearningEntry
from .utils import make_unique_id, slugify

_STOPWORDS = frozenset({
    "a", "an", "the", "in", "on", "at", "by", "of", "to", "for", "from",
    "with", "and", "but", "or", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "it", "its",
    "this", "that", "these", "those", "i", "we", "you", "they", "he", "she",
    "not", "as", "if", "all", "any", "also", "just", "each", "per",
})


def _tokenize(text: str) -> frozenset[str]:
    """Lowercase tokenize and filter stopwords."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return frozenset(t for t in tokens if t not in _STOPWORDS)


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Compute Jaccard similarity. Returns 1.0 if both sets are empty."""
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def _rules_match(r1: HarvestRule, r2: HarvestRule) -> bool:
    """Return True if two rules should be merged: same category, shared stack, Jaccard >= 0.4."""
    if r1.category != r2.category:
        return False
    # Empty stacks means "all" — treat as matching any stack set
    if r1.stacks and r2.stacks and not (set(r1.stacks) & set(r2.stacks)):
        return False
    t1 = _tokenize(r1.rule)
    t2 = _tokenize(r2.rule)
    return _jaccard(t1, t2) >= 0.4


def synthesize_single(
    learnings: list[LearningEntry],
    clarity_entries: list[ClarityEntry],
    file_churns: list[FileChurn],
    project_name: str,
) -> tuple[list[HarvestRule], HarvestResult]:
    """Map each LearningEntry 1:1 to a HarvestRule with confidence='low'.
    Build HarvestResult summary. Identify unstable files from file_churns."""
    rules: list[HarvestRule] = []
    existing_ids: set[str] = set()

    for entry in learnings:
        slug = slugify(entry.description)
        rule_id = make_unique_id(slug, existing_ids)
        existing_ids.add(rule_id)

        stacks = list(entry.applicable_stacks)
        applicable_to = ", ".join(stacks) if stacks else "all"

        rules.append(
            HarvestRule(
                id=rule_id,
                category=entry.category,
                stacks=stacks,
                confidence="low",
                source_projects=[project_name],
                rule=entry.description,
                applicable_to=applicable_to,
            )
        )

    categories: dict[str, int] = {}
    for rule in rules:
        categories[rule.category] = categories.get(rule.category, 0) + 1

    stacks_dist: dict[str, int] = {}
    for rule in rules:
        for stack in rule.stacks:
            stacks_dist[stack] = stacks_dist.get(stack, 0) + 1

    result = HarvestResult(
        projects_analyzed=1,
        total_learnings=len(learnings),
        total_rules=len(rules),
        categories=categories,
        stacks=stacks_dist,
        high_confidence_rules=0,
        unstable_files=_select_unstable_files(file_churns),
    )

    return rules, result


def synthesize_cross(
    project_results: list[tuple[list[HarvestRule], HarvestResult]],
) -> tuple[list[HarvestRule], HarvestResult]:
    """Merge rules across projects: same category + shared stack + Jaccard >= 0.4."""
    if not project_results:
        return [], HarvestResult.empty()

    all_rules: list[HarvestRule] = [rule for rules, _ in project_results for rule in rules]

    # Union-find grouping
    parent = list(range(len(all_rules)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(len(all_rules)):
        for j in range(i + 1, len(all_rules)):
            if _rules_match(all_rules[i], all_rules[j]):
                union(i, j)

    # Group by root
    groups: dict[int, list[int]] = {}
    for i in range(len(all_rules)):
        root = find(i)
        groups.setdefault(root, []).append(i)

    # Merge each group into a single rule
    merged_rules: list[HarvestRule] = []
    existing_ids: set[str] = set()

    for indices in groups.values():
        group_rules = [all_rules[i] for i in indices]
        best_rule = max(group_rules, key=lambda r: len(r.rule))

        # Deduplicate source projects (preserve insertion order)
        seen_proj: set[str] = set()
        source_projects: list[str] = []
        for r in group_rules:
            for p in r.source_projects:
                if p not in seen_proj:
                    source_projects.append(p)
                    seen_proj.add(p)

        n_sources = len(source_projects)
        confidence = "high" if n_sources >= 3 else "medium" if n_sources == 2 else "low"

        merged_stacks = sorted({s for r in group_rules for s in r.stacks})
        applicable_to = ", ".join(merged_stacks) if merged_stacks else "all"

        slug = slugify(best_rule.rule)
        rule_id = make_unique_id(slug, existing_ids)
        existing_ids.add(rule_id)

        merged_rules.append(
            HarvestRule(
                id=rule_id,
                category=best_rule.category,
                stacks=merged_stacks,
                confidence=confidence,
                source_projects=source_projects,
                rule=best_rule.rule,
                applicable_to=applicable_to,
            )
        )

    # Build HarvestResult
    categories: dict[str, int] = {}
    for rule in merged_rules:
        categories[rule.category] = categories.get(rule.category, 0) + 1

    stacks_dist: dict[str, int] = {}
    for rule in merged_rules:
        for stack in rule.stacks:
            stacks_dist[stack] = stacks_dist.get(stack, 0) + 1

    high_conf = sum(1 for r in merged_rules if r.confidence == "high")

    seen_paths: set[str] = set()
    unstable_files: list[FileChurn] = []
    for _, result in project_results:
        for fc in result.unstable_files:
            if fc.path not in seen_paths:
                unstable_files.append(fc)
                seen_paths.add(fc.path)

    return merged_rules, HarvestResult(
        projects_analyzed=len(project_results),
        total_learnings=sum(r.total_learnings for _, r in project_results),
        total_rules=len(merged_rules),
        categories=categories,
        stacks=stacks_dist,
        high_confidence_rules=high_conf,
        unstable_files=unstable_files,
    )


def _select_unstable_files(file_churns: list[FileChurn]) -> list[FileChurn]:
    """Return files that are: top 20% by modify_count, OR revert_count > 0, OR modify_count >= 5."""
    if not file_churns:
        return []

    sorted_desc = sorted(file_churns, key=lambda f: f.modify_count, reverse=True)
    top_count = max(1, math.ceil(len(file_churns) * 0.20))
    top_20_pct = {f.path for f in sorted_desc[:top_count]}

    seen: set[str] = set()
    unstable: list[FileChurn] = []
    for fc in file_churns:
        if fc.path in seen:
            continue
        if fc.path in top_20_pct or fc.revert_count > 0 or fc.modify_count >= 5:
            unstable.append(fc)
            seen.add(fc.path)

    return unstable
