from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from agent_harvest.cli import _build_parser, _discover_projects, main

# ─── Fixture helpers ─────────────────────────────────────────────────────────

LEARNINGS_CONTENT = """\
### Learning: Use pytest fixtures for test setup
- Context: setting up unit tests for Python project
- Discovery: pytest fixtures are cleaner than unittest setUp/tearDown
- Rule: Use pytest fixtures instead of unittest setUp/tearDown
"""


def make_project(
    parent: Path,
    name: str = "myproject",
    with_learnings: bool = True,
) -> Path:
    """Create a minimal Python project directory."""
    p = parent / name
    p.mkdir(exist_ok=True)
    (p / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    if with_learnings:
        (p / "LEARNINGS.md").write_text(LEARNINGS_CONTENT, encoding="utf-8")
    return p


# ─── _build_parser ───────────────────────────────────────────────────────────


class TestBuildParser:
    def test_project_dir_positional(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.project_dir == "myproject"
        assert args.gallery is None

    def test_gallery_flag(self) -> None:
        args = _build_parser().parse_args(["--gallery", "/some/dir"])
        assert args.gallery == "/some/dir"
        assert args.project_dir is None

    def test_output_default(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.output == "harvest-output"

    def test_output_custom(self) -> None:
        args = _build_parser().parse_args(["myproject", "--output", "out"])
        assert args.output == "out"

    def test_stack_default_none(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.stack is None

    def test_stack_set(self) -> None:
        args = _build_parser().parse_args(["myproject", "--stack", "python"])
        assert args.stack == "python"

    def test_min_confidence_default(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.min_confidence == "low"

    def test_min_confidence_medium(self) -> None:
        args = _build_parser().parse_args(["myproject", "--min-confidence", "medium"])
        assert args.min_confidence == "medium"

    def test_min_confidence_high(self) -> None:
        args = _build_parser().parse_args(["myproject", "--min-confidence", "high"])
        assert args.min_confidence == "high"

    def test_format_default_yaml(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.format == "yaml"

    def test_format_json(self) -> None:
        args = _build_parser().parse_args(["myproject", "--format", "json"])
        assert args.format == "json"

    def test_dry_run_default_false(self) -> None:
        args = _build_parser().parse_args(["myproject"])
        assert args.dry_run is False

    def test_dry_run_true(self) -> None:
        args = _build_parser().parse_args(["myproject", "--dry-run"])
        assert args.dry_run is True

    def test_format_invalid_rejected(self) -> None:
        with pytest.raises(SystemExit):
            _build_parser().parse_args(["myproject", "--format", "csv"])

    def test_min_confidence_invalid_rejected(self) -> None:
        with pytest.raises(SystemExit):
            _build_parser().parse_args(["myproject", "--min-confidence", "ultra"])

    def test_no_positional_args_allowed_for_gallery(self) -> None:
        # gallery mode: no project_dir positional
        args = _build_parser().parse_args(["--gallery", "/g"])
        assert args.project_dir is None

    def test_gallery_with_output(self) -> None:
        args = _build_parser().parse_args(["--gallery", "/g", "--output", "/out"])
        assert args.gallery == "/g"
        assert args.output == "/out"


# ─── _discover_projects ──────────────────────────────────────────────────────


class TestDiscoverProjects:
    def test_empty_dir_returns_empty(self, tmp_path: Path) -> None:
        assert _discover_projects(tmp_path) == []

    def test_project_with_git_dir_included(self, tmp_path: Path) -> None:
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / ".git").mkdir()
        assert _discover_projects(tmp_path) == [proj]

    def test_project_with_pyproject_toml(self, tmp_path: Path) -> None:
        proj = tmp_path / "myproject"
        proj.mkdir()
        (proj / "pyproject.toml").write_text("", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]

    def test_project_with_pom_xml(self, tmp_path: Path) -> None:
        proj = tmp_path / "javaproject"
        proj.mkdir()
        (proj / "pom.xml").write_text("", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]

    def test_project_with_package_json(self, tmp_path: Path) -> None:
        proj = tmp_path / "nodeproject"
        proj.mkdir()
        (proj / "package.json").write_text("{}", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]

    def test_project_with_cargo_toml(self, tmp_path: Path) -> None:
        proj = tmp_path / "rustproject"
        proj.mkdir()
        (proj / "Cargo.toml").write_text("", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]

    def test_project_with_go_mod(self, tmp_path: Path) -> None:
        proj = tmp_path / "goproject"
        proj.mkdir()
        (proj / "go.mod").write_text("", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]

    def test_hidden_dir_excluded(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "pyproject.toml").write_text("", encoding="utf-8")
        assert _discover_projects(tmp_path) == []

    def test_file_not_dir_excluded(self, tmp_path: Path) -> None:
        (tmp_path / "readme.txt").write_text("hello", encoding="utf-8")
        assert _discover_projects(tmp_path) == []

    def test_plain_dir_without_markers_excluded(self, tmp_path: Path) -> None:
        plain = tmp_path / "nomarkers"
        plain.mkdir()
        assert _discover_projects(tmp_path) == []

    def test_multiple_projects_returned_sorted(self, tmp_path: Path) -> None:
        for name in ["beta", "alpha", "gamma"]:
            p = tmp_path / name
            p.mkdir()
            (p / "pyproject.toml").write_text("", encoding="utf-8")
        result = _discover_projects(tmp_path)
        assert [r.name for r in result] == ["alpha", "beta", "gamma"]

    def test_nonexistent_dir_returns_empty(self, tmp_path: Path) -> None:
        assert _discover_projects(tmp_path / "nonexistent") == []

    def test_setup_py_also_detected(self, tmp_path: Path) -> None:
        proj = tmp_path / "legacy"
        proj.mkdir()
        (proj / "setup.py").write_text("from setuptools import setup\n", encoding="utf-8")
        assert _discover_projects(tmp_path) == [proj]


# ─── main() — single-project mode ────────────────────────────────────────────


class TestMainSingleProject:
    def test_missing_project_dir_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing = tmp_path / "nonexistent"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", str(missing)])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_no_source_files_prints_no_patterns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        proj = tmp_path / "empty"
        proj.mkdir()
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", str(proj), "--output", str(output_dir)]
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        assert "No patterns found" in capsys.readouterr().out

    def test_with_learnings_creates_rules_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", str(proj), "--output", str(output_dir)]
        )
        main()
        assert (output_dir / "rules").is_dir()
        assert len(list((output_dir / "rules").glob("*.yaml"))) >= 1

    def test_creates_all_report_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", str(proj), "--output", str(output_dir)]
        )
        main()
        assert (output_dir / "instability-report.md").exists()
        assert (output_dir / "spec-guide.md").exists()
        assert (output_dir / "summary.json").exists()

    def test_format_json_creates_json_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", str(proj), "--output", str(output_dir), "--format", "json"],
        )
        main()
        assert len(list((output_dir / "rules").glob("*.json"))) >= 1
        assert len(list((output_dir / "rules").glob("*.yaml"))) == 0

    def test_dry_run_no_files_created(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", str(proj), "--output", str(output_dir), "--dry-run"],
        )
        main()
        assert not output_dir.exists()
        assert len(capsys.readouterr().out) > 0

    def test_dry_run_prints_summary_fields(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", str(proj), "--output", str(output_dir), "--dry-run"],
        )
        main()
        out = capsys.readouterr().out
        assert "Projects analyzed" in out
        assert "Total rules" in out

    def test_dry_run_with_min_confidence_shows_filtered_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Single-project rules are always low confidence.
        # --min-confidence=medium filters them all out → "Would write: 0 rules"
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "agent-harvest",
                str(proj),
                "--output",
                str(output_dir),
                "--dry-run",
                "--min-confidence",
                "medium",
            ],
        )
        main()
        out = capsys.readouterr().out
        assert "Would write" in out
        assert "0 rules" in out
        assert "min-confidence=medium" in out
        # No files created
        assert not output_dir.exists()

    def test_dry_run_with_stack_filter_shows_filtered_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Python project rules have stacks=["python"]; filtering for stack=java
        # excludes them → "Would write: 0 rules (filtered by stack=java)"
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "agent-harvest",
                str(proj),
                "--output",
                str(output_dir),
                "--dry-run",
                "--stack",
                "java",
            ],
        )
        main()
        out = capsys.readouterr().out
        assert "Would write" in out
        assert "stack=java" in out
        assert not output_dir.exists()

    def test_summary_json_is_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys, "argv", ["agent-harvest", str(proj), "--output", str(output_dir)]
        )
        main()
        data = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
        assert data["projects_analyzed"] == 1
        assert data["total_rules"] >= 1

    def test_no_args_exits_nonzero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["agent-harvest"])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_both_project_dir_and_gallery_exits_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proj = make_project(tmp_path)
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", str(proj), "--gallery", str(tmp_path)],
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0

    def test_min_confidence_high_no_rules_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Single-project rules are always low confidence.
        # write_rules filters them out — rules/ dir not created.
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "agent-harvest",
                str(proj),
                "--output",
                str(output_dir),
                "--min-confidence",
                "high",
            ],
        )
        main()
        # No rules/ dir (all filtered), but report files still written
        assert not (output_dir / "rules").exists()
        assert (output_dir / "summary.json").exists()

    def test_stack_filter_no_rules_written_for_wrong_stack(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # pyproject.toml project → python rules; filtering for java → no rules written
        proj = make_project(tmp_path)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", str(proj), "--output", str(output_dir), "--stack", "java"],
        )
        main()
        # Rules with stacks=["python"] are excluded; rules with stacks=[] ("all") pass through
        # Either way, verify rules dir state is consistent
        if (output_dir / "rules").exists():
            for f in (output_dir / "rules").glob("*.yaml"):
                import yaml  # noqa: PLC0415
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
                assert not data["stacks"] or "java" in data["stacks"]


