"""Report generation package."""

from __future__ import annotations

import json
from pathlib import Path

from agent_eval.models import RunResult
from agent_eval.report.html import generate_html_report
from agent_eval.report.json_report import generate_json_report
from agent_eval.report.markdown import generate_markdown_report


def discover_results(results_dir: Path | str) -> list[RunResult]:
    """Recursively find result.json files and deserialize to a RunResult list.

    Each result.json may contain either:
    - A bare RunResult dict (produced by runner.py per-run serialization), or
    - A full report dict with a "results" key (produced by generate_json_report).
    """
    results_dir = Path(results_dir)
    run_results: list[RunResult] = []
    for path in sorted(results_dir.rglob("result.json")):
        with open(path) as f:
            data = json.load(f)
        if "results" in data:
            for item in data["results"]:
                run_results.append(RunResult.from_dict(item))
        else:
            run_results.append(RunResult.from_dict(data))
    return run_results


def generate_report(
    results: list[RunResult],
    output_path: Path | str,
    format: str = "json",
) -> None:
    """Dispatch to the appropriate report generator based on format."""
    if format == "json":
        generate_json_report(results, output_path)
    elif format == "markdown":
        generate_markdown_report(results, output_path)
    elif format == "html":
        generate_html_report(results, output_path)
    else:
        raise ValueError(f"Unknown format: {format!r}. Supported formats: json, markdown, html")
