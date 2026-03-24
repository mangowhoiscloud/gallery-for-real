"""trend command: time-series view of binding metrics across all versions."""

from pathlib import Path

from prompt_vc.storage import is_initialized, read_index, read_yaml, store_path


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


def _load_latest_bindings(bindings_dir: Path, version: str) -> dict[str, dict]:
    """Load the latest run per benchmark for a version.

    Returns:
        Mapping of benchmark name -> binding data dict (latest run only).
    """
    files = list(bindings_dir.glob(f"{version}_run*.yaml"))
    latest: dict[str, tuple[int, dict]] = {}
    for f in files:
        try:
            run_num = int(f.stem.split("_run")[-1])
        except (ValueError, IndexError):
            continue
        data = read_yaml(f)
        bname = data.get("benchmark", "")
        if not bname:
            continue
        if bname not in latest or run_num > latest[bname][0]:
            latest[bname] = (run_num, data)
    return {bname: d for bname, (_, d) in latest.items()}


def _fmt_value(val: object) -> str:
    if val == "—":
        return "—"
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)


def _format_benchmark_table(
    benchmark: str,
    version_ids: list[str],
    bindings_by_version: dict[str, dict],
) -> str:
    """Format a trend table for a single benchmark.

    Args:
        benchmark: Benchmark name.
        version_ids: All version IDs in chronological order.
        bindings_by_version: version_id -> binding data (may be missing entries).

    Returns:
        Formatted table string.
    """
    # Gather all metric keys across all bindings for this benchmark
    all_metrics: set[str] = set()
    for vid in version_ids:
        data = bindings_by_version.get(vid)
        if data:
            all_metrics |= set((data.get("metrics") or {}).keys())

    col_w = 14
    lines = [f"Benchmark: {benchmark}"]
    header = f"{'Metric':<20}" + "".join(f" {v:<{col_w}}" for v in version_ids)
    lines.append(header)
    lines.append("-" * len(header))

    for key in sorted(all_metrics):
        row = f"{key:<20}"
        for vid in version_ids:
            data = bindings_by_version.get(vid)
            if data is None:
                val: object = "—"
            else:
                val = (data.get("metrics") or {}).get(key, "—")
            row += f" {_fmt_value(val):<{col_w}}"
        lines.append(row)

    return "\n".join(lines)


def trend(cwd: Path) -> str:
    """Show metric trends across all versions with bindings.

    Args:
        cwd: Working directory containing .prompt-vc/ store.

    Returns:
        Formatted trend string.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)
    if not index.versions:
        return "No versions yet. Run 'prompt-vc snapshot' first."

    bindings_dir = store_path(cwd) / "bindings"
    version_ids = [v.version for v in index.versions]  # chronological order

    # Load bindings for each version, keyed by benchmark
    # Structure: benchmark -> version_id -> binding_data
    benchmark_data: dict[str, dict[str, dict]] = {}
    for vid in version_ids:
        bindings = _load_latest_bindings(bindings_dir, vid)
        for bname, data in bindings.items():
            if bname not in benchmark_data:
                benchmark_data[bname] = {}
            benchmark_data[bname][vid] = data

    if not benchmark_data:
        return "No binding data found. Run 'prompt-vc bind' to attach results to versions."

    output_parts = ["=== Metric Trend ==="]

    for bname in sorted(benchmark_data):
        output_parts.append("")
        output_parts.append(
            _format_benchmark_table(bname, version_ids, benchmark_data[bname])
        )

    return "\n".join(output_parts)
