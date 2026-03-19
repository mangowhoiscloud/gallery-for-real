#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — ASIS Legacy Employee API                     ║
# ║  Java 1.8 + Spring 4.3.4 + MyBatis 3.2.2 + PostgreSQL       ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: ASIS Legacy Employee API ==="
echo ""
echo "Stack: Java 1.8 + Spring Framework 4.3.4 + Spring Security 4.2.4"
echo "       + MyBatis 3.2.2 + PostgreSQL"
echo ""
echo "Phase iterations:"
echo "  Socratic: max 5 rounds"
echo "  Plan:     max 3 rounds"
echo "  Build:    max 20 rounds"
echo "  Verify:   max 3 rounds"
echo ""

# ─── Setup project ───────────────────────────────────────────
cd "$DEMO_DIR"

# Init git if needed
if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "init: asis legacy employee api demo project"
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

# Run init.sh to detect project type (java-maven)
bash init.sh

git add -A
git commit -m "setup: harness files and maven project structure"

echo ""
echo "=== Starting Harness ==="
echo "  Monitor in another terminal: bash scripts/monitor.sh"
echo ""

# ─── Run harness with controlled iterations ──────────────────
MAX_SOCRATIC=5 \
MAX_PLAN=3 \
MAX_BUILD=20 \
MAX_VERIFY=3 \
MAX_STUCK=3 \
bash loop.sh socratic
