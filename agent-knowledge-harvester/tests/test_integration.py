"""End-to-end integration tests for the agent-harvest pipeline.

Covers:
- Full single-project pipeline (LEARNINGS.md + CLARITY_LOG.md + progress.txt + git)
- Gallery mode with 2 projects sharing common learnings
- Cross-project confidence escalation to "medium"
- All output file validity (YAML parses, JSON parses, markdown has expected structure)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from agent_harvest.cli import main


# ─── Learning entry tuples: (title, context, discovery, rule) ─────────────────

# 3 entries for single-project tests — no higher-priority keywords so category is stable
_SINGLE_LEARNINGS: list[tuple[str, str, str, str]] = [
    (
        "Use pytest fixtures for test isolation",
        "organizing test suites",
        "pytest fixtures allow clean test isolation without teardown boilerplate",
        "Use pytest fixtures for clean test isolation",
    ),
    (
        "dataclass field defaults must use field() for mutable types",
        "defining data models with list and dict fields",
        "Using list or dict directly as default causes shared mutable state",
        "Use field default_factory list for mutable defaults in dataclasses",
    ),
    (
        "uv run preserves virtual environment isolation",
        "running tools via uv during CI setup",
        "uv run automatically uses the project venv without explicit activation",
        "Always prefix Python tool invocations with uv run in harness scripts",
    ),
]

# Alpha cross-project learning: "Use pytest fixtures for test isolation"
_ALPHA_LEARNINGS: list[tuple[str, str, str, str]] = [
    (
        "Use pytest fixtures for test isolation",
        "organizing test suites in alpha project",
        "pytest fixtures allow clean test isolation without teardown boilerplate",
        "Use pytest fixtures for clean test isolation",
    ),
    (
        "parse YAML safely with safe_load",
        "loading configuration files",
        "yaml full_load can execute arbitrary Python objects so safe_load is required",
        "Always use yaml safe_load for untrusted YAML input",
    ),
]

# Beta cross-project learning: overlapping title with Jaccard >= 0.4 vs Alpha's
_BETA_LEARNINGS: list[tuple[str, str, str, str]] = [
    (
        "pytest fixtures for test isolation and reuse",
        "test suite organization in beta project",
        "pytest fixtures enable test isolation and reuse across test modules",
        "pytest fixtures for test isolation and reuse",
    ),
    (
        "ruff F401 flags unused imports in test files",
        "writing test files",
        "Imported pytest by reflex even when no pytest symbols were used",
        "Only import pytest explicitly when using pytest-specific features",
    ),
]


# ─── Git helpers ──────────────────────────────────────────────────────────────


def _git(project_dir: Path, *args: str) -> None:
    """Run a git command in project_dir."""
    subprocess.run(
        ["git", *args],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )


def _init_git_repo(project_dir: Path) -> None:
    """Initialize a git repo with 11 commits including fix: messages and high-churn file."""
    _git(project_dir, "init")
    _git(project_dir, "config", "user.email", "test@example.com")
    _git(project_dir, "config", "user.name", "Test Author")

    # C1: add main.py
    (project_dir / "main.py").write_text("# v1\n", encoding="utf-8")
    _git(project_dir, "add", "main.py")
    _git(project_dir, "commit", "-m", "feat: initial main module")

    # C2–C6: modify main.py 5 more times (modify_count = 5 → unstable)
    for i in range(2, 7):
        (project_dir / "main.py").write_text(f"# v{i}\n", encoding="utf-8")
        _git(project_dir, "add", "main.py")
        _git(project_dir, "commit", "-m", f"feat: update main to version {i}")

    # C7: add utils.py
    (project_dir / "utils.py").write_text("# utils\n", encoding="utf-8")
    _git(project_dir, "add", "utils.py")
    _git(project_dir, "commit", "-m", "feat: add utilities module")

    # C8: fix commit → produces LearningEntry with category=error-recovery
    (project_dir / "utils.py").write_text("# utils fixed\n", encoding="utf-8")
    _git(project_dir, "add", "utils.py")
    _git(project_dir, "commit", "-m", "fix: handle missing file error in utils")

    # C9: add temp.py
    (project_dir / "temp.py").write_text("# temp\n", encoding="utf-8")
    _git(project_dir, "add", "temp.py")
    _git(project_dir, "commit", "-m", "feat: add temporary helper")

    # C10: delete temp.py
    _git(project_dir, "rm", "temp.py")
    _git(project_dir, "commit", "-m", "chore: remove temporary helper")

    # C11: another fix commit
    (project_dir / "main.py").write_text("# main final\n", encoding="utf-8")
    _git(project_dir, "add", "main.py")
    _git(project_dir, "commit", "-m", "fix: correct initialization order in main")


# ─── Project file helpers ──────────────────────────────────────────────────────


def _make_learnings(path: Path, entries: list[tuple[str, str, str, str]]) -> None:
    """Write LEARNINGS.md with (title, context, discovery, rule) entries."""
    lines = ["# LEARNINGS\n"]
    for title, ctx, disc, rule in entries:
        lines += [
            f"\n### Learning: {title}\n",
            f"- Context: {ctx}\n",
            f"- Discovery: {disc}\n",
            f"- Rule: {rule}\n",
        ]
    path.write_text("".join(lines), encoding="utf-8")


def _make_clarity_log(path: Path) -> None:
    """Write a realistic CLARITY_LOG.md with 5 ambiguity blocks across 2 rounds."""
    path.write_text(
        """\
