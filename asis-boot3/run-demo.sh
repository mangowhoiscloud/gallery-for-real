#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — AS-IS Spring Boot 3 Employee API             ║
# ║  Java 21 + Spring Boot 3.3.7 + MyBatis 3.0.4 + PostgreSQL   ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: AS-IS Spring Boot 3 Employee API ==="
echo ""
echo "Stack: Java 21 + Spring Boot 3.3.7 + Spring Security 6.x"
echo "       + MyBatis Spring Boot Starter 3.0.4 + PostgreSQL"
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
  git commit -m "init: asis spring boot 3 employee api demo project"
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
git commit -m "setup: harness files and asis spring boot 3 project"

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
