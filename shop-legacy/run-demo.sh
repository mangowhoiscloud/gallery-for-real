#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — Shopping Mall MVP (Spring 4 Legacy)           ║
# ║  Java 1.8 + Spring 4.3.4 + MyBatis 3.2.2 + PostgreSQL        ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: Shopping Mall MVP (Spring 4 Legacy) ==="
echo ""
echo "Stack: Java 1.8 + Spring Framework 4.3.4 + Spring Security 4.2.4"
echo "       + MyBatis 3.2.2 + PostgreSQL"
echo ""
echo "Domains: Member, Product, Cart, Order + Frontend Pages"
echo ""
echo "Phase iterations:"
echo "  Socratic: max 5 rounds"
echo "  Plan:     max 3 rounds"
echo "  Build:    max 30 rounds"
echo "  Verify:   max 3 rounds"
echo ""

# ─── Setup project ───────────────────────────────────────────
cd "$DEMO_DIR"

# Init git if needed
if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "init: shop-legacy shopping mall mvp demo project"
fi

# Copy harness files into demo project
cp "$HARNESS_DIR/CLAUDE.md" .claude-base.md
if [ -f "CLAUDE.md" ]; then
  true
else
  cp "$HARNESS_DIR/CLAUDE.md" .
fi
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

# Restore project-specific CLAUDE.md (init.sh may overwrite it)
git checkout -- CLAUDE.md 2>/dev/null || true

git add -A
git commit -m "setup: harness files and maven project structure"

echo ""
echo "=== Starting Harness ==="
echo "  Monitor in another terminal: bash scripts/monitor.sh"
echo ""

# ─── Run harness with controlled iterations ──────────────────
MAX_SOCRATIC=5 \
MAX_PLAN=3 \
MAX_BUILD=30 \
MAX_VERIFY=3 \
MAX_STUCK=3 \
bash loop.sh socratic
