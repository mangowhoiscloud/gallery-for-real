#!/usr/bin/env bash
# Measures test code ratio across the project
# Usage: bash scripts/test-ratio.sh

cd "${1:-.}"

CONFIG=".harness-config"
if [ -f "$CONFIG" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG"
fi

TARGET="${TEST_CODE_RATIO_TARGET:-0.70}"
SRC="${SRC_DIRS:-src/ lib/}"
TST="${TEST_DIRS:-tests/ test/ __tests__/ spec/}"

# Count lines in existing source dirs
SRC_LINES=0
for d in $SRC; do
  if [ -d "$d" ]; then
    LINES=$(find "$d" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.java' -o -name '*.go' -o -name '*.rs' \) -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    SRC_LINES=$((SRC_LINES + ${LINES:-0}))
  fi
done

# Count lines in existing test dirs
TEST_LINES=0
for d in $TST; do
  if [ -d "$d" ]; then
    LINES=$(find "$d" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.java' -o -name '*.go' -o -name '*.rs' \) -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    TEST_LINES=$((TEST_LINES + ${LINES:-0}))
  fi
done

TOTAL=$((SRC_LINES + TEST_LINES))
if [ "$TOTAL" -eq 0 ]; then
  echo "No code found."
  exit 0
fi

RATIO=$(awk -v tl="$TEST_LINES" -v tot="$TOTAL" 'BEGIN {printf "%.2f", tl / tot}' 2>/dev/null || echo "0")
PCT=$(awk -v r="$RATIO" 'BEGIN {printf "%.0f", r * 100}' 2>/dev/null || echo "0")
TARGET_PCT=$(awk -v t="$TARGET" 'BEGIN {printf "%.0f", t * 100}' 2>/dev/null || echo "70")

echo "=== Test Code Ratio ==="
echo "  Source lines: $SRC_LINES"
echo "  Test lines:   $TEST_LINES"
echo "  Total:        $TOTAL"
echo "  Ratio:        ${PCT}% (target: ${TARGET_PCT}%)"

if awk -v r="$RATIO" -v t="$TARGET" 'BEGIN {exit (r >= t) ? 0 : 1}' 2>/dev/null; then
  echo "  Status:       PASS"
  exit 0
else
  echo "  Status:       BELOW TARGET"
  exit 1
fi
