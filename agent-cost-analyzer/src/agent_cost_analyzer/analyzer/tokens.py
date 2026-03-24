"""Token usage analysis."""
from __future__ import annotations

import math
from collections import defaultdict

from agent_cost_analyzer.models import (
    AnomalyEntry,
    CostEntry,
    EscalationEvent,
    ModelTokenData,
    PhaseTokenData,
    TokenAnalysis,
)


def _model_rank(model: str) -> int:
    """Return cost rank for a model name (higher = more expensive).

    Returns -1 for unknown models (suppresses escalation detection).
    """
    name = model.lower()
    if "haiku" in name:
        return 0
    if "sonnet" in name:
        return 1
    if "opus" in name:
        return 2
    return -1


def analyze_tokens(entries: list[CostEntry]) -> TokenAnalysis:
    """Analyze token usage across all cost log entries.

    Computes per-phase and per-model token totals, model escalation events
    (cheaper → more expensive on same item), and per-phase anomalies using
    a 3σ threshold (population stddev, requires ≥3 entries per phase).
    """
    if not entries:
        return TokenAnalysis()

    total_input = sum(e.input_tokens for e in entries)
    total_output = sum(e.output_tokens for e in entries)
    io_ratio = total_output / total_input if total_input > 0 else 0.0

    # per-phase token totals
    by_phase: dict[str, PhaseTokenData] = defaultdict(PhaseTokenData)
    for e in entries:
        p = by_phase[e.phase]
        p.input_tokens += e.input_tokens
        p.output_tokens += e.output_tokens
        p.count += 1

    # per-model token totals
    by_model: dict[str, ModelTokenData] = defaultdict(ModelTokenData)
    for e in entries:
        m = by_model[e.model]
        m.input_tokens += e.input_tokens
        m.output_tokens += e.output_tokens
        m.count += 1

    # escalation detection: consecutive entries on the same item where model
    # changes from a cheaper to a more expensive tier
    item_entries: dict[int, list[CostEntry]] = defaultdict(list)
    for e in entries:
        if e.item is not None:
            item_entries[e.item].append(e)

    escalations: list[EscalationEvent] = []
    for item_list in item_entries.values():
        item_list.sort(key=lambda x: x.timestamp)
        for i in range(len(item_list) - 1):
            from_entry = item_list[i]
            to_entry = item_list[i + 1]
            if from_entry.model != to_entry.model:
                from_rank = _model_rank(from_entry.model)
                to_rank = _model_rank(to_entry.model)
                if from_rank >= 0 and to_rank > from_rank:
                    escalations.append(
                        EscalationEvent(
                            item=from_entry.item,  # type: ignore[arg-type]
                            iteration=to_entry.iteration,
                            from_model=from_entry.model,
                            to_model=to_entry.model,
                        )
                    )

    # anomaly detection: 3σ threshold per phase (population stddev)
    phase_totals: dict[str, list[tuple[int, CostEntry]]] = defaultdict(list)
    for e in entries:
        phase_totals[e.phase].append((e.input_tokens + e.output_tokens, e))

    anomalies: list[AnomalyEntry] = []
    for phase, token_entry_list in phase_totals.items():
        if len(token_entry_list) < 3:
            continue
        totals = [t for t, _ in token_entry_list]
        mean = sum(totals) / len(totals)
        variance = sum((t - mean) ** 2 for t in totals) / len(totals)
        stddev = math.sqrt(variance)
        threshold = mean + 3 * stddev
        for total_tokens, e in token_entry_list:
            if total_tokens > threshold:
                anomalies.append(
                    AnomalyEntry(
                        phase=phase,
                        iteration=e.iteration,
                        actual_tokens=total_tokens,
                        threshold=threshold,
                    )
                )

    return TokenAnalysis(
        total_input=total_input,
        total_output=total_output,
        io_ratio=io_ratio,
        by_phase=dict(by_phase),
        by_model=dict(by_model),
        escalations=escalations,
        anomalies=anomalies,
    )
