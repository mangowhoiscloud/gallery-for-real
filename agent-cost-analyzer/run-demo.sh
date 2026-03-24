#!/usr/bin/env bash
set -euo pipefail
HARNESS_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Harness Demo: Agent Cost Analyzer ==="
echo "Stack: Python 3.11+ / uv / jinja2 / Chart.js"
echo ""

cd "$DEMO_DIR"
if [ ! -d ".git" ]; then
  git init && git add -A && git commit -m "init: agent-cost-analyzer"
fi

[ -f "CLAUDE.md" ] || cp "$HARNESS_DIR/CLAUDE.md" .
cp "$HARNESS_DIR/AGENTS.md" "$HARNESS_DIR/PROMPT_socratic.md" "$HARNESS_DIR/PROMPT_plan.md" "$HARNESS_DIR/PROMPT_build.md" "$HARNESS_DIR/PROMPT_verify.md" "$HARNESS_DIR/loop.sh" "$HARNESS_DIR/init.sh" .
cp -r "$HARNESS_DIR/hooks" .
mkdir -p scripts
cp "$HARNESS_DIR/scripts/monitor.sh" "$HARNESS_DIR/scripts/plan-parser.sh" "$HARNESS_DIR/scripts/parallel-build.sh" "$HARNESS_DIR/scripts/test-ratio.sh" scripts/

bash init.sh
git checkout -- CLAUDE.md 2>/dev/null || true
git add -A && git commit -m "setup: harness files"

MAX_SOCRATIC=5 MAX_PLAN=3 MAX_BUILD=20 MAX_VERIFY=3 MAX_STUCK=3 bash loop.sh socratic
