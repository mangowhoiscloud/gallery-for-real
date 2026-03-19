#!/usr/bin/env bash
set -euo pipefail

# ╔═══════════════════════════════════════════════════════════════╗
# ║  Ralphton Harness v2 — 4-Phase Autonomous Loop                ║
# ║  Phases: Socratic → Plan → Build → Verify → DONE              ║
# ║                                                                ║
# ║  v2 Enhancements:                                             ║
# ║    1. Parallel Build (git worktree)                            ║
# ║    2. Predictive Circuit Breaker                               ║
# ║    3. Runtime Learning (LEARNINGS.md + chub annotate)          ║
# ║    4. Adaptive Model Routing (per-item complexity)             ║
# ║    5. Socratic Convergence Acceleration                        ║
# ╚═══════════════════════════════════════════════════════════════╝

# ─── Load shared config ─────────────────────────────────────────
CONFIG_FILE=".harness-config"
if [ -f "$CONFIG_FILE" ]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
fi

# ─── Configuration (env vars override config) ───────────────────
PHASE="${1:-socratic}"
MAX_STUCK="${MAX_STUCK:-5}"
PREDICTIVE_STUCK="${PREDICTIVE_STUCK:-2}"  # v2: predict after 2 failures
OPUS_MODEL="${OPUS_MODEL:-opus}"
SONNET_MODEL="${SONNET_MODEL:-sonnet}"
PERMISSION_MODE="${PERMISSION_MODE:---dangerously-skip-permissions}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-stream-json}"
BUDGET_USD="${MAX_BUDGET_USD:-0}"
AMBIGUITY_THRESHOLD="${AMBIGUITY_THRESHOLD:-0.10}"
CONVERGENCE_THRESHOLD="${CONVERGENCE_THRESHOLD:-0.15}"  # v2: relaxed threshold
CONVERGENCE_STAGNATION="${CONVERGENCE_STAGNATION:-3}"   # v2: stagnation rounds
MAX_PARALLEL="${MAX_PARALLEL:-3}"                        # v2: max parallel builds
LOG_DIR=".harness-logs"
COST_LOG="$LOG_DIR/cost.log"
PHASE_LOG="$LOG_DIR/phase.log"
METRICS_LOG="$LOG_DIR/metrics.log"  # v2: per-iteration metrics
STATE_FILE="$LOG_DIR/harness-state.json"

# Pricing from config or defaults
OPUS_INPUT_PRICE="${OPUS_INPUT_PRICE:-0.000015}"
OPUS_OUTPUT_PRICE="${OPUS_OUTPUT_PRICE:-0.000075}"
SONNET_INPUT_PRICE="${SONNET_INPUT_PRICE:-0.000003}"
SONNET_OUTPUT_PRICE="${SONNET_OUTPUT_PRICE:-0.000015}"

# ─── State ───────────────────────────────────────────────────────
ITERATION=0
TOTAL_ITERATION=0
STUCK_COUNT=0
LAST_COMMIT=""
TOTAL_INPUT_TOKENS=0
TOTAL_OUTPUT_TOKENS=0
ESTIMATED_COST=0
START_TIME=$(date +%s)
CURRENT_ITEM=""           # v2: current build item number
ITEM_FAIL_COUNT=0         # v2: failures on current item
ESCALATED=false           # v2: model escalated for current item

# ─── Allow nested claude invocations ─────────────────────────────
unset CLAUDECODE 2>/dev/null || true

# ─── Colors ──────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Setup ───────────────────────────────────────────────────────
mkdir -p "$LOG_DIR"
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$BRANCH" = "unknown" ]; then
  echo -e "${YELLOW}WARNING: Could not detect git branch. Using 'unknown'.${NC}"
fi

# ─── Checkpoint: resume from saved state ─────────────────────────
load_checkpoint() {
  if [ -f "$STATE_FILE" ] && [ "$PHASE" = "socratic" ]; then
    if [ "${2:-}" != "--fresh" ]; then
      local saved_phase saved_iter saved_total
      saved_phase=$(grep -o '"phase":"[^"]*"' "$STATE_FILE" 2>/dev/null | head -1 | cut -d'"' -f4)
      saved_iter=$(grep -o '"iteration":[0-9]*' "$STATE_FILE" 2>/dev/null | head -1 | cut -d: -f2)
      saved_total=$(grep -o '"total_iteration":[0-9]*' "$STATE_FILE" 2>/dev/null | head -1 | cut -d: -f2)
      if [ -n "$saved_phase" ] && [ "$saved_phase" != "DONE" ]; then
        echo -e "${CYAN}[RESUME] Restoring from checkpoint: phase=$saved_phase iter=$saved_iter${NC}"
        PHASE="$saved_phase"
        ITERATION="${saved_iter:-0}"
        TOTAL_ITERATION="${saved_total:-0}"
      fi
    fi
  fi
}

