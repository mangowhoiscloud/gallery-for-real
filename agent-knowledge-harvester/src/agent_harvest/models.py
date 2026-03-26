from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LearningEntry:
    id: str
    category: str
    description: str
    context: str
    applicable_stacks: list[str]
    source_project: str
    source_file: str


@dataclass
class ClarityEntry:
    round: int
    question: str
    answer: str
    decision: str


@dataclass
class FileChurn:
    path: str
    add_count: int = 0
    modify_count: int = 0
    delete_count: int = 0
    revert_count: int = 0
    net_changes: int = 0


@dataclass
class HarvestRule:
    id: str
    category: str
    stacks: list[str]
    confidence: str
    source_projects: list[str]
    rule: str
    applicable_to: str


@dataclass
class HarvestResult:
    projects_analyzed: int
    total_learnings: int
    total_rules: int
    categories: dict[str, int] = field(default_factory=dict)
    stacks: dict[str, int] = field(default_factory=dict)
    high_confidence_rules: int = 0
    unstable_files: list[FileChurn] = field(default_factory=list)

    @classmethod
    def empty(cls) -> HarvestResult:
        return cls(
            projects_analyzed=0,
            total_learnings=0,
            total_rules=0,
            categories={},
            stacks={},
            high_confidence_rules=0,
            unstable_files=[],
        )
