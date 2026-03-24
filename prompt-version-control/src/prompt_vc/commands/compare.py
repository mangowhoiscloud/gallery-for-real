"""compare command: side-by-side A/B comparison of binding metrics between two versions."""

from pathlib import Path

from prompt_vc.storage import is_initialized, read_index, read_yaml, store_path


class NotInitializedError(Exception):
    """Raised when .prompt-vc/ has not been initialized."""


class VersionNotFoundError(Exception):
    """Raised when the specified version does not exist."""


class NoBenchmarksError(Exception):
    """Raised when there are no common benchmarks to compare."""


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
    if isinstance(val, float):
        return f"{val:.4f}"
    return str(val)


def _fmt_delta(v1_val: object, v2_val: object) -> str:
    if isinstance(v1_val, bool) and isinstance(v2_val, bool):
        if v1_val == v2_val:
            return "—"
        return f"{v1_val}→{v2_val}"
    if isinstance(v1_val, (int, float)) and isinstance(v2_val, (int, float)):
        # Avoid treating bool as numeric (bool is subclass of int)
        if isinstance(v1_val, bool) or isinstance(v2_val, bool):
            return "—" if v1_val == v2_val else f"{v1_val}→{v2_val}"
        delta = v2_val - v1_val
        sign = "+" if delta >= 0 else ""
        if isinstance(v1_val, float) or isinstance(v2_val, float):
            pct = (delta / v1_val * 100) if v1_val != 0 else float("nan")
            if pct != pct:  # nan check
                return f"{sign}{delta:.4f}"
            return f"{sign}{delta:.4f} ({sign}{pct:.2f}%)"
        return f"{sign}{delta}"
    if v1_val == v2_val:
        return "—"
    return f"{v1_val}→{v2_val}"


def _is_numeric_improved(v1_val: object, v2_val: object) -> bool | None:
    """Return True if v2 is numerically greater than v1, None if not comparable."""
    if isinstance(v1_val, bool) or isinstance(v2_val, bool):
        return None
    if isinstance(v1_val, (int, float)) and isinstance(v2_val, (int, float)):
        return v2_val > v1_val
    return None


def _format_benchmark_table(
    benchmark: str, v1_id: str, v2_id: str, b1: dict, b2: dict
) -> tuple[str, int, int]:
    """Format one benchmark comparison table.

    Returns:
        (table_str, improved_count, total_numeric_count)
    """
    m1: dict = b1.get("metrics") or {}
    m2: dict = b2.get("metrics") or {}
    all_keys = sorted(set(m1) | set(m2))

    col_w = 14
    lines = [f"Benchmark: {benchmark}"]
    header = f"{'Metric':<20} {v1_id:<{col_w}} {v2_id:<{col_w}} {'Δ'}"
    lines.append(header)
    lines.append("-" * len(header))

    improved = 0
    total_numeric = 0

    for key in all_keys:
        val1 = m1.get(key, "—")
        val2 = m2.get(key, "—")
        delta = _fmt_delta(val1, val2) if val1 != "—" and val2 != "—" else "—"
        result = _is_numeric_improved(val1, val2)
        if result is not None:
            total_numeric += 1
            if result:
                improved += 1
        lines.append(
            f"{key:<20} {_fmt_value(val1):<{col_w}} {_fmt_value(val2):<{col_w}} {delta}"
        )

    return "\n".join(lines), improved, total_numeric


def compare(
    cwd: Path,
    v1: str,
    v2: str,
    benchmark: str | None = None,
) -> str:
    """Compare binding metrics between two prompt versions.

    Args:
        cwd: Working directory containing .prompt-vc/ store.
        v1: First version ID (e.g. "v1").
        v2: Second version ID (e.g. "v2").
        benchmark: Optional benchmark name to filter by.

    Returns:
        Formatted comparison string.

    Raises:
        NotInitializedError: If .prompt-vc/ does not exist.
        VersionNotFoundError: If either version does not exist in the index.
        NoBenchmarksError: If there are no common benchmarks to compare.
    """
    if not is_initialized(cwd):
        raise NotInitializedError(
            f"No .prompt-vc/ found in {cwd}. Run 'prompt-vc init' first."
        )

    index = read_index(cwd)
    version_ids = {v.version for v in index.versions}
    if v1 not in version_ids:
        raise VersionNotFoundError(f"Version '{v1}' not found.")
    if v2 not in version_ids:
        raise VersionNotFoundError(f"Version '{v2}' not found.")

    bindings_dir = store_path(cwd) / "bindings"
    bindings1 = _load_latest_bindings(bindings_dir, v1)
    bindings2 = _load_latest_bindings(bindings_dir, v2)

    common = set(bindings1) & set(bindings2)

    if benchmark is not None:
        if benchmark not in common:
            raise NoBenchmarksError(
                f"Benchmark '{benchmark}' not found in both versions. "
                f"Available common benchmarks: {sorted(common) or 'none'}"
            )
        common = {benchmark}

    if not common:
        raise NoBenchmarksError(
            f"No common benchmarks found between {v1} and {v2}."
        )

    # Find v2 message for "Key Change"
    v2_message = next(
        (vm.message for vm in index.versions if vm.version == v2), ""
    )

    output_parts = [f"=== Prompt A/B Comparison: {v1} vs {v2} ==="]

    total_improved = 0
    total_numeric = 0

    for bname in sorted(common):
        table, improved, numeric = _format_benchmark_table(
            bname, v1, v2, bindings1[bname], bindings2[bname]
        )
        output_parts.append("")
        output_parts.append(table)
        total_improved += improved
        total_numeric += numeric

    if total_numeric > 0:
        output_parts.append("")
        output_parts.append(
            f"Winner: {v2} ({total_improved}/{total_numeric} numeric metrics improved)"
        )

    if v2_message:
        output_parts.append(f'Key Change: "{v2_message}"')

    return "\n".join(output_parts)
