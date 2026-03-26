from __future__ import annotations

import json
from pathlib import Path

from agent_harvest.stack import detect_project_stacks, extract_text_stacks


# ─── detect_project_stacks ────────────────────────────────────────────────────


def test_detect_python_from_pyproject_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    assert detect_project_stacks(tmp_path) == ["python"]


def test_detect_python_from_setup_py(tmp_path: Path) -> None:
    (tmp_path / "setup.py").write_text("from setuptools import setup\nsetup(name='x')\n")
    assert detect_project_stacks(tmp_path) == ["python"]


def test_detect_rust_from_cargo_toml(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'x'\n")
    assert detect_project_stacks(tmp_path) == ["rust"]


def test_detect_go_from_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n")
    assert detect_project_stacks(tmp_path) == ["go"]


def test_detect_java_from_pom_xml(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project><groupId>com.example</groupId></project>")
    assert detect_project_stacks(tmp_path) == ["java"]


def test_detect_spring_from_pom_xml_with_spring_boot(tmp_path: Path) -> None:
    pom = """<project>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
  </parent>
</project>"""
    (tmp_path / "pom.xml").write_text(pom)
    result = detect_project_stacks(tmp_path)
    assert "java" in result
    assert "spring" in result


def test_detect_java_without_spring_when_no_spring_boot(tmp_path: Path) -> None:
    (tmp_path / "pom.xml").write_text("<project><dependencies></dependencies></project>")
    result = detect_project_stacks(tmp_path)
    assert "java" in result
    assert "spring" not in result


def test_detect_nodejs_from_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(json.dumps({"name": "x"}))
    assert detect_project_stacks(tmp_path) == ["nodejs"]


def test_detect_nextjs_from_package_json_next_dep(tmp_path: Path) -> None:
    data = {"dependencies": {"next": "14.0.0", "react": "18.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(data))
    result = detect_project_stacks(tmp_path)
    assert "nodejs" in result
    assert "nextjs" in result
    assert "react" in result


def test_detect_react_from_package_json_react_dep(tmp_path: Path) -> None:
    data = {"dependencies": {"react": "18.0.0", "react-dom": "18.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(data))
    result = detect_project_stacks(tmp_path)
    assert "nodejs" in result
    assert "react" in result
    assert "nextjs" not in result


def test_detect_react_from_dev_dependencies(tmp_path: Path) -> None:
    data = {"devDependencies": {"react": "18.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(data))
    result = detect_project_stacks(tmp_path)
    assert "react" in result


def test_detect_nextjs_from_dev_dependencies(tmp_path: Path) -> None:
    data = {"devDependencies": {"next": "14.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(data))
    result = detect_project_stacks(tmp_path)
    assert "nextjs" in result


def test_detect_multiple_stacks(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "package.json").write_text(json.dumps({"name": "x"}))
    result = detect_project_stacks(tmp_path)
    assert "python" in result
    assert "nodejs" in result


def test_empty_dir_returns_empty_list(tmp_path: Path) -> None:
    assert detect_project_stacks(tmp_path) == []


def test_result_is_sorted(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("")
    (tmp_path / "go.mod").write_text("module x\n")
    result = detect_project_stacks(tmp_path)
    assert result == sorted(result)


def test_invalid_package_json_returns_nodejs_only(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("not valid json {{")
    result = detect_project_stacks(tmp_path)
    assert result == ["nodejs"]


# ─── extract_text_stacks ──────────────────────────────────────────────────────


def test_extract_python_from_pytest(tmp_path: Path) -> None:
    result = extract_text_stacks("use pytest and ruff for testing")
    assert "python" in result


def test_extract_python_from_mypy(tmp_path: Path) -> None:
    result = extract_text_stacks("add mypy type checking")
    assert "python" in result


def test_extract_python_from_extension(tmp_path: Path) -> None:
    result = extract_text_stacks("edited src/main.py for the fix")
    assert "python" in result


def test_extract_java_from_spring(tmp_path: Path) -> None:
    result = extract_text_stacks("Spring dependency injection")
    assert "java" in result
    assert "spring" in result


def test_extract_java_from_spring_boot(tmp_path: Path) -> None:
    result = extract_text_stacks("using spring-boot for the backend")
    assert "java" in result
    assert "spring" in result


def test_extract_java_from_extension(tmp_path: Path) -> None:
    result = extract_text_stacks("found in Main.java file")
    assert "java" in result


def test_extract_nodejs_from_npm(tmp_path: Path) -> None:
    result = extract_text_stacks("run npm install first")
    assert "nodejs" in result


def test_extract_nodejs_from_webpack(tmp_path: Path) -> None:
    result = extract_text_stacks("webpack bundles the app")
    assert "nodejs" in result


def test_extract_nextjs_from_text(tmp_path: Path) -> None:
    result = extract_text_stacks("built with Next.js app router")
    assert "nextjs" in result
    assert "nodejs" in result


def test_extract_react_from_text(tmp_path: Path) -> None:
    result = extract_text_stacks("React hooks make state easy")
    assert "react" in result


def test_extract_react_from_tsx_extension(tmp_path: Path) -> None:
    result = extract_text_stacks("updated src/Button.tsx component")
    assert "react" in result


def test_extract_rust_from_cargo(tmp_path: Path) -> None:
    result = extract_text_stacks("add serde to Cargo dependencies")
    assert "rust" in result


def test_extract_rust_from_tokio(tmp_path: Path) -> None:
    result = extract_text_stacks("tokio async runtime required")
    assert "rust" in result


def test_extract_rust_from_extension(tmp_path: Path) -> None:
    result = extract_text_stacks("change lib.rs to use the new API")
    assert "rust" in result


def test_extract_go_from_golang(tmp_path: Path) -> None:
    result = extract_text_stacks("golang goroutine pattern")
    assert "go" in result


def test_extract_go_from_extension(tmp_path: Path) -> None:
    result = extract_text_stacks("edit main.go to add the handler")
    assert "go" in result


def test_extract_case_insensitive(tmp_path: Path) -> None:
    result = extract_text_stacks("Using PYTEST for unit tests")
    assert "python" in result


def test_extract_empty_text_returns_empty(tmp_path: Path) -> None:
    assert extract_text_stacks("") == []


def test_extract_unknown_text_returns_empty(tmp_path: Path) -> None:
    assert extract_text_stacks("no keywords here at all, just words") == []


def test_extract_result_is_sorted(tmp_path: Path) -> None:
    result = extract_text_stacks("pytest and serde and npm packages")
    assert result == sorted(result)


def test_extract_multiple_stacks(tmp_path: Path) -> None:
    result = extract_text_stacks("pytest for python, jest for nodejs, serde for rust")
    assert "python" in result
    assert "nodejs" in result
    assert "rust" in result


def test_extract_no_false_positive_on_partial_match(tmp_path: Path) -> None:
    # "cargo" inside "discourage" should not match \bcargo\b
    result = extract_text_stacks("we should discourage this pattern")
    assert "rust" not in result
