#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Ralphton Harness — Live Monitor                             ║
# ║  Run in a separate terminal: bash scripts/monitor.sh          ║
# ╚═══════════════════════════════════════════════════════════════╝

LOG_DIR=".harness-logs"
COST_LOG="$LOG_DIR/cost.log"
PHASE_LOG="$LOG_DIR/phase.log"
REFRESH="${1:-5}"  # Refresh interval in seconds

# Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

while true; do
  clear

  echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║          RALPHTON HARNESS — Live Monitor                 ║${NC}"
  echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
  echo ""

  # ─── Current phase ─────────────────────────────────────────
  if [ -f "$PHASE_LOG" ]; then
    LAST_EVENT=$(tail -1 "$PHASE_LOG" 2>/dev/null || echo "none")
    echo -e "${BOLD}Last Event:${NC} $LAST_EVENT"
  fi
  echo ""

  # ─── Git status ────────────────────────────────────────────
  echo -e "${BOLD}=== Git ===${NC}"
  COMMIT_COUNT=$(git rev-list --count HEAD 2>/dev/null || echo "0")
  LAST_COMMIT=$(git log --oneline -1 2>/dev/null || echo "none")
  echo "  Commits:     $COMMIT_COUNT"
  echo "  Last commit: $LAST_COMMIT"
  echo ""

  # ─── Implementation Plan ───────────────────────────────────
  if [ -f "IMPLEMENTATION_PLAN.md" ]; then
    echo -e "${BOLD}=== Implementation Plan ===${NC}"
    TOTAL=$(grep -c "status:" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
    DONE=$(grep -c "status: DONE" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
    TODO=$(grep -c "status: TODO" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
    WIP=$(grep -c "status: IN_PROGRESS" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
    BLOCKED=$(grep -c "status: BLOCKED" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")

    echo -e "  Total:       ${BOLD}$TOTAL${NC}"
    echo -e "  Done:        ${GREEN}$DONE${NC}"
    echo -e "  TODO:        ${YELLOW}$TODO${NC}"
    echo -e "  In Progress: ${CYAN}$WIP${NC}"
    echo -e "  Blocked:     ${RED}$BLOCKED${NC}"

    if [ "$TOTAL" -gt 0 ]; then
      PCT=$((DONE * 100 / TOTAL))
      BAR_LEN=30
      FILLED=$((PCT * BAR_LEN / 100))
      EMPTY=$((BAR_LEN - FILLED))
      BAR=""
      for ((i=0; i<FILLED; i++)); do BAR="${BAR}#"; done
      SPACE=""
      for ((i=0; i<EMPTY; i++)); do SPACE="${SPACE}-"; done
      echo -e "  Progress:    [${GREEN}${BAR}${NC}${SPACE}] ${PCT}%"
    fi
    echo ""
  fi

  # ─── Clarity Log (Socratic) ────────────────────────────────
  if [ -f "CLARITY_LOG.md" ]; then
    echo -e "${BOLD}=== Socratic Phase ===${NC}"
    ROUNDS=$(grep -c "^Round:" CLARITY_LOG.md 2>/dev/null || echo "0")
    SCORE=$(grep 'AMBIGUITY_SCORE:' CLARITY_LOG.md 2>/dev/null | tail -1 | sed 's/.*AMBIGUITY_SCORE:[[:space:]]*//' | grep -o '[0-9.]*' | head -1 || echo "N/A")
    COMPLETE=$(grep -c "PHASE_0_COMPLETE" CLARITY_LOG.md 2>/dev/null || echo "0")

    echo "  Rounds:      $ROUNDS"
    echo "  Ambiguity:   $SCORE"
    [ "$COMPLETE" -gt 0 ] && echo -e "  Status:      ${GREEN}COMPLETE${NC}" || echo -e "  Status:      ${YELLOW}IN PROGRESS${NC}"
    echo ""
  fi

  # ─── Spec Hash Check ──────────────────────────────────
  if [ -d "specs" ] && [ -f "CLARITY_LOG.md" ]; then
    echo -e "${BOLD}=== Spec Integrity ===${NC}"
    CURRENT_HASH=$(find specs/ -type f -exec md5 -q {} \; 2>/dev/null | sort | md5 -q 2>/dev/null || find specs/ -type f -exec md5sum {} \; 2>/dev/null | sort | md5sum 2>/dev/null | cut -d' ' -f1)
    if [ -f ".harness-logs/specs.hash" ]; then
      SAVED_HASH=$(cat .harness-logs/specs.hash)
      if [ "$CURRENT_HASH" = "$SAVED_HASH" ]; then
        echo -e "  Status: ${GREEN}Unchanged${NC}"
      else
        echo -e "  Status: ${RED}SPECS CHANGED since Socratic phase!${NC}"
        echo -e "  ${YELLOW}CLARITY_LOG.md may be outdated${NC}"
      fi
    else
      echo "  No baseline hash (Socratic phase not completed)"
    fi
    echo ""
  fi

  # ─── Cost ──────────────────────────────────────────────────
  if [ -f "$COST_LOG" ]; then
    echo -e "${BOLD}=== Cost ===${NC}"
    ENTRIES=$(wc -l < "$COST_LOG" 2>/dev/null || echo "0")
    echo "  Iterations tracked: $ENTRIES"
    tail -3 "$COST_LOG" 2>/dev/null | while read -r line; do
      echo "  $line"
    done
    echo ""
  fi

  # ─── Progress (last 5 lines) ───────────────────────────────
  if [ -f "progress.txt" ]; then
    echo -e "${BOLD}=== Recent Progress ===${NC}"
    tail -8 progress.txt 2>/dev/null
    echo ""
  fi

  # ─── Loop logs ─────────────────────────────────────────────
  LATEST_LOG=$(ls -t "$LOG_DIR"/*.log 2>/dev/null | head -1)
  if [ -n "${LATEST_LOG:-}" ]; then
    echo -e "${BOLD}=== Latest Log ===${NC} ($LATEST_LOG)"
    tail -5 "$LATEST_LOG" 2>/dev/null
    echo ""
  fi

  # ─── Harness completion check ──────────────────────────────
  if [ -f "progress.txt" ] && grep -q "HARNESS_COMPLETE" progress.txt 2>/dev/null; then
    echo -e "${GREEN}${BOLD}>>> HARNESS COMPLETE <<<${NC}"
  fi

  echo -e "${BOLD}Last updated: $(date +%H:%M:%S) | Refreshing every ${REFRESH}s...${NC} (Ctrl+C to stop)"
  sleep "$REFRESH"
done
