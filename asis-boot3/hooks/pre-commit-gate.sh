#!/usr/bin/env bash
# Pre-commit gate — reads commands from .harness-config
# Exit 0 = allow commit, Exit 2 = block (agent must fix)

cd "${CLAUDE_PROJECT_DIR:-.}"

# Load config (required — run init.sh first)
CONFIG=".harness-config"
if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
else
  echo "[gate] ERROR: .harness-config not found. Run init.sh first." >&2
  exit 2
fi

echo "[gate] Running pre-commit checks..."

# Run tests (with timeout to prevent hangs)
if [ -n "${TEST_CMD:-}" ] && [ "$TEST_CMD" != "" ]; then
  timeout 120 bash -c "$TEST_CMD" 2>&1 || { echo "[gate] Tests failed" >&2; exit 2; }
fi

# Check for skip markers in all known source/test dirs
ALL_DIRS="${SRC_DIRS:-src/} ${TEST_DIRS:-tests/}"
EXISTING_DIRS=""
for d in $ALL_DIRS; do
  [ -d "$d" ] && EXISTING_DIRS="$EXISTING_DIRS $d"
done

if [ -n "$EXISTING_DIRS" ]; then
  # shellcheck disable=SC2086
  SKIP_MARKERS=$(grep -rn 'it\.skip\|describe\.skip\|@pytest\.mark\.skip\|@Disabled\|@Ignore' $EXISTING_DIRS 2>/dev/null | head -5)
  if [ -n "$SKIP_MARKERS" ]; then
    echo "[gate] ERROR: Skipped tests found:" >&2
    echo "$SKIP_MARKERS" >&2
    exit 2
  fi
fi

# Check for TODO/FIXME in code (not in tests or docs)
SRC_ONLY="${SRC_DIRS:-src/}"
EXISTING_SRC=""
for d in $SRC_ONLY; do
  [ -d "$d" ] && EXISTING_SRC="$EXISTING_SRC $d"
done

if [ -n "$EXISTING_SRC" ]; then
  # shellcheck disable=SC2086
  TODO_MARKERS=$(grep -rn 'TODO\|FIXME\|XXX\|HACK' $EXISTING_SRC 2>/dev/null | grep -v 'node_modules\|__pycache__\|target/' | head -5)
  if [ -n "$TODO_MARKERS" ]; then
    echo "[gate] ERROR: TODO/FIXME markers found in source:" >&2
    echo "$TODO_MARKERS" >&2
    exit 2
  fi
fi

echo "[gate] All checks passed"
exit 0