save_checkpoint() {
  cat > "$STATE_FILE" << CKPT_EOF
{"phase":"$PHASE","iteration":$ITERATION,"total_iteration":$TOTAL_ITERATION,"timestamp":"$(date -Iseconds)","stuck_count":$STUCK_COUNT,"current_item":"$CURRENT_ITEM","item_fail_count":$ITEM_FAIL_COUNT}
CKPT_EOF
}

# ─── Phase → Default Model mapping ──────────────────────────────
get_model() {
  case "$1" in
    socratic) echo "$OPUS_MODEL" ;;
    plan)     echo "$OPUS_MODEL" ;;
    build)    echo "$SONNET_MODEL" ;;
    verify)   echo "$OPUS_MODEL" ;;
    *)        echo "$SONNET_MODEL" ;;
  esac
}

# ═══════════════════════════════════════════════════════════════════
# v2 FEATURE 4: Adaptive Model Routing
# ═══════════════════════════════════════════════════════════════════
get_adaptive_model() {
  local phase="$1"

  if [ "$phase" != "build" ]; then
    get_model "$phase"
    return
  fi

  # Already escalated → stay on Opus
  if [ "$ESCALATED" = true ]; then
    echo "$OPUS_MODEL"
    return
  fi

  # Get current item complexity from plan
  if [ -n "$CURRENT_ITEM" ] && [ -f "scripts/plan-parser.sh" ]; then
    local complexity
    complexity=$(bash scripts/plan-parser.sh complexity "$CURRENT_ITEM" 2>/dev/null || echo "M")

    case "$complexity" in
      S|M)
        # Auto-escalate after PREDICTIVE_STUCK failures
        if [ "$ITEM_FAIL_COUNT" -ge "$PREDICTIVE_STUCK" ]; then
          echo -e "${YELLOW}  [ADAPTIVE] Item $CURRENT_ITEM: $ITEM_FAIL_COUNT failures → Opus${NC}" >&2
          ESCALATED=true
          echo "$OPUS_MODEL"
        else
          echo "$SONNET_MODEL"
        fi
        ;;
      L|XL)
        echo "$OPUS_MODEL"
        ;;
      *)
        echo "$SONNET_MODEL"
        ;;
    esac
  else
    echo "$SONNET_MODEL"
  fi
}

# ═══════════════════════════════════════════════════════════════════
# v2 FEATURE 5: Socratic Convergence Acceleration
# ═══════════════════════════════════════════════════════════════════
detect_convergence() {
  if [ ! -f "CLARITY_LOG.md" ]; then return 1; fi

  # Check for explicit CONVERGENCE_DETECTED marker from agent
  if grep -q "CONVERGENCE_DETECTED: true" CLARITY_LOG.md 2>/dev/null; then
    local score
    score=$(grep 'AMBIGUITY_SCORE:' CLARITY_LOG.md 2>/dev/null | tail -1 | sed 's/.*AMBIGUITY_SCORE:[[:space:]]*//' | grep -o '[0-9]*\.[0-9]*' | head -1)
    if [ -n "$score" ]; then
      local critical_count
      critical_count=$(grep 'CRITICAL: [0-9]*' CLARITY_LOG.md 2>/dev/null | tail -1 | grep -o '[0-9]*$' || echo "0")
      if [ "${critical_count:-0}" -eq 0 ]; then
        if awk -v s="$score" -v t="$CONVERGENCE_THRESHOLD" 'BEGIN {exit (s < t) ? 0 : 1}' 2>/dev/null; then
          echo -e "${GREEN}  [CONVERGENCE] Agent-detected: score=$score < $CONVERGENCE_THRESHOLD, CRITICAL=0${NC}"
          log_phase "CONVERGENCE" "score=$score threshold=$CONVERGENCE_THRESHOLD critical=0"
          return 0
        fi
      fi
    fi
  fi

  # Fallback: harness-side stagnation detection from score history
  local scores
  scores=$(grep 'AMBIGUITY_SCORE:' CLARITY_LOG.md 2>/dev/null | sed 's/.*AMBIGUITY_SCORE:[[:space:]]*//' | grep -o '[0-9]*\.[0-9]*')
  local score_count
  score_count=$(echo "$scores" | grep -c '[0-9]' 2>/dev/null || echo "0")

  if [ "$score_count" -ge "$((CONVERGENCE_STAGNATION + 1))" ]; then
    local recent
    recent=$(echo "$scores" | tail -"$((CONVERGENCE_STAGNATION + 1))")
    local stagnant=true
    local prev=""
    for s in $recent; do
      if [ -n "$prev" ]; then
        local delta
        delta=$(awk -v a="$prev" -v b="$s" 'BEGIN {d=a-b; if(d<0)d=-d; printf "%.4f", d}' 2>/dev/null || echo "1")
        if awk -v d="$delta" 'BEGIN {exit (d >= 0.01) ? 0 : 1}' 2>/dev/null; then
          stagnant=false
          break
        fi
      fi
      prev="$s"
    done

    if [ "$stagnant" = true ]; then
      local latest
      latest=$(echo "$scores" | tail -1)
      if awk -v s="$latest" -v t="$CONVERGENCE_THRESHOLD" 'BEGIN {exit (s < t) ? 0 : 1}' 2>/dev/null; then
        echo -e "${GREEN}  [CONVERGENCE] Stagnation detected: score=$latest, $CONVERGENCE_STAGNATION rounds flat${NC}"
        log_phase "CONVERGENCE_STAGNATION" "score=$latest rounds=$score_count"
        return 0
      fi
    fi
  fi

  return 1
}