# CLARITY_LOG

## Round 1

```
Round: 1
Spec: agent.md
Category: UNDEFINED_TERM
Severity: CRITICAL
Q: What format does LEARNINGS.md follow?
A: H3 headers with Context, Discovery, Rule sub-bullets.
Resolution: Parse on ### Learning: headers and extract sub-bullet fields.
---
```

```
Round: 1
Spec: agent.md
Category: AMBIGUOUS_ACCEPTANCE_CRITERIA
Severity: MAJOR
Q: How is confidence computed for cross-project matching?
A: Confidence is based on unique source project count: 1=low, 2=medium, 3+=high.
Resolution: Count unique source_projects in merged rule group.
---
```

```
Round: 1
Spec: agent.md
Category: INTEGRATION_GAP
Severity: MAJOR
Q: How to track file operation types from git history?
A: Use git log --name-status for A/M/D codes and --numstat for line counts.
Resolution: Run both git commands and combine per-file results.
---
```

## Round 2

```
Round: 2
Spec: agent.md
Category: EDGE_CASE
Severity: MINOR
Q: What output does --dry-run produce?
A: Print HarvestResult summary to stdout without writing any files.
Resolution: Print summary then return without calling any write_ functions.
---
```

```
Round: 2
Spec: agent.md
Category: UNDEFINED_TERM
Severity: MINOR
Q: Does --stack filter projects or individual rules?
A: Filtering happens at rule output time after full synthesis.
Resolution: Pass stack argument to write_rules; all projects still analyzed.
---
```
""",
        encoding="utf-8",
    )


def _make_progress(path: Path) -> None:
    """Write progress.txt with 3 sessions, 2 of which have Discovered fields."""
    path.write_text(
        """\
=== Harness initialized: 2026-01-01T00:00:00Z ===
Project type: python-uv

=== Session 2026-01-01T01:00:00Z ===
Completed: Item 1 - Data models
Changes: Created models.py with core dataclasses.
Why: Foundation for subsequent items — all parsers depend on these types.
Discovered: Python datetime.fromisoformat() does not support timezone-aware strings before 3.11. Use strptime fallback for older Python versions.
Difficulty: S as estimated.

=== Session 2026-01-01T02:00:00Z ===
Completed: Item 2 - HTML parser
Changes: Implemented parse_post_html() using BeautifulSoup4.
Why: BeautifulSoup handles malformed HTML better than stdlib html.parser.
Difficulty: M as estimated.

