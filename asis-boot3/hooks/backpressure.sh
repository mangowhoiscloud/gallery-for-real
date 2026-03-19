#!/usr/bin/env bash
# Post-tool backpressure hook — reads commands from .harness-config
# Exit 0 = success (silent), Exit 2 = error (agent re-enters to fix)

cd "${CLAUDE_PROJECT_DIR:-.}"

# Load config (required — run init.sh first)
CONFIG=".harness-config"
if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
else
  echo "[backpressure] WARNING: .harness-config not found. Run init.sh first." >&2
  echo "[backpressure] Skipping checks — no backpressure active." >&2
  exit 0
fi

ERRORS=""

# Typecheck
if [ -n "${TYPECHECK_CMD:-}" ] && [ "$TYPECHECK_CMD" != "" ]; then
  OUTPUT=$(timeout 60 bash -c "$TYPECHECK_CMD" 2>&1) || ERRORS="${ERRORS}\n=== TypeCheck Errors ===\n${OUTPUT}\n"
fi

# Lint
if [ -n "${LINT_CMD:-}" ] && [ "$LINT_CMD" != "" ]; then
  OUTPUT=$(timeout 60 bash -c "$LINT_CMD" 2>&1) || ERRORS="${ERRORS}\n=== Lint Errors ===\n${OUTPUT}\n"
fi

if [ -n "$ERRORS" ]; then
  echo -e "$ERRORS" >&2
  exit 2
fi

exit 0