# ─── Phase → Max iterations ─────────────────────────────────────
get_max_iter() {
  case "$1" in
    socratic) echo "${MAX_SOCRATIC:-150}" ;;
    plan)     echo "${MAX_PLAN:-10}" ;;
    build)    echo "${MAX_BUILD:-999}" ;;
    verify)   echo "${MAX_VERIFY:-20}" ;;
    *)        echo 10 ;;
  esac
}

get_phase_icon() {
  case "$1" in
    socratic) echo "[?]" ;;
    plan)     echo "[P]" ;;
    build)    echo "[B]" ;;
    verify)   echo "[V]" ;;
    *)        echo "[.]" ;;
  esac
}

next_phase() {
  case "$1" in
    socratic) echo "plan" ;;
    plan)     echo "build" ;;
    build)    echo "verify" ;;
    verify)   echo "DONE" ;;
    *)        echo "DONE" ;;
  esac
}

# ─── Transition conditions ───────────────────────────────────────
should_transition() {
  case "$PHASE" in
    socratic)
      if [ -f "CLARITY_LOG.md" ]; then
        grep -q "PHASE_0_COMPLETE" CLARITY_LOG.md 2>/dev/null && return 0
        local score
        score=$(grep 'AMBIGUITY_SCORE:' CLARITY_LOG.md 2>/dev/null | tail -1 | sed 's/.*AMBIGUITY_SCORE:[[:space:]]*//' | grep -o '[0-9]*\.[0-9]*' | head -1)
        if [ -n "$score" ]; then
          # Standard threshold
          awk -v s="$score" -v t="$AMBIGUITY_THRESHOLD" 'BEGIN {exit (s < t) ? 0 : 1}' && return 0
          # v2: Convergence gate
          detect_convergence && return 0
        fi
      fi
      return 1
      ;;
    plan)
      if [ -f "IMPLEMENTATION_PLAN.md" ]; then
        grep -q "PHASE_1_COMPLETE" IMPLEMENTATION_PLAN.md 2>/dev/null && return 0
        grep -cq "status:" IMPLEMENTATION_PLAN.md 2>/dev/null && return 0
      fi
      return 1
      ;;
    build)
      if [ -f "IMPLEMENTATION_PLAN.md" ]; then
        local remaining
        remaining=$(grep -c "status: TODO\|status: IN_PROGRESS" IMPLEMENTATION_PLAN.md 2>/dev/null || echo "0")
        [ "$remaining" -eq 0 ] && return 0
      fi
      return 1
      ;;
    verify)
      [ -f "progress.txt" ] && grep -q "HARNESS_COMPLETE" progress.txt 2>/dev/null && return 0
      return 1
      ;;
  esac
  return 1
}

