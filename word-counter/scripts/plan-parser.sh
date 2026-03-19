#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  IMPLEMENTATION_PLAN.md Parser                                ║
# ║  Extracts items, dependencies, and independent groups         ║
# ╚═══════════════════════════════════════════════════════════════╝
#
# Usage:
#   bash scripts/plan-parser.sh todo          # list TODO items
#   bash scripts/plan-parser.sh complexity N  # get complexity of item N
#   bash scripts/plan-parser.sh independent   # list independent TODO groups
#   bash scripts/plan-parser.sh deps N        # list dependencies of item N
#   bash scripts/plan-parser.sh count-todo    # count remaining TODO items
#   bash scripts/plan-parser.sh failure-count N  # count failures for item N

set -euo pipefail

PLAN="IMPLEMENTATION_PLAN.md"
PROGRESS="progress.txt"

if [ ! -f "$PLAN" ]; then
  echo "ERROR: $PLAN not found" >&2
  exit 1
fi

CMD="${1:-todo}"

case "$CMD" in

  # ─── List all TODO items with their numbers ──────────────────
  todo)
    grep -n '^## Item [0-9]*:' "$PLAN" | while IFS= read -r line; do
      linenum=$(echo "$line" | cut -d: -f1)
      item_num=$(echo "$line" | grep -o 'Item [0-9]*' | grep -o '[0-9]*')

      # Check status within next 10 lines
      status=$(sed -n "$((linenum+1)),$((linenum+10))p" "$PLAN" | grep -o 'status: [A-Z_]*' | head -1 | cut -d' ' -f2)

      if [ "$status" = "TODO" ]; then
        title=$(echo "$line" | sed 's/.*Item [0-9]*: //')
        complexity=$(sed -n "$((linenum+1)),$((linenum+10))p" "$PLAN" | grep -o 'complexity: [A-Z]*' | head -1 | cut -d' ' -f2)
        priority=$(sed -n "$((linenum+1)),$((linenum+10))p" "$PLAN" | grep -o 'priority: [A-Z0-9]*' | head -1 | cut -d' ' -f2)
        echo "$item_num|$priority|$complexity|$title"
      fi
    done || true
    ;;

  # ─── Get complexity of a specific item ───────────────────────
  complexity)
    ITEM_NUM="${2:-1}"
    linenum=$(grep -n "^## Item ${ITEM_NUM}:" "$PLAN" | head -1 | cut -d: -f1)
    if [ -z "$linenum" ]; then
      echo "UNKNOWN"
      exit 0
    fi
    complexity=$(sed -n "$((linenum+1)),$((linenum+10))p" "$PLAN" | grep -o 'complexity: [A-Z]*' | head -1 | cut -d' ' -f2)
    echo "${complexity:-M}"
    ;;

  # ─── List independent TODO item groups ───────────────────────
  independent)
    # Strategy: find TODO items whose depends_on items are all DONE or empty
    # Output: space-separated item numbers per line
    # Note: bash 3.2 compatible (no associative arrays)

    # Collect TODO items and deps into temp files
    TMPDIR_PARSE=$(mktemp -d)
    trap 'rm -rf "$TMPDIR_PARSE"' EXIT

    grep -n '^## Item [0-9]*:' "$PLAN" | while IFS= read -r line; do
      linenum=$(echo "$line" | cut -d: -f1)
      item_num=$(echo "$line" | grep -o 'Item [0-9]*' | grep -o '[0-9]*')
      block=$(sed -n "$((linenum+1)),$((linenum+15))p" "$PLAN")
      status=$(echo "$block" | grep -o 'status: [A-Z_]*' | head -1 | cut -d' ' -f2)

      if [ "$status" = "TODO" ]; then
        deps=$(echo "$block" | grep 'depends_on:' | head -1 | grep -o 'Item [0-9]*' | grep -o '[0-9]*' | tr '\n' ' ' || true)
        echo "$item_num" >> "$TMPDIR_PARSE/todos.txt"
        echo "$deps" > "$TMPDIR_PARSE/deps_${item_num}.txt"
      fi
    done || true

    if [ ! -f "$TMPDIR_PARSE/todos.txt" ]; then
      exit 0
    fi

    ALL_TODOS=$(tr '\n' ' ' < "$TMPDIR_PARSE/todos.txt")

    # Find items with no TODO dependencies
    INDEPENDENT=""
    DEPENDENT=""
    for item in $ALL_TODOS; do
      deps=""
      if [ -f "$TMPDIR_PARSE/deps_${item}.txt" ]; then
        deps=$(cat "$TMPDIR_PARSE/deps_${item}.txt")
      fi
      has_todo_dep=false
      for dep in $deps; do
        if echo "$ALL_TODOS" | grep -qw "$dep"; then
          has_todo_dep=true
          break
        fi
      done
      if [ "$has_todo_dep" = false ]; then
        INDEPENDENT="$INDEPENDENT $item"
      else
        DEPENDENT="$DEPENDENT $item"
      fi
    done

    if [ -n "$INDEPENDENT" ]; then
      echo "INDEPENDENT:$INDEPENDENT"
    fi
    if [ -n "$DEPENDENT" ]; then
      echo "DEPENDENT:$DEPENDENT"
    fi
    ;;

  # ─── Get dependencies of an item ─────────────────────────────
  deps)
    ITEM_NUM="${2:-1}"
    linenum=$(grep -n "^## Item ${ITEM_NUM}:" "$PLAN" | head -1 | cut -d: -f1)
    if [ -z "$linenum" ]; then
      echo "NONE"
      exit 0
    fi
    deps=$(sed -n "$((linenum+1)),$((linenum+10))p" "$PLAN" | grep 'depends_on:' | head -1 | grep -o 'Item [0-9]*' | grep -o '[0-9]*' | tr '\n' ' ')
    echo "${deps:-NONE}"
    ;;

  # ─── Count remaining TODO items ──────────────────────────────
  count-todo)
    count=$(grep -c 'status: TODO' "$PLAN" 2>/dev/null || echo "0")
    echo "$count"
    ;;

  # ─── Count failures for a specific item (from progress.txt) ──
  failure-count)
    ITEM_NUM="${2:-1}"
    if [ ! -f "$PROGRESS" ]; then
      echo "0"
      exit 0
    fi
    count=$(grep -c "BUILD_ITEM_FAILURE.*item: $ITEM_NUM\|FAILED.*Item $ITEM_NUM\|Difficulty:.*Item $ITEM_NUM" "$PROGRESS" 2>/dev/null || echo "0")
    echo "$count"
    ;;

  *)
    echo "Usage: $0 {todo|complexity N|independent|deps N|count-todo|failure-count N}" >&2
    exit 1
    ;;
esac
