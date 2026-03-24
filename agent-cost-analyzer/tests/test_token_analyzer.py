"""Tests for the token usage analyzer."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from agent_cost_analyzer.analyzer.tokens import _model_rank, analyze_tokens
from agent_cost_analyzer.models import (
    AnomalyEntry,
    CostEntry,
    EscalationEvent,
    ModelTokenData,
    PhaseTokenData,
    TokenAnalysis,
)
from agent_cost_analyzer.parser.cost_log import parse_cost_log


def _make_entry(
    phase: str,
    iteration: int,
    model: str,
    input_tokens: int,
    output_tokens: int,
    item: int | None = None,
    ts_hour: int = 10,
) -> CostEntry:
    """Helper to build a CostEntry for testing."""
    return CostEntry(
        timestamp=datetime(2026, 3, 19, ts_hour, 0, 0, tzinfo=timezone.utc),
        phase=phase,
        iteration=iteration,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=Decimal("0.10"),
        cumulative=Decimal("0.10"),
        item=item,
    )


# ---------------------------------------------------------------------------
# Empty input
# ---------------------------------------------------------------------------


def test_empty_input_returns_zero_analysis() -> None:
    result = analyze_tokens([])
    assert isinstance(result, TokenAnalysis)
    assert result.total_input == 0
    assert result.total_output == 0
    assert result.io_ratio == 0.0
    assert result.by_phase == {}
    assert result.by_model == {}
    assert result.escalations == []
    assert result.anomalies == []


# ---------------------------------------------------------------------------
# Single entry
# ---------------------------------------------------------------------------


def test_single_entry() -> None:
    entry = _make_entry("build", 1, "claude-sonnet-4-5", 1000, 500, item=1)
    result = analyze_tokens([entry])
    assert result.total_input == 1000
    assert result.total_output == 500
    assert result.io_ratio == pytest.approx(0.5)
    assert "build" in result.by_phase
    assert result.by_phase["build"].count == 1
    assert result.by_phase["build"].input_tokens == 1000
    assert result.by_phase["build"].output_tokens == 500
    assert "claude-sonnet-4-5" in result.by_model
    assert result.escalations == []
    # single entry → less than 3 in any phase → no anomaly
    assert result.anomalies == []


# ---------------------------------------------------------------------------
# Fixture-based integration
# ---------------------------------------------------------------------------

FIXTURE_COST_LOG = Path(__file__).parent / "fixtures" / "cost.log"

# Computed totals from the fixture:
#   socratic(sonnet):  in=12563, out=8734
#   plan(opus):        in=15234, out=9876
#   build(various):    in=5234+2345+8765+4321+8543+6789+3456+2987 = 42440
#                      out=3456+1234+5432+2109+35897+5432+2109+1876 = 57545
#   verify(sonnet):    in=13456, out=9234
EXPECTED_TOTAL_IN = 12563 + 15234 + 42440 + 13456  # 83693
EXPECTED_TOTAL_OUT = 8734 + 9876 + 57545 + 9234  # 85389


def test_fixture_total_tokens() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    assert result.total_input == EXPECTED_TOTAL_IN
    assert result.total_output == EXPECTED_TOTAL_OUT


def test_fixture_io_ratio() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    expected = EXPECTED_TOTAL_OUT / EXPECTED_TOTAL_IN
    assert result.io_ratio == pytest.approx(expected, rel=1e-6)
    assert result.io_ratio > 0


def test_fixture_by_phase_keys() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    assert set(result.by_phase.keys()) == {"socratic", "plan", "build", "verify"}


def test_fixture_by_phase_build_totals() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    build = result.by_phase["build"]
    assert isinstance(build, PhaseTokenData)
    assert build.input_tokens == 42440
    assert build.output_tokens == 57545
    assert build.count == 8


def test_fixture_by_phase_socratic() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    s = result.by_phase["socratic"]
    assert s.input_tokens == 12563
    assert s.output_tokens == 8734
    assert s.count == 1


def test_fixture_by_model_keys() -> None:
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    assert set(result.by_model.keys()) == {"claude-sonnet-4-5", "claude-opus-4-5"}


def test_fixture_by_model_sonnet() -> None:
    # sonnet entries: socratic(iter1), build(iter1,2,4), verify(iter1) → 5 entries
    # in: 12563+5234+2345+4321+13456 = 37919
    # out: 8734+3456+1234+2109+9234 = 24767
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    sonnet = result.by_model["claude-sonnet-4-5"]
    assert isinstance(sonnet, ModelTokenData)
    assert sonnet.input_tokens == 37919
    assert sonnet.output_tokens == 24767
    assert sonnet.count == 5


def test_fixture_by_model_opus() -> None:
    # opus entries: plan(iter1), build(iter3,5,6,7,8) → 6 entries
    # in: 15234+8765+8543+6789+3456+2987 = 45774
    # out: 9876+5432+35897+5432+2109+1876 = 60622
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    opus = result.by_model["claude-opus-4-5"]
    assert opus.input_tokens == 45774
    assert opus.output_tokens == 60622
    assert opus.count == 6


def test_fixture_no_escalations() -> None:
    # No item has a model change in the fixture (item 5 stays all opus)
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    assert result.escalations == []


def test_fixture_anomalies_is_list() -> None:
    # Build phase has 8 entries; iter=5 has 44440 total tokens vs ~12498 mean.
    # With population stddev the threshold is ~50155, so iter=5 may or may not flag.
    entries = parse_cost_log(FIXTURE_COST_LOG)
    result = analyze_tokens(entries)
    assert isinstance(result.anomalies, list)
    for a in result.anomalies:
        assert isinstance(a, AnomalyEntry)
        assert a.actual_tokens > a.threshold


# ---------------------------------------------------------------------------
# Escalation detection
# ---------------------------------------------------------------------------


def test_escalation_sonnet_to_opus_same_item() -> None:
    entries = [
        _make_entry("build", 1, "claude-sonnet-4-5", 1000, 500, item=3, ts_hour=10),
        _make_entry("build", 2, "claude-opus-4-5", 2000, 1000, item=3, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert len(result.escalations) == 1
    esc = result.escalations[0]
    assert isinstance(esc, EscalationEvent)
    assert esc.item == 3
    assert esc.iteration == 2
    assert esc.from_model == "claude-sonnet-4-5"
    assert esc.to_model == "claude-opus-4-5"


def test_no_escalation_opus_to_sonnet() -> None:
    # downgrade is not an escalation
    entries = [
        _make_entry("build", 1, "claude-opus-4-5", 2000, 1000, item=2, ts_hour=10),
        _make_entry("build", 2, "claude-sonnet-4-5", 1000, 500, item=2, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert result.escalations == []


def test_no_escalation_same_model() -> None:
    entries = [
        _make_entry("build", 1, "claude-sonnet-4-5", 1000, 500, item=1, ts_hour=10),
        _make_entry("build", 2, "claude-sonnet-4-5", 1000, 500, item=1, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert result.escalations == []


def test_no_escalation_different_items() -> None:
    # model changes across items should not register as escalation
    entries = [
        _make_entry("build", 1, "claude-sonnet-4-5", 1000, 500, item=1, ts_hour=10),
        _make_entry("build", 2, "claude-opus-4-5", 2000, 1000, item=2, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert result.escalations == []


def test_escalation_haiku_to_opus() -> None:
    entries = [
        _make_entry("build", 1, "claude-haiku-4-5", 500, 200, item=4, ts_hour=10),
        _make_entry("build", 2, "claude-opus-4-5", 2000, 1000, item=4, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert len(result.escalations) == 1
    assert result.escalations[0].from_model == "claude-haiku-4-5"
    assert result.escalations[0].to_model == "claude-opus-4-5"


def test_multiple_escalations_same_item() -> None:
    # haiku → sonnet → opus in same item = 2 escalations
    entries = [
        _make_entry("build", 1, "claude-haiku-4-5", 500, 200, item=1, ts_hour=10),
        _make_entry("build", 2, "claude-sonnet-4-5", 1000, 500, item=1, ts_hour=11),
        _make_entry("build", 3, "claude-opus-4-5", 2000, 1000, item=1, ts_hour=12),
    ]
    result = analyze_tokens(entries)
    assert len(result.escalations) == 2


def test_escalation_unknown_model_not_counted() -> None:
    # unknown model names should not produce escalations
    entries = [
        _make_entry("build", 1, "model-x", 1000, 500, item=7, ts_hour=10),
        _make_entry("build", 2, "claude-opus-4-5", 2000, 1000, item=7, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert result.escalations == []


def test_no_escalation_for_non_build_entries() -> None:
    # entries with item=None should not be considered for escalation
    entries = [
        _make_entry("socratic", 1, "claude-sonnet-4-5", 1000, 500, item=None),
        _make_entry("plan", 1, "claude-opus-4-5", 2000, 1000, item=None),
    ]
    result = analyze_tokens(entries)
    assert result.escalations == []


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------


def _build_phase_entries(totals: list[int]) -> list[CostEntry]:
    """Create build-phase entries with given total tokens (split 60/40 in/out)."""
    entries = []
    for i, total in enumerate(totals):
        in_tok = int(total * 0.6)
        out_tok = total - in_tok
        entries.append(
            CostEntry(
                timestamp=datetime(2026, 3, 19, 10 + i, 0, 0, tzinfo=timezone.utc),
                phase="build",
                iteration=i + 1,
                model="claude-sonnet-4-5",
                input_tokens=in_tok,
                output_tokens=out_tok,
                cost=Decimal("0.10"),
                cumulative=Decimal("0.10"),
                item=i + 1,
            )
        )
    return entries


def test_anomaly_detected_with_clear_outlier() -> None:
    # With n >= 10 normal values, any M > C is guaranteed to be detected by
    # population 3σ: threshold < M iff n > 9 (derived algebraically).
    # Use 10 uniform entries of 100 + one clear outlier.
    normal = [100] * 10
    outlier = 5000
    entries = _build_phase_entries(normal + [outlier])
    result = analyze_tokens(entries)
    assert len(result.anomalies) == 1
    anomaly = result.anomalies[0]
    assert isinstance(anomaly, AnomalyEntry)
    assert anomaly.phase == "build"
    assert anomaly.actual_tokens == outlier
    assert anomaly.actual_tokens > anomaly.threshold


def test_no_anomaly_when_values_uniform() -> None:
    entries = _build_phase_entries([100, 100, 100, 100, 100])
    result = analyze_tokens(entries)
    # stddev=0, threshold=mean → no entry can exceed it
    assert result.anomalies == []


def test_no_anomaly_when_fewer_than_3_entries_in_phase() -> None:
    entries = [
        _make_entry("socratic", 1, "claude-sonnet-4-5", 100000, 100000),
    ]
    result = analyze_tokens(entries)
    assert result.anomalies == []


def test_no_anomaly_when_exactly_2_entries_in_phase() -> None:
    entries = [
        _make_entry("socratic", 1, "claude-sonnet-4-5", 100000, 100000, ts_hour=10),
        _make_entry("socratic", 2, "claude-sonnet-4-5", 100, 100, ts_hour=11),
    ]
    result = analyze_tokens(entries)
    assert result.anomalies == []


def test_anomaly_threshold_uses_population_stddev() -> None:
    # Build 3 entries: 10, 10, 10000
    # mean = (10+10+10000)/3 = 3340/3 ≈ 3340
    # population variance = ((10-3340)^2 + (10-3340)^2 + (10000-3340)^2) / 3
    # = (2*(-3330)^2 + 6660^2) / 3
    # = (2*11088900 + 44355600) / 3
    # = (22177800 + 44355600) / 3 = 66533400 / 3 = 22177800
    # stddev = sqrt(22177800) ≈ 4709.3
    # threshold = 3340 + 3*4709.3 = 3340 + 14127.9 = 17467.9
    # 10000 < 17467.9 → NOT an anomaly with population stddev
    entries = _build_phase_entries([10, 10, 10000])
    result = analyze_tokens(entries)
    assert result.anomalies == []


def test_anomaly_entry_fields() -> None:
    entries = _build_phase_entries([100] * 10 + [50000])
    result = analyze_tokens(entries)
    assert len(result.anomalies) == 1
    a = result.anomalies[0]
    assert a.phase == "build"
    assert isinstance(a.iteration, int)
    assert isinstance(a.actual_tokens, int)
    assert isinstance(a.threshold, float)


# ---------------------------------------------------------------------------
# Model rank helper
# ---------------------------------------------------------------------------


def test_model_rank_haiku() -> None:
    assert _model_rank("claude-haiku-4-5") == 0


def test_model_rank_sonnet() -> None:
    assert _model_rank("claude-sonnet-4-5") == 1


def test_model_rank_opus() -> None:
    assert _model_rank("claude-opus-4-5") == 2


def test_model_rank_unknown() -> None:
    assert _model_rank("gpt-4o") == -1
    assert _model_rank("") == -1


def test_model_rank_case_insensitive() -> None:
    assert _model_rank("Claude-Opus-4-5") == 2
    assert _model_rank("CLAUDE-SONNET") == 1