# ─── Circuit breaker ────────────────────────────────────────────
check_circuit_breaker() {
  local current_commit
  current_commit=$(git rev-parse HEAD 2>/dev/null || echo "none")

  if [ "$current_commit" = "$LAST_COMMIT" ]; then
    STUCK_COUNT=$((STUCK_COUNT + 1))
  else
    STUCK_COUNT=0
    LAST_COMMIT="$current_commit"
  fi

  [ "$STUCK_COUNT" -ge "$MAX_STUCK" ] && return 1
  return 0
}

# ═══════════════════════════════════════════════════════════════════
# v2 FEATURE 2: Predictive Circuit Breaker
# ═══════════════════════════════════════════════════════════════════
predictive_check() {
  if [ "$PHASE" != "build" ]; then return 0; fi

  local log_file="$1"
  if [ ! -f "$log_file" ]; then return 0; fi

  # Check for BUILD_ITEM_FAILURE marker from agent
  if grep -q "BUILD_ITEM_FAILURE" "$log_file" 2>/dev/null; then
    ITEM_FAIL_COUNT=$((ITEM_FAIL_COUNT + 1))
    local suggestion
    suggestion=$(grep 'suggestion:' "$log_file" 2>/dev/null | tail -1 | sed 's/.*suggestion: //' | tr -d ' ')

    echo -e "${YELLOW}[PREDICT] Item $CURRENT_ITEM failure #$ITEM_FAIL_COUNT (suggestion: ${suggestion:-unknown})${NC}"
    log_phase "PREDICT_FAILURE" "item=$CURRENT_ITEM count=$ITEM_FAIL_COUNT suggestion=${suggestion:-unknown}"
    log_metrics "item_failure" "$CURRENT_ITEM" "$ITEM_FAIL_COUNT" "${suggestion:-unknown}"

    case "${suggestion:-RETRY}" in
      SPLIT)
        echo -e "${MAGENTA}[PREDICT] Agent suggests splitting Item $CURRENT_ITEM${NC}"
        CURRENT_ITEM=""
        ITEM_FAIL_COUNT=0
        ESCALATED=false
        ;;
      ESCALATE)
        if [ "$ESCALATED" != true ]; then
          echo -e "${MAGENTA}[PREDICT] Escalating to Opus for Item $CURRENT_ITEM${NC}"
          ESCALATED=true
        fi
        ;;
      SKIP)
        echo -e "${MAGENTA}[PREDICT] Skipping Item $CURRENT_ITEM${NC}"
        CURRENT_ITEM=""
        ITEM_FAIL_COUNT=0
        ESCALATED=false
        ;;
      *)
        if [ "$ITEM_FAIL_COUNT" -ge "$PREDICTIVE_STUCK" ] && [ "$ESCALATED" != true ]; then
          echo -e "${MAGENTA}[PREDICT] Auto-escalating to Opus after $ITEM_FAIL_COUNT failures${NC}"
          ESCALATED=true
        fi
        ;;
    esac
  fi

  # Track error trend
  local error_count
  error_count=$(grep -c 'error\|Error\|ERROR\|FAIL\|FAILED' "$log_file" 2>/dev/null || echo "0")
  log_metrics "error_count" "$PHASE" "$ITERATION" "$error_count"

  return 0
}

# ─── Circuit breaker recovery ────────────────────────────────────
recover_from_stuck() {
  local model
  model=$(get_adaptive_model "$PHASE")

  echo -e "${RED}[CIRCUIT BREAKER]${NC} Stuck for $STUCK_COUNT iterations in phase: $PHASE"
  log_phase "CIRCUIT_BREAKER" "Stuck $STUCK_COUNT iterations, phase=$PHASE, model=$model"

  local recovery_model
  if [ "$model" = "$SONNET_MODEL" ]; then
    recovery_model="$OPUS_MODEL"
    echo -e "${YELLOW}  -> Escalating Sonnet to Opus for recovery${NC}"
  else
    recovery_model="$OPUS_MODEL"
    echo -e "${YELLOW}  -> Retrying with Opus + fresh context${NC}"
  fi

  STUCK_COUNT=0

  RECOVERY_LOG="$LOG_DIR/recovery_$(date +%Y%m%d_%H%M%S).log"
  {
    echo "RECOVERY MODE: The harness detected $MAX_STUCK consecutive iterations with no git commits in phase '$PHASE'."
    echo "Try a DIFFERENT approach than previous iterations. Check git log and progress.txt for what was already attempted."
    echo "If blocked, document the blocker in progress.txt and exit."
    echo "---"
    inject_learnings
    cat "PROMPT_${PHASE}.md"
  } | claude -p \
    $PERMISSION_MODE \
    --output-format "$OUTPUT_FORMAT" \
    --model "$recovery_model" \
    --verbose 2>&1 | tee -a "$RECOVERY_LOG" || true

  local new_commit
  new_commit=$(git rev-parse HEAD 2>/dev/null || echo "none")
  if [ "$new_commit" != "$LAST_COMMIT" ]; then
    echo -e "${GREEN}  -> Recovery successful${NC}"
    LAST_COMMIT="$new_commit"
    return 0
  fi

  echo -e "${YELLOW}  -> Recovery failed, forcing transition to next phase${NC}"
  local next
  next=$(next_phase "$PHASE")
  if [ "$next" = "DONE" ]; then
    echo -e "${RED}  -> Cannot advance further. Harness stopping.${NC}"
    return 1
  fi
  PHASE="$next"
  ITERATION=0
  STUCK_COUNT=0
  CURRENT_ITEM=""
  ITEM_FAIL_COUNT=0
  ESCALATED=false
  return 0
}

