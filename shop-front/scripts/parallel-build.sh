#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════════╗
# ║  Parallel Build Orchestrator                                   ║
# ║  Runs independent items simultaneously via git worktrees       ║
# ╚═══════════════════════════════════════════════════════════════╝
#
# Usage: bash scripts/parallel-build.sh [max_parallel]
#
# Requires: IMPLEMENTATION_PLAN.md with Dependency Graph section
# Creates: git worktrees in .worktrees/ for each parallel item
# Merges: completed items back to main branch

set -euo pipefail

# ─── Configuration ─────────────────────────────────────────────
MAX_PARALLEL="${1:-3}"
WORKTREE_DIR=".worktrees"
LOG_DIR=".harness-logs"
CONFIG_FILE=".harness-config"
PLAN="IMPLEMENTATION_PLAN.md"

# Load config
if [ -f "$CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
fi

SONNET_MODEL="${SONNET_MODEL:-sonnet}"
OPUS_MODEL="${OPUS_MODEL:-opus}"
PERMISSION_MODE="${PERMISSION_MODE:---dangerously-skip-permissions}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-stream-json}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

mkdir -p "$LOG_DIR" "$WORKTREE_DIR"

# ─── Get independent items ────────────────────────────────────
get_independent_items() {
  bash scripts/plan-parser.sh independent 2>/dev/null | grep '^INDEPENDENT:' | sed 's/INDEPENDENT://' | tr -s ' '
}

# ─── Get model for item based on complexity ───────────────────
get_item_model() {
  local item_num="$1"
  local complexity
  complexity=$(bash scripts/plan-parser.sh complexity "$item_num" 2>/dev/null)
  case "$complexity" in
    S|M) echo "$SONNET_MODEL" ;;
    L|XL) echo "$OPUS_MODEL" ;;
    *) echo "$SONNET_MODEL" ;;
  esac
}

