#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — Agent Knowledge Harvester                     ║
# ║  Python 3.11+ CLI: Extract patterns from agent sessions        ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: Agent Knowledge Harvester ==="
echo ""
echo "Stack: Python 3.11+ / uv / pyyaml"
echo ""
echo "Features: LEARNINGS.md parsing, git diff analysis,"
echo "          cross-project pattern synthesis, skill generation"
echo ""

# ─── Setup project ───────────────────────────────────────────
cd "$DEMO_DIR"

if [ ! -d ".git" ]; then
  git init
  git add -A
  git commit -m "init: agent-knowledge-harvester pattern extraction cli"
fi

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

bash init.sh
git checkout -- CLAUDE.md 2>/dev/null || true

git add -A
git commit -m "setup: harness files and python project structure"

echo ""
echo "=== Starting Harness ==="
echo "  Monitor in another terminal: bash scripts/monitor.sh"
echo ""

MAX_SOCRATIC=5 \
MAX_PLAN=3 \
MAX_BUILD=20 \
MAX_VERIFY=3 \
MAX_STUCK=3 \
bash loop.sh socratic