# ═══════════════════════════════════════════════════════════════════
# v2 FEATURE 3: Runtime Learning Injection
# ═══════════════════════════════════════════════════════════════════
inject_learnings() {
  if [ -f "LEARNINGS.md" ]; then
    echo ""
    echo "## Runtime Learnings (accumulated from previous iterations)"
    echo "These are discoveries from earlier build sessions. Follow these rules."
    echo ""
    cat LEARNINGS.md
    echo ""
    echo "---"
    echo ""
  fi
}

# ═══════════════════════════════════════════════════════════════════
# v2 FEATURE 1: Parallel Build
# ═══════════════════════════════════════════════════════════════════
try_parallel_build() {
  if [ "$PHASE" != "build" ]; then return 1; fi
  if [ ! -f "scripts/plan-parser.sh" ] || [ ! -f "scripts/parallel-build.sh" ]; then return 1; fi

  # Need >1 TODO items to consider parallel
  local todo_count
  todo_count=$(bash scripts/plan-parser.sh count-todo 2>/dev/null) || todo_count="0"
  if [ "$todo_count" -le 1 ] 2>/dev/null; then return 1; fi

  # Check for independent items
  local independent
  independent=$(bash scripts/plan-parser.sh independent 2>/dev/null | grep '^INDEPENDENT:' | sed 's/INDEPENDENT://') || independent=""
  independent=$(echo "$independent" | tr -s ' ')
  local ind_count
  ind_count=$(echo "$independent" | wc -w | tr -d ' ') || ind_count="0"

  if [ "$ind_count" -le 1 ]; then return 1; fi

  echo -e "${CYAN}[PARALLEL] $ind_count independent items detected, launching parallel build${NC}"
  log_phase "PARALLEL_START" "items=$ind_count max=$MAX_PARALLEL"

  if bash scripts/parallel-build.sh "$MAX_PARALLEL" 2>&1; then
    echo -e "${GREEN}[PARALLEL] Parallel build completed${NC}"
    log_phase "PARALLEL_DONE" "success"
    return 0
  else
    echo -e "${YELLOW}[PARALLEL] Falling back to sequential${NC}"
    return 1
  fi
}

# ─── Detect current build item ───────────────────────────────────
detect_current_item() {
  if [ "$PHASE" != "build" ] || [ ! -f "scripts/plan-parser.sh" ]; then return; fi

  local first_todo
  first_todo=$(bash scripts/plan-parser.sh todo 2>/dev/null | head -1 | cut -d'|' -f1)

  if [ -n "$first_todo" ] && [ "$first_todo" != "$CURRENT_ITEM" ]; then
    CURRENT_ITEM="$first_todo"
    ITEM_FAIL_COUNT=0
    ESCALATED=false
  fi
}

