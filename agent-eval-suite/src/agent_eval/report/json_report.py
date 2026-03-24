"""JSON report generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_eval.models import RunResult


def generate_json_report(results: list[RunResult], output_path: Path | str) -> None:
    """Serialize results to a JSON file with a per-benchmark summary section."""
    output_path = Path(output_path)

    # Aggregate per benchmark
    benchmarks: dict[str, dict[str, Any]] = {}
    for r in results:
        if r.benchmark not in benchmarks:
            benchmarks[r.benchmark] = {
                "agents": [],
                "success_count": 0,
                "total_count": 0,
            }
        benchmarks[r.benchmark]["agents"].append(r.agent)
        benchmarks[r.benchmark]["total_count"] += 1
        if r.success:
            benchmarks[r.benchmark]["success_count"] += 1

    summary: dict[str, Any] = {
        bname: {
            "agents": bdata["agents"],
            "success_count": bdata["success_count"],
            "total_count": bdata["total_count"],
            "success_rate": (
                bdata["success_count"] / bdata["total_count"]
                if bdata["total_count"] > 0
                else 0.0
            ),
        }
        for bname, bdata in benchmarks.items()
    }

    report: dict[str, Any] = {
        "summary": summary,
        "results": [r.to_dict() for r in results],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
