#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Harness Demo — Shopping Mall Frontend                        ║
# ║  Next.js 15 + TypeScript + Tailwind CSS 4 + shadcn/ui        ║
# ╚═══════════════════════════════════════════════════════════════╝

HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: Shopping Mall Frontend ==="
echo ""
echo "Stack: Next.js 15 + TypeScript + Tailwind CSS 4 + shadcn/ui"
echo "       + Shopify-grade UI + Vercel deployment"
echo ""
echo "Backend: shop-boot3 REST API (HTTP Basic Auth)"
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
  git commit -m "init: shop-front next.js e-commerce frontend"
fi

# Copy harness files into demo project
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

# Run init.sh to detect project type (node-npm)
bash init.sh

# Restore project-specific CLAUDE.md (init.sh may overwrite it)
git checkout -- CLAUDE.md 2>/dev/null || true

# Install dependencies
npm install

git add -A
git commit -m "setup: harness files and next.js dependencies"

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