# ─── Cost tracking ──────────────────────────────────────────────
track_cost() {
  local log_file="$1"
  if [ ! -f "$log_file" ]; then return; fi

  local input_tokens output_tokens
  input_tokens=$(grep '"input_tokens"' "$log_file" 2>/dev/null | tail -1 | sed 's/.*"input_tokens":[[:space:]]*//' | grep -o '[0-9]*' | head -1 || echo "0")
  output_tokens=$(grep '"output_tokens"' "$log_file" 2>/dev/null | tail -1 | sed 's/.*"output_tokens":[[:space:]]*//' | grep -o '[0-9]*' | head -1 || echo "0")

  if [ -z "$input_tokens" ] || [ "$input_tokens" = "0" ]; then return; fi

  TOTAL_INPUT_TOKENS=$((TOTAL_INPUT_TOKENS + input_tokens))
  TOTAL_OUTPUT_TOKENS=$((TOTAL_OUTPUT_TOKENS + output_tokens))

  local model price_in price_out iter_cost
  model=$(get_adaptive_model "$PHASE")
  if [ "$model" = "$OPUS_MODEL" ]; then
    price_in="$OPUS_INPUT_PRICE"
    price_out="$OPUS_OUTPUT_PRICE"
  else
    price_in="$SONNET_INPUT_PRICE"
    price_out="$SONNET_OUTPUT_PRICE"
  fi

  iter_cost=$(awk -v it="$input_tokens" -v pi="$price_in" -v ot="$output_tokens" -v po="$price_out" \
    'BEGIN {printf "%.4f", it * pi + ot * po}' 2>/dev/null || echo "0")
  ESTIMATED_COST=$(awk -v ec="$ESTIMATED_COST" -v ic="$iter_cost" \
    'BEGIN {printf "%.4f", ec + ic}' 2>/dev/null || echo "0")

  echo "$(date -Iseconds) phase=$PHASE iter=$ITERATION model=$model in=$input_tokens out=$output_tokens cost=\$$iter_cost cumulative=\$$ESTIMATED_COST item=$CURRENT_ITEM" >> "$COST_LOG"
}

# ─── Budget enforcement ──────────────────────────────────────────
check_budget() {
  if [ "$BUDGET_USD" = "0" ]; then return 0; fi

  if awk -v ec="$ESTIMATED_COST" -v bu="$BUDGET_USD" 'BEGIN {exit (ec >= bu) ? 0 : 1}' 2>/dev/null; then
    echo -e "${RED}[BUDGET] Exceeded \$${BUDGET_USD} budget (spent: \$${ESTIMATED_COST}). Stopping.${NC}"
    log_phase "BUDGET_EXCEEDED" "budget=$BUDGET_USD spent=$ESTIMATED_COST"
    return 1
  fi

  if awk -v ec="$ESTIMATED_COST" -v bu="$BUDGET_USD" 'BEGIN {exit (ec >= bu * 0.8) ? 0 : 1}' 2>/dev/null; then
    echo -e "${YELLOW}[BUDGET] Warning: \$${ESTIMATED_COST} / \$${BUDGET_USD} (80%+ used)${NC}"
  fi

  return 0
}

# ─── Logging ──────────────────────────────────────────────────────
log_phase() {
  echo "$(date -Iseconds) event=$1 $2" >> "$PHASE_LOG"
}

log_metrics() {
  echo "$(date -Iseconds) metric=$1 context=$2 value=$3 detail=${4:-}" >> "$METRICS_LOG"
}

# ─── Banner ──────────────────────────────────────────────────────
print_banner() {
  echo ""
  echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║       RALPHTON HARNESS v2 — Autonomous Loop              ║${NC}"
  echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════╝${NC}"
  echo -e "  Phase:      ${BOLD}$PHASE${NC}"
  echo -e "  Model:      ${BOLD}$(get_model "$PHASE")${NC} (adaptive in build)"
  echo -e "  Branch:     ${BOLD}$BRANCH${NC}"
  echo -e "  Max iter:   ${BOLD}$(get_max_iter "$PHASE")${NC}"
  echo -e "  Stuck:      ${BOLD}$MAX_STUCK${NC} (circuit) / ${BOLD}$PREDICTIVE_STUCK${NC} (predictive)"
  echo -e "  Parallel:   ${BOLD}$MAX_PARALLEL${NC} max workers"
  echo -e "  Convergence:${BOLD} $CONVERGENCE_THRESHOLD${NC} (relaxed) / ${BOLD}$AMBIGUITY_THRESHOLD${NC} (standard)"
  [ "$BUDGET_USD" != "0" ] && echo -e "  Budget:     ${BOLD}\$${BUDGET_USD}${NC}"
  [ -f "$CONFIG_FILE" ] && echo -e "  Config:     ${BOLD}$CONFIG_FILE${NC}"
  [ -f "LEARNINGS.md" ] && echo -e "  Learnings:  ${BOLD}$(wc -l < LEARNINGS.md | tr -d ' ') lines${NC}"
  echo ""
}