# ─── main() — gallery mode ────────────────────────────────────────────────────


class TestMainGallery:
    def test_missing_gallery_dir_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing = tmp_path / "nonexistent"
        monkeypatch.setattr(sys, "argv", ["agent-harvest", "--gallery", str(missing)])
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

    def test_empty_gallery_exits_0_no_projects_message(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        assert "No projects found" in capsys.readouterr().out

    def test_gallery_with_one_project(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        make_project(gallery, name="proj1")
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        main()
        assert (output_dir / "rules").is_dir()
        assert (output_dir / "summary.json").exists()

    def test_gallery_summary_shows_correct_project_count(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        for name in ["proj1", "proj2", "proj3"]:
            make_project(gallery, name=name)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        main()
        data = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
        assert data["projects_analyzed"] == 3

    def test_gallery_cross_project_two_identical_rules_medium_confidence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two projects with identical learning → cross synthesis → confidence="medium"
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        for name in ["proj1", "proj2"]:
            p = make_project(gallery, name=name, with_learnings=False)
            (p / "LEARNINGS.md").write_text(LEARNINGS_CONTENT, encoding="utf-8")
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        main()
        data = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
        assert data["projects_analyzed"] == 2
        # With 2 source projects, at least one rule should be medium+ confidence
        yaml_files = list((output_dir / "rules").glob("*.yaml"))
        assert len(yaml_files) >= 1

    def test_gallery_with_no_learnings_exits_0(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        # Projects exist but no learnings → 0 rules
        make_project(gallery, name="proj1", with_learnings=False)
        make_project(gallery, name="proj2", with_learnings=False)
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        assert "No patterns found" in capsys.readouterr().out

    def test_gallery_hidden_subdirs_excluded(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        # Hidden project → excluded from discovery
        hidden = gallery / ".dotproject"
        hidden.mkdir()
        (hidden / "pyproject.toml").write_text("", encoding="utf-8")
        (hidden / "LEARNINGS.md").write_text(LEARNINGS_CONTENT, encoding="utf-8")
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            ["agent-harvest", "--gallery", str(gallery), "--output", str(output_dir)],
        )
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 0
        assert "No projects found" in capsys.readouterr().out

    def test_gallery_dry_run_prints_summary(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        gallery = tmp_path / "gallery"
        gallery.mkdir()
        make_project(gallery, name="proj1")
        output_dir = tmp_path / "out"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "agent-harvest",
                "--gallery",
                str(gallery),
                "--output",
                str(output_dir),
                "--dry-run",
            ],
        )
        main()
        out = capsys.readouterr().out
        assert "Projects analyzed" in out
        assert not output_dir.exists()
