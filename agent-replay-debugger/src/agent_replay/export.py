"""JSON export for agent session replay data.

Schema per clarity Round 9:
{
  "project": str,
  "total_iterations": int,
  "total_cost": str,
  "total_duration": str,
  "iterations": [
    {
      "number": int,
      "phase": str,
      "status": str,
      "cost_total": str,
      "tokens_in": int,
      "tokens_out": int,
      "duration": str,
      "items_done": list[str],
      "events": [{"timestamp": str, "event_type": str, "data": {...}}],
      "git_commits": [{"hash": str, "message": str, "timestamp": str}]
    }
  ]
}

Decimal values exported as strings; timestamps as ISO 8601 strings.
"""
from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from agent_replay.models import (
    CostEntry,
    GitCommit,
    Iteration,
    MetricsEntry,
    PhaseEntry,
    SessionBlock,
    TimelineEvent,
)


def _serialize_event_data(
    data: CostEntry | PhaseEntry | GitCommit | SessionBlock | MetricsEntry,
) -> dict:
    """Serialize event-specific data to a JSON-safe dict."""
    if isinstance(data, CostEntry):
        return {
            "type": "cost",
            "timestamp": data.timestamp.isoformat(),
            "phase": data.phase,
            "iter": data.iter,
            "model": data.model,
            "tokens_in": data.tokens_in,
            "tokens_out": data.tokens_out,
            "cost": str(data.cost),
            "cumulative": str(data.cumulative),
            "item": data.item,
        }
    if isinstance(data, PhaseEntry):
        return {
            "type": "phase",
            "timestamp": data.timestamp.isoformat(),
            "event_type": data.event_type,
            "params": data.params,
        }
    if isinstance(data, GitCommit):
        return {
            "type": "commit",
            "hash": data.hash,
            "message": data.message,
            "timestamp": data.timestamp.isoformat(),
        }
    if isinstance(data, SessionBlock):
        return {
            "type": "session",
            "timestamp": data.timestamp.isoformat(),
            "items_completed": data.items_completed,
        }
    # MetricsEntry
    return {
        "type": "metrics",
        "timestamp": data.timestamp.isoformat(),
        "metric": data.metric,
        "context": data.context,
        "value": data.value,
        "detail": data.detail,
    }


def _serialize_event(event: TimelineEvent) -> dict:
    return {
        "timestamp": event.timestamp.isoformat(),
        "event_type": event.event_type,
        "data": _serialize_event_data(event.data),
    }


def _serialize_iteration(it: Iteration) -> dict:
    return {
        "number": it.number,
        "phase": it.phase,
        "status": it.status,
        "cost_total": str(it.cost_total),
        "tokens_in": it.tokens_in,
        "tokens_out": it.tokens_out,
        "duration": str(it.duration),
        "items_done": it.items_done,
        "events": [_serialize_event(e) for e in it.events],
        "git_commits": [
            {
                "hash": c.hash,
                "message": c.message,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in it.git_commits
        ],
    }


def export_json(
    iterations: list[Iteration],
    output_path: Path,
    *,
    project: str = "",
) -> None:
    """Serialize iterations to pretty-printed JSON at output_path.

    Top-level document includes aggregate metadata (Round 9 schema).
    Decimal → str, datetime → ISO 8601, timedelta → str.
    """
    total_cost = sum((it.cost_total for it in iterations), Decimal("0"))
    total_duration = sum((it.duration for it in iterations), timedelta())
    doc = {
        "project": project,
        "total_iterations": len(iterations),
        "total_cost": str(total_cost),
        "total_duration": str(total_duration),
        "iterations": [_serialize_iteration(it) for it in iterations],
    }
    output_path.write_text(json.dumps(doc, indent=2))