print_iteration_header() {
  local elapsed=$(($(date +%s) - START_TIME))
  local hours=$((elapsed / 3600))
  local minutes=$(( (elapsed % 3600) / 60 ))
  local secs=$((elapsed % 60))
  local icon
  icon=$(get_phase_icon "$PHASE")
  local model
  model=$(get_adaptive_model "$PHASE")

  echo ""
  echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
  echo -e " ${icon} Phase: ${BOLD}${PHASE}${NC} | Iter: ${BOLD}${ITERATION}${NC}/$(get_max_iter "$PHASE") | Total: ${BOLD}${TOTAL_ITERATION}${NC} | Stuck: ${STUCK_COUNT}/${MAX_STUCK}"
  echo -e " Time: ${hours}h${minutes}m${secs}s | Model: ${BOLD}${model}${NC} | Cost: \$${ESTIMATED_COST}"
  if [ "$PHASE" = "build" ] && [ -n "$CURRENT_ITEM" ]; then
    echo -e " Item: ${BOLD}$CURRENT_ITEM${NC} | Fails: ${ITEM_FAIL_COUNT} | Escalated: ${ESCALATED}"
  fi
  echo -e "${BOLD}═══════════════════════════════════════════════════════════${NC}"
  echo ""
}

# ─── Validate prerequisites ──────────────────────────────────────
validate_phase() {
  local prompt_file="PROMPT_${PHASE}.md"
  if [ ! -f "$prompt_file" ]; then
    echo -e "${RED}ERROR: $prompt_file not found${NC}"
    exit 1
  fi

  case "$PHASE" in
    socratic)
      if [ ! -d "specs" ] || [ -z "$(ls -A specs/ 2>/dev/null)" ]; then
        echo -e "${RED}ERROR: specs/ directory is empty. Write your specs first!${NC}"
        exit 1
      fi
      ;;
    plan)
      if [ ! -f "CLARITY_LOG.md" ]; then
        echo -e "${YELLOW}WARNING: No CLARITY_LOG.md found.${NC}"
      fi
      ;;
    build)
      if [ ! -f "IMPLEMENTATION_PLAN.md" ]; then
        echo -e "${YELLOW}WARNING: No IMPLEMENTATION_PLAN.md found.${NC}"
      fi
      ;;
  esac
}

# ─── Main ────────────────────────────────────────────────────────
load_checkpoint "$@"
print_banner
validate_phase
log_phase "START" "phase=$PHASE version=v2"
LAST_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "none")