# ─── Build single item in worktree ────────────────────────────
build_in_worktree() {
  local item_num="$1"
  local branch="harness/item-${item_num}"
  local worktree="$WORKTREE_DIR/item-${item_num}"
  local log_file="$LOG_DIR/parallel_item${item_num}_$(date +%Y%m%d_%H%M%S).log"
  local model
  model=$(get_item_model "$item_num")

  echo -e "${CYAN}[PARALLEL] Starting Item $item_num in worktree (model: $model)${NC}"

  # Create worktree with new branch
  git worktree add "$worktree" -b "$branch" 2>/dev/null || {
    # Branch might already exist, try checkout
    git worktree add "$worktree" "$branch" 2>/dev/null || {
      echo -e "${RED}[PARALLEL] Failed to create worktree for Item $item_num${NC}"
      return 1
    }
  }

  # Copy harness files to worktree (they're not tracked)
  cp -f .harness-config "$worktree/" 2>/dev/null || true
  [ -f LEARNINGS.md ] && cp -f LEARNINGS.md "$worktree/" || true
  mkdir -p "$worktree/.context"
  cp -rf .context/* "$worktree/.context/" 2>/dev/null || true

  # Create item-specific build prompt
  local item_prompt="$worktree/.harness-build-prompt.md"
  {
    echo "# BUILD TARGET: Item $item_num ONLY"
    echo ""
    echo "You are building Item $item_num from IMPLEMENTATION_PLAN.md."
    echo "Focus ONLY on this item. Do not touch other items."
    echo ""
    if [ -f "LEARNINGS.md" ]; then
      echo "## Runtime Learnings (from previous iterations)"
      cat LEARNINGS.md
      echo ""
    fi
    cat PROMPT_build.md
  } > "$item_prompt"

  # Run Claude in the worktree
  (
    cd "$worktree"
    cat "$item_prompt" | claude -p \
      $PERMISSION_MODE \
      --output-format "$OUTPUT_FORMAT" \
      --model "$model" \
      --verbose 2>&1 | tee "$log_file" || true
  )

  echo -e "${GREEN}[PARALLEL] Item $item_num completed${NC}"
  return 0
}

# ─── Merge worktree back ──────────────────────────────────────
merge_worktree() {
  local item_num="$1"
  local branch="harness/item-${item_num}"
  local worktree="$WORKTREE_DIR/item-${item_num}"

  if [ ! -d "$worktree" ]; then
    echo -e "${YELLOW}[MERGE] Worktree for Item $item_num not found, skipping${NC}"
    return 1
  fi

  echo -e "${CYAN}[MERGE] Merging Item $item_num...${NC}"

  # Check if there are commits on the branch
  local main_head branch_head
  main_head=$(git rev-parse HEAD)
  branch_head=$(git rev-parse "$branch" 2>/dev/null || echo "$main_head")

  if [ "$main_head" = "$branch_head" ]; then
    echo -e "${YELLOW}[MERGE] No changes in Item $item_num${NC}"
    git worktree remove "$worktree" --force 2>/dev/null || true
    git branch -D "$branch" 2>/dev/null || true
    return 1
  fi

  # Attempt merge
  if git merge "$branch" --no-edit -m "merge: parallel build item $item_num" 2>/dev/null; then
    echo -e "${GREEN}[MERGE] Item $item_num merged successfully${NC}"
    git worktree remove "$worktree" --force 2>/dev/null || true
    git branch -d "$branch" 2>/dev/null || true
    return 0
  else
    echo -e "${RED}[MERGE] Conflict in Item $item_num — aborting merge, will retry sequentially${NC}"
    git merge --abort 2>/dev/null || true
    git worktree remove "$worktree" --force 2>/dev/null || true
    git branch -D "$branch" 2>/dev/null || true
    return 2  # signal: needs sequential rebuild
  fi
}

# ─── Cleanup ──────────────────────────────────────────────────
cleanup_worktrees() {
  git worktree prune 2>/dev/null || true
  rm -rf "$WORKTREE_DIR" 2>/dev/null || true
}

# ─── Main ─────────────────────────────────────────────────────
ITEMS=$(get_independent_items)

if [ -z "$ITEMS" ]; then
  echo -e "${YELLOW}[PARALLEL] No independent items found, falling back to sequential${NC}"
  exit 1  # signal: use sequential mode
fi

# Count items
ITEM_COUNT=$(echo "$ITEMS" | wc -w | tr -d ' ')

if [ "$ITEM_COUNT" -le 1 ]; then
  echo -e "${YELLOW}[PARALLEL] Only 1 independent item, using sequential mode${NC}"
  exit 1
fi

# Cap at MAX_PARALLEL
ITEMS_TO_BUILD=""
COUNT=0
for item in $ITEMS; do
  if [ "$COUNT" -ge "$MAX_PARALLEL" ]; then break; fi
  ITEMS_TO_BUILD="$ITEMS_TO_BUILD $item"
  COUNT=$((COUNT + 1))
done

echo ""
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║          PARALLEL BUILD — $COUNT items simultaneously          ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo -e "  Items: ${BOLD}$ITEMS_TO_BUILD${NC}"
echo ""

# Launch parallel builds
PIDS=""
for item in $ITEMS_TO_BUILD; do
  build_in_worktree "$item" &
  PIDS="$PIDS $!"
done

# Wait for all builds to complete
FAILED=""
for pid in $PIDS; do
  if ! wait "$pid"; then
    FAILED="$FAILED $pid"
  fi
done

if [ -n "$FAILED" ]; then
  echo -e "${YELLOW}[PARALLEL] Some builds had issues${NC}"
fi

# Merge results back (sequentially to avoid conflicts)
NEEDS_SEQUENTIAL=""
for item in $ITEMS_TO_BUILD; do
  merge_result=0
  merge_worktree "$item" || merge_result=$?
  if [ "$merge_result" -eq 2 ]; then
    NEEDS_SEQUENTIAL="$NEEDS_SEQUENTIAL $item"
  fi
done

# Cleanup
cleanup_worktrees

# Report
MERGED_COUNT=$((COUNT - $(echo "$NEEDS_SEQUENTIAL" | wc -w | tr -d ' ')))
echo ""
echo -e "${GREEN}[PARALLEL] $MERGED_COUNT/$COUNT items merged successfully${NC}"

if [ -n "$NEEDS_SEQUENTIAL" ]; then
  echo -e "${YELLOW}[PARALLEL] Items needing sequential rebuild:$NEEDS_SEQUENTIAL${NC}"
  # Write these back as high-priority TODO items
  for item in $NEEDS_SEQUENTIAL; do
    echo "[PARALLEL_CONFLICT] Item $item needs sequential rebuild" >> progress.txt
  done
fi

exit 0