=== Session 2026-01-01T03:00:00Z ===
Completed: Item 3 - Markdown writer
Changes: Created write_markdown() with YAML front-matter output.
Why: YAML front-matter required by downstream tools.
Discovered: pyyaml safe_dump strips trailing newlines from multi-line strings. Append newline before calling safe_dump to preserve them.
Difficulty: S as estimated.
""",
        encoding="utf-8",
    )


def _make_project(
    parent: Path,
    name: str,
    learnings: list[tuple[str, str, str, str]],
    *,
    with_git: bool = False,
) -> Path:
    """Create a project directory with pyproject.toml, LEARNINGS.md, CLARITY_LOG.md,
    progress.txt, and optionally a git repo."""
    p = parent / name
    p.mkdir()
    (p / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    _make_learnings(p / "LEARNINGS.md", learnings)
    _make_clarity_log(p / "CLARITY_LOG.md")
    _make_progress(p / "progress.txt")
    if with_git:
        _init_git_repo(p)
    return p


# ─── Single-project pipeline tests ───────────────────────────────────────────


class TestSingleProjectPipeline:
    """Full single-project pipeline end-to-end tests."""

    def test_all_output_files_created(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Running agent-harvest on a project produces all expected output files."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS, with_git=True)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        assert (output / "rules").is_dir()
        assert len(list((output / "rules").glob("*.yaml"))) > 0
        assert (output / "instability-report.md").is_file()
        assert (output / "spec-guide.md").is_file()
        assert (output / "summary.json").is_file()

    def test_yaml_rules_are_valid_and_round_trip_safe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """All YAML rule files are valid and survive a safe_load → safe_dump round trip."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        for yaml_file in (output / "rules").glob("*.yaml"):
            text = yaml_file.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            assert isinstance(data, dict), f"{yaml_file.name} did not parse to a dict"
            for field in ("id", "rule", "category", "confidence", "stacks", "source_projects"):
                assert field in data, f"field '{field}' missing from {yaml_file.name}"
            # Round-trip safety
            re_dumped = yaml.safe_dump(data, allow_unicode=True)
            assert yaml.safe_load(re_dumped) == data

    def test_summary_json_has_correct_fields_and_counts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """summary.json is valid JSON with all HarvestResult fields and sensible counts."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        for field in (
            "projects_analyzed",
            "total_learnings",
            "total_rules",
            "high_confidence_rules",
            "categories",
            "stacks",
            "unstable_files",
        ):
            assert field in data, f"field '{field}' missing from summary.json"

        assert data["projects_analyzed"] == 1
        assert data["total_learnings"] > 0
        assert data["total_rules"] > 0

    def test_total_learnings_combines_all_sources(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """total_learnings in summary reflects LEARNINGS.md entries + progress.txt Discovered."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        # 3 LEARNINGS.md entries + 2 progress.txt Discovered = minimum 5
        assert data["total_learnings"] >= 5

    def test_instability_report_has_header(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """instability-report.md starts with the expected markdown header."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS, with_git=True)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        content = (output / "instability-report.md").read_text(encoding="utf-8")
        assert "# Instability Report" in content

    def test_instability_report_contains_unstable_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main.py (modified 5+ times) appears in the instability report."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS, with_git=True)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        content = (output / "instability-report.md").read_text(encoding="utf-8")
        assert "main.py" in content

    def test_spec_guide_has_guidelines(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """spec-guide.md contains the expected header and at least one guideline entry."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(project), "--output", str(output)])

        main()

        content = (output / "spec-guide.md").read_text(encoding="utf-8")
        assert "# Spec Guide" in content
        # Each resolution entry should produce at least one "- " bullet
        assert "- " in content

    def test_dry_run_no_files_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--dry-run prints a summary to stdout but writes no output files."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv",
            ["agent-harvest", str(project), "--output", str(output), "--dry-run"],
        )

        main()

        assert not output.exists(), "output directory should not be created in dry-run mode"
        captured = capsys.readouterr()
        assert "Total learnings:" in captured.out
        assert "Total rules:" in captured.out

    def test_format_json_produces_json_rule_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--format json writes .json files that are valid JSON with expected fields."""
        project = _make_project(tmp_path, "myproject", _SINGLE_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv",
            ["agent-harvest", str(project), "--output", str(output), "--format", "json"],
        )

        main()

        json_files = list((output / "rules").glob("*.json"))
        assert len(json_files) > 0
        for jf in json_files:
            data = json.loads(jf.read_text(encoding="utf-8"))
            assert "rule" in data
            assert "confidence" in data

    def test_missing_learnings_md_skips_gracefully(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Project with no LEARNINGS.md still produces output from progress.txt entries."""
        p = tmp_path / "nolarnings"
        p.mkdir()
        (p / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        _make_progress(p / "progress.txt")
        _make_clarity_log(p / "CLARITY_LOG.md")
        output = tmp_path / "out"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(p), "--output", str(output)])

        main()

        assert (output / "summary.json").is_file()
        data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        # 2 Discovered entries in progress.txt
        assert data["total_learnings"] >= 2