while true; do
  # ─── Save checkpoint every iteration ────────────────────────
  save_checkpoint

  # ─── Check phase completion ────────────────────────────────
  if [ "$PHASE" = "DONE" ]; then
    echo ""
    echo -e "${GREEN}${BOLD}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}${BOLD}║                    HARNESS COMPLETE                       ║${NC}"
    echo -e "${GREEN}${BOLD}╚═══════════════════════════════════════════════════════════╝${NC}"
    ELAPSED=$(($(date +%s) - START_TIME))
    echo -e "  Total iterations: ${BOLD}${TOTAL_ITERATION}${NC}"
    echo -e "  Total time:       ${BOLD}$((ELAPSED / 3600))h $(( (ELAPSED % 3600) / 60 ))m $((ELAPSED % 60))s${NC}"
    echo -e "  Total tokens:     ${BOLD}in=${TOTAL_INPUT_TOKENS} out=${TOTAL_OUTPUT_TOKENS}${NC}"
    echo -e "  Estimated cost:   ${BOLD}\$${ESTIMATED_COST}${NC}"
    [ -f "LEARNINGS.md" ] && echo -e "  Learnings:        ${BOLD}$(grep -c '### Learning:' LEARNINGS.md 2>/dev/null || echo 0) entries${NC}"
    log_phase "COMPLETE" "total_iter=$TOTAL_ITERATION cost=$ESTIMATED_COST"
    rm -f "$STATE_FILE"
    break
  fi

  # ─── Check budget ──────────────────────────────────────────
  if ! check_budget; then
    save_checkpoint
    break
  fi

  # ─── Check iteration limit ─────────────────────────────────
  MAX_ITER_CUR=$(get_max_iter "$PHASE")
  if [ "$ITERATION" -ge "$MAX_ITER_CUR" ]; then
    echo -e "${YELLOW}[MAX ITER] Reached $MAX_ITER_CUR iterations in phase: $PHASE${NC}"
    log_phase "MAX_ITER" "phase=$PHASE iter=$ITERATION"
    PHASE=$(next_phase "$PHASE")
    ITERATION=0
    STUCK_COUNT=0
    CURRENT_ITEM=""
    ITEM_FAIL_COUNT=0
    ESCALATED=false
    validate_phase
    continue
  fi

  # ─── v2: Try parallel build at start of build phase ─────────
  if [ "$PHASE" = "build" ] && [ "$ITERATION" -eq 0 ]; then
    if try_parallel_build; then
      if should_transition; then
        NEXT_P=$(next_phase "$PHASE")
        echo -e "${GREEN}[TRANSITION] ${PHASE} -> ${NEXT_P} (after parallel build)${NC}"
        log_phase "TRANSITION" "from=$PHASE to=$NEXT_P parallel=true"
        PHASE="$NEXT_P"
        ITERATION=0
        STUCK_COUNT=0
        CURRENT_ITEM=""
        ITEM_FAIL_COUNT=0
        ESCALATED=false
        if [ "$PHASE" != "DONE" ]; then validate_phase; fi
        continue
      fi
      echo -e "${CYAN}[PARALLEL] Remaining items will be built sequentially${NC}"
    fi
  fi

  # ─── v2: Detect current build item ─────────────────────────
  detect_current_item

  # ─── Print header ──────────────────────────────────────────
  print_iteration_header

  # ─── Run Claude ─────────────────────────────────────────────
  CUR_MODEL=$(get_adaptive_model "$PHASE")
  CUR_PROMPT="PROMPT_${PHASE}.md"
  CUR_LOG="$LOG_DIR/${PHASE}_iter${ITERATION}_$(date +%Y%m%d_%H%M%S).log"

  # v2: Inject learnings into build prompt
  if [ "$PHASE" = "build" ]; then
    {
      inject_learnings
      cat "$CUR_PROMPT"
    } | claude -p \
      $PERMISSION_MODE \
      --output-format "$OUTPUT_FORMAT" \
      --model "$CUR_MODEL" \
      --verbose 2>&1 | tee "$CUR_LOG" || true
  else
    cat "$CUR_PROMPT" | claude -p \
      $PERMISSION_MODE \
      --output-format "$OUTPUT_FORMAT" \
      --model "$CUR_MODEL" \
      --verbose 2>&1 | tee "$CUR_LOG" || true
  fi

  ITERATION=$((ITERATION + 1))
  TOTAL_ITERATION=$((TOTAL_ITERATION + 1))

  # ─── Track cost ─────────────────────────────────────────────
  track_cost "$CUR_LOG"

  # ─── v2: Predictive check ──────────────────────────────────
  predictive_check "$CUR_LOG"

  # ─── Check transition ──────────────────────────────────────
  if should_transition; then
    NEXT_P=$(next_phase "$PHASE")
    echo -e "${GREEN}[TRANSITION] ${PHASE} -> ${NEXT_P}${NC}"
    log_phase "TRANSITION" "from=$PHASE to=$NEXT_P iter=$ITERATION"
    PHASE="$NEXT_P"
    ITERATION=0
    STUCK_COUNT=0
    CURRENT_ITEM=""
    ITEM_FAIL_COUNT=0
    ESCALATED=false
    if [ "$PHASE" != "DONE" ]; then
      validate_phase
    fi
    continue
  fi

  # ─── Circuit breaker ───────────────────────────────────────
  if ! check_circuit_breaker; then
    if ! recover_from_stuck; then
      echo -e "${RED}[HARNESS] Unable to recover. Stopping.${NC}"
      log_phase "ABORT" "unrecoverable stuck"
      save_checkpoint
      break
    fi
    continue
  fi

  # ─── Push changes ──────────────────────────────────────────
  git push origin "$BRANCH" 2>/dev/null || true

done

echo ""
echo -e "${BOLD}Logs:      $LOG_DIR/${NC}"
echo -e "${BOLD}Cost:      cat $COST_LOG${NC}"
echo -e "${BOLD}Metrics:   cat $METRICS_LOG${NC}"
echo -e "${BOLD}State:     cat $STATE_FILE${NC}"
[ -f "LEARNINGS.md" ] && echo -e "${BOLD}Learnings: cat LEARNINGS.md${NC}"
