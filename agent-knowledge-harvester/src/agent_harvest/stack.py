from __future__ import annotations

import json
import re
from pathlib import Path

# Maps text patterns to stack tags.
# Tuples: (regex_pattern, stack_tags)
# Word-boundary patterns for library names; literal dot-extension patterns for extensions.
_TEXT_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    # Python
    (re.compile(r"\bpytest\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bruff\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bmypy\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bpip\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bpyproject\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bdjango\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bflask\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bfastapi\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bsqlalchemy\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bpydantic\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bpandas\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bnumpy\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bmatplotlib\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\bpython\b", re.IGNORECASE), ["python"]),
    (re.compile(r"\.py\b"), ["python"]),
    # Java / Spring
    (re.compile(r"\bspring-boot\b", re.IGNORECASE), ["java", "spring"]),
    (re.compile(r"\bspring\b", re.IGNORECASE), ["java", "spring"]),
    (re.compile(r"\bmybatis\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\bhibernate\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\bmaven\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\bgradle\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\bjunit\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\blombok\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\bjava\b", re.IGNORECASE), ["java"]),
    (re.compile(r"\.java\b"), ["java"]),
    # Next.js (check before react/nodejs to get both tags)
    (re.compile(r"\bnext\.js\b", re.IGNORECASE), ["nodejs", "nextjs"]),
    (re.compile(r"\bnextjs\b", re.IGNORECASE), ["nodejs", "nextjs"]),
    # React
    (re.compile(r"\breact\b", re.IGNORECASE), ["react"]),
    (re.compile(r"\.jsx\b"), ["react"]),
    (re.compile(r"\.tsx\b"), ["react"]),
    # Node.js
    (re.compile(r"\bnode\.js\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\bnodejs\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\bnpm\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\bexpress\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\bwebpack\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\bbabel\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\beslint\b", re.IGNORECASE), ["nodejs"]),
    (re.compile(r"\.ts\b"), ["nodejs"]),
    (re.compile(r"\.js\b"), ["nodejs"]),
    # Rust
    (re.compile(r"\bcargo\b", re.IGNORECASE), ["rust"]),
    (re.compile(r"\btokio\b", re.IGNORECASE), ["rust"]),
    (re.compile(r"\bserde\b", re.IGNORECASE), ["rust"]),
    (re.compile(r"\bactix\b", re.IGNORECASE), ["rust"]),
    (re.compile(r"\brust\b", re.IGNORECASE), ["rust"]),
    (re.compile(r"\.rs\b"), ["rust"]),
    # Go
    (re.compile(r"\bgolang\b", re.IGNORECASE), ["go"]),
    (re.compile(r"\bgorilla\b", re.IGNORECASE), ["go"]),
    (re.compile(r"\bgin\b", re.IGNORECASE), ["go"]),
    (re.compile(r"\.go\b"), ["go"]),
]


def detect_project_stacks(project_dir: Path) -> list[str]:
    """Detect stack tags from marker files in project_dir.

    Checks for pyproject.toml (python), pom.xml (java/spring),
    package.json (nodejs/nextjs/react), Cargo.toml (rust), go.mod (go).
    Returns sorted unique list of stack tags.
    """
    stacks: set[str] = set()

    if (project_dir / "pyproject.toml").exists() or (project_dir / "setup.py").exists():
        stacks.add("python")

    if (project_dir / "Cargo.toml").exists():
        stacks.add("rust")

    if (project_dir / "go.mod").exists():
        stacks.add("go")

    pom = project_dir / "pom.xml"
    if pom.exists():
        stacks.add("java")
        try:
            content = pom.read_text(encoding="utf-8")
            if "spring-boot" in content:
                stacks.add("spring")
        except OSError:
            pass

    pkg = project_dir / "package.json"
    if pkg.exists():
        stacks.add("nodejs")
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
            all_deps: dict[str, str] = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))
            if "next" in all_deps:
                stacks.add("nextjs")
            if "react" in all_deps or "react-dom" in all_deps:
                stacks.add("react")
        except (OSError, json.JSONDecodeError):
            pass

    return sorted(stacks)


def extract_text_stacks(text: str) -> list[str]:
    """Scan text for known library/extension names and return matched stack tags.

    Returns sorted unique list of stack tags.
    """
    stacks: set[str] = set()
    for pattern, tags in _TEXT_PATTERNS:
        if pattern.search(text):
            stacks.update(tags)
    return sorted(stacks)
