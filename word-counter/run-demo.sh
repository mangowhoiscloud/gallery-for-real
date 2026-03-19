#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — Word Counter CLI                             ║
# ║  Reduced iterations for quick test run                        ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: Word Counter CLI ==="
echo ""
echo "This demo runs the full 4-phase harness with reduced iterations:"
echo "  Socratic: max 5 rounds  (normally 150)"
echo "  Plan:     max 3 rounds  (normally 10)"
echo "  Build:    max 15 rounds (normally 999)"
echo "  Verify:   max 3 rounds  (normally 20)"
echo ""

# ─── Setup project ───────────────────────────────────────────
cd "$DEMO_DIR"

# Init git if needed
if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "init: word counter demo project"
fi

# Copy harness files into demo project
cp "$HARNESS_DIR/CLAUDE.md" .
cp "$HARNESS_DIR/AGENTS.md" .
cp "$HARNESS_DIR/PROMPT_socratic.md" .
cp "$HARNESS_DIR/PROMPT_plan.md" .
cp "$HARNESS_DIR/PROMPT_build.md" .
cp "$HARNESS_DIR/PROMPT_verify.md" .
cp "$HARNESS_DIR/loop.sh" .
cp "$HARNESS_DIR/init.sh" .
cp -r "$HARNESS_DIR/hooks" .
mkdir -p scripts
cp "$HARNESS_DIR/scripts/monitor.sh" scripts/
cp "$HARNESS_DIR/scripts/plan-parser.sh" scripts/
cp "$HARNESS_DIR/scripts/parallel-build.sh" scripts/
cp "$HARNESS_DIR/scripts/test-ratio.sh" scripts/

# Create pyproject.toml for Python project
if [ ! -f "pyproject.toml" ]; then
  cat > pyproject.toml << 'PYPROJECT'
[project]
name = "word-counter"
version = "0.1.0"
description = "CLI tool for word frequency analysis"
requires-python = ">=3.12"

[project.scripts]
wc-freq = "word_counter.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100

[tool.mypy]
strict = true
PYPROJECT
fi

mkdir -p src/word_counter tests
touch src/word_counter/__init__.py tests/__init__.py

# Run init.sh to detect project type
bash init.sh

# Create sample test file
mkdir -p testdata
cat > testdata/sample.txt << 'SAMPLE'
The quick brown fox jumps over the lazy dog.
The dog barked at the fox, and the fox ran away.
It was a quick chase, but the lazy dog didn't care.
The quick brown fox was too quick for the lazy dog.
SAMPLE

git add -A
git commit -m "setup: demo project with specs and test data"

echo ""
echo "=== Starting Harness ==="
echo "  Monitor in another terminal: bash scripts/monitor.sh"
echo ""

# ─── Run harness with reduced iterations ─────────────────────
MAX_SOCRATIC=5 \
MAX_PLAN=3 \
MAX_BUILD=15 \
MAX_VERIFY=3 \
MAX_STUCK=3 \
bash loop.sh socratic