# ─── Gallery pipeline tests ───────────────────────────────────────────────────


class TestGalleryPipeline:
    """Gallery mode integration tests with multiple projects."""

    def _make_gallery(self, tmp_path: Path) -> Path:
        """Create a gallery directory with alpha and beta project subdirs."""
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        _make_project(gallery, "alpha", _ALPHA_LEARNINGS)
        _make_project(gallery, "beta", _BETA_LEARNINGS)
        return gallery

    def test_gallery_discovers_both_projects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gallery mode analyzes both project subdirectories."""
        gallery = self._make_gallery(tmp_path)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", "--gallery", str(gallery), "--output", str(output)]
        )

        main()

        data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        assert data["projects_analyzed"] == 2

    def test_gallery_all_output_files_created(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Gallery mode produces all expected output files."""
        gallery = self._make_gallery(tmp_path)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", "--gallery", str(gallery), "--output", str(output)]
        )

        main()

        assert (output / "instability-report.md").is_file()
        assert (output / "spec-guide.md").is_file()
        assert (output / "summary.json").is_file()
        assert (output / "rules").is_dir()

    def test_gallery_total_learnings_spans_both_projects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """total_learnings in summary aggregates across both projects."""
        gallery = self._make_gallery(tmp_path)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", "--gallery", str(gallery), "--output", str(output)]
        )

        main()

        data = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        # 2 LEARNINGS.md entries per project (4 total) + 2 progress Discovered per project (4)
        assert data["total_learnings"] >= 8

    def test_gallery_spec_guide_from_both_projects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """spec-guide.md is produced from combined CLARITY_LOG entries."""
        gallery = self._make_gallery(tmp_path)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", "--gallery", str(gallery), "--output", str(output)]
        )

        main()

        content = (output / "spec-guide.md").read_text(encoding="utf-8")
        assert "# Spec Guide" in content

    def test_gallery_missing_dir_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--gallery with a non-existent directory exits with code 1."""
        monkeypatch.setattr(
            sys, "argv",
            ["agent-harvest", "--gallery", str(tmp_path / "nonexistent")],
        )

        with pytest.raises(SystemExit) as exc:
            main()

        assert exc.value.code == 1


# ─── Cross-project confidence tests ───────────────────────────────────────────


class TestCrossProjectConfidence:
    """Targeted tests verifying cross-project Jaccard matching and confidence escalation."""

    def _run_gallery(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Set up a 2-project gallery and run main(), returning the output dir."""
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        _make_project(gallery, "alpha", _ALPHA_LEARNINGS)
        _make_project(gallery, "beta", _BETA_LEARNINGS)
        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", "--gallery", str(gallery), "--output", str(output)]
        )
        main()
        return output

    def test_matching_rules_merged_to_medium_confidence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two projects with overlapping pytest-fixture learnings produce a medium-confidence rule."""
        output = self._run_gallery(tmp_path, monkeypatch)

        yaml_files = list((output / "rules").glob("*.yaml"))
        assert yaml_files, "No YAML rule files were written"

        confidences = [
            yaml.safe_load(f.read_text(encoding="utf-8"))["confidence"]
            for f in yaml_files
        ]
        assert "medium" in confidences, (
            f"Expected at least one 'medium' confidence rule; got: {confidences}"
        )

    def test_merged_rule_lists_both_source_projects(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The merged medium-confidence rule lists both 'alpha' and 'beta' as source projects."""
        output = self._run_gallery(tmp_path, monkeypatch)

        medium_rules = [
            yaml.safe_load(f.read_text(encoding="utf-8"))
            for f in (output / "rules").glob("*.yaml")
            if yaml.safe_load(f.read_text(encoding="utf-8"))["confidence"] == "medium"
        ]
        assert medium_rules, "No medium-confidence rule found"
        rule = medium_rules[0]
        assert "alpha" in rule["source_projects"], "alpha not in source_projects"
        assert "beta" in rule["source_projects"], "beta not in source_projects"

    def test_skills_file_created_for_medium_confidence_rules(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """write_skills produces a python-common.md because the merged rule has medium confidence."""
        output = self._run_gallery(tmp_path, monkeypatch)

        skills_dir = output / "skills"
        assert skills_dir.is_dir(), "skills/ directory was not created"
        skill_files = list(skills_dir.glob("*.md"))
        assert skill_files, "No skill markdown files were written"

        # At least one file should mention the python stack
        content_combined = "".join(f.read_text(encoding="utf-8") for f in skill_files)
        assert "pytest" in content_combined.lower() or "isolation" in content_combined.lower()

    def test_non_matching_rules_remain_low_confidence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Learnings unique to one project (no cross-project match) stay at low confidence."""
        output = self._run_gallery(tmp_path, monkeypatch)

        yaml_files = list((output / "rules").glob("*.yaml"))
        low_rules = [
            yaml.safe_load(f.read_text(encoding="utf-8"))
            for f in yaml_files
            if yaml.safe_load(f.read_text(encoding="utf-8"))["confidence"] == "low"
        ]
        # The unique learnings from each project (safe_load, ruff, fromisoformat, safe_dump)
        # should remain low confidence since they don't match across projects
        assert low_rules, "Expected at least one low-confidence rule (unique to one project)"


# ─── Gallery instability report path namespacing tests ───────────────────────


class TestGalleryInstabilityPaths:
    """Gallery mode must prefix FileChurn paths with project name in instability-report.md."""

    def test_gallery_instability_report_prefixes_paths_with_project_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """In gallery mode, instability-report.md paths include the project name prefix."""
        gallery = tmp_path / "gallery"
        gallery.mkdir()

        # Create a project with a git repo so analyze_git returns FileChurn objects
        project = _make_project(gallery, "proj1", _SINGLE_LEARNINGS, with_git=True)
        (project / "pyproject.toml").write_text("[project]\nname='proj1'\n", encoding="utf-8")

        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output)],
        )
        main()

        report = (output / "instability-report.md").read_text(encoding="utf-8")
        # main.py had 6 commits (add + 5 modifies) → appears in report
        # In gallery mode, path must be "proj1/main.py", not bare "main.py"
        assert "proj1/main.py" in report
        # The bare path must NOT appear as a table cell entry
        assert "| main.py " not in report

    def test_gallery_two_projects_same_filename_distinguished(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two projects with the same filename (main.py) are distinguished by project prefix."""
        gallery = tmp_path / "gallery"
        gallery.mkdir()

        # Both projects have a git repo with main.py commits
        for proj_name in ("proj-a", "proj-b"):
            p = _make_project(gallery, proj_name, _SINGLE_LEARNINGS, with_git=True)
            (p / "pyproject.toml").write_text(f"[project]\nname='{proj_name}'\n", encoding="utf-8")

        output = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output)],
        )
        main()

        report = (output / "instability-report.md").read_text(encoding="utf-8")
        # Both prefixed paths must appear; bare "main.py" must not appear as its own cell
        assert "proj-a/main.py" in report
        assert "proj-b/main.py" in report
        assert "| main.py " not in report
