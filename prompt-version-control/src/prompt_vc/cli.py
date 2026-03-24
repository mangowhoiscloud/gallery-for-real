"""CLI entry point for prompt-vc."""

import argparse
import sys
from pathlib import Path


def _cwd() -> Path:
    return Path.cwd()


def _handle_init(args: argparse.Namespace) -> int:
    from prompt_vc.commands.init import AlreadyInitializedError, init

    try:
        init(cwd=_cwd(), prompt_dir=Path(args.dir))
        print(f"Initialized .prompt-vc/ (prompt_dir={args.dir})")
        return 0
    except AlreadyInitializedError as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_snapshot(args: argparse.Namespace) -> int:
    from prompt_vc.commands.snapshot import NoChangesError, NotInitializedError, snapshot

    try:
        meta = snapshot(cwd=_cwd(), message=args.message)
        print(f"Snapshot {meta.version} created: {meta.message}")
        return 0
    except (NotInitializedError, NoChangesError) as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_log(args: argparse.Namespace) -> int:
    from prompt_vc.commands.log import NotInitializedError, log

    try:
        output = log(cwd=_cwd())
        print(output)
        return 0
    except NotInitializedError as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_diff(args: argparse.Namespace) -> int:
    from prompt_vc.commands.diff import NotInitializedError, VersionNotFoundError, diff

    try:
        output = diff(cwd=_cwd(), v1=args.v1, v2=args.v2)
        print(output)
        return 0
    except (NotInitializedError, VersionNotFoundError) as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_checkout(args: argparse.Namespace) -> int:
    from prompt_vc.commands.checkout import (
        NotInitializedError,
        UnsavedChangesError,
        VersionNotFoundError,
        checkout,
    )

    try:
        checkout(cwd=_cwd(), version=args.version, force=args.force)
        print(f"Checked out {args.version}")
        return 0
    except (NotInitializedError, VersionNotFoundError, UnsavedChangesError) as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_bind(args: argparse.Namespace) -> int:
    from prompt_vc.commands.bind import (
        InvalidResultError,
        NotInitializedError,
        VersionNotFoundError,
        bind,
    )

    try:
        meta = bind(cwd=_cwd(), version=args.version, result_file=Path(args.result))
        print(f"Bound {meta.version} to benchmark '{meta.benchmark}'")
        return 0
    except (NotInitializedError, VersionNotFoundError, InvalidResultError) as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_compare(args: argparse.Namespace) -> int:
    from prompt_vc.commands.compare import (
        NoBenchmarksError,
        NotInitializedError,
        VersionNotFoundError,
        compare,
    )
    from prompt_vc.formatters import UnsupportedFormatError, apply_format

    try:
        output = compare(
            cwd=_cwd(),
            v1=args.v1,
            v2=args.v2,
            benchmark=args.benchmark,
        )
        print(apply_format(output, args.format, title=f"compare {args.v1} vs {args.v2}"))
        return 0
    except (NotInitializedError, VersionNotFoundError, NoBenchmarksError) as e:
        print(str(e), file=sys.stderr)
        return 1
    except UnsupportedFormatError as e:
        print(str(e), file=sys.stderr)
        return 1


def _handle_trend(args: argparse.Namespace) -> int:
    from prompt_vc.commands.trend import NotInitializedError, trend
    from prompt_vc.formatters import UnsupportedFormatError, apply_format

    try:
        output = trend(cwd=_cwd())
        print(apply_format(output, args.format, title="trend"))
        return 0
    except NotInitializedError as e:
        print(str(e), file=sys.stderr)
        return 1
    except UnsupportedFormatError as e:
        print(str(e), file=sys.stderr)
        return 1


_HANDLERS = {
    "init": _handle_init,
    "snapshot": _handle_snapshot,
    "log": _handle_log,
    "diff": _handle_diff,
    "checkout": _handle_checkout,
    "bind": _handle_bind,
    "compare": _handle_compare,
    "trend": _handle_trend,
}


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="prompt-vc",
        description="AI prompt version control, A/B testing, and performance tracking.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a .prompt-vc/ store")
    p_init.add_argument(
        "--dir",
        default=".",
        metavar="DIR",
        help="Directory where prompt files live (default: .)",
    )

    # snapshot
    p_snapshot = subparsers.add_parser("snapshot", help="Create a versioned snapshot")
    p_snapshot.add_argument("--message", "-m", required=True, help="Snapshot message")

    # log
    subparsers.add_parser("log", help="List all snapshots")

    # diff
    p_diff = subparsers.add_parser("diff", help="Show diff between two versions")
    p_diff.add_argument("v1", help="First version (e.g. v1)")
    p_diff.add_argument("v2", help="Second version (e.g. v2)")

    # checkout
    p_checkout = subparsers.add_parser(
        "checkout", help="Restore prompt files from a snapshot"
    )
    p_checkout.add_argument("version", help="Version to restore (e.g. v2)")
    p_checkout.add_argument(
        "--force", "-f", action="store_true", help="Overwrite unsaved changes"
    )

    # bind
    p_bind = subparsers.add_parser("bind", help="Attach benchmark results to a version")
    p_bind.add_argument("version", help="Version to bind results to (e.g. v3)")
    p_bind.add_argument(
        "--result", "-r", required=True, metavar="FILE", help="Path to JSON result file"
    )

    # compare
    p_compare = subparsers.add_parser("compare", help="A/B comparison of two versions")
    p_compare.add_argument("v1", help="First version (e.g. v1)")
    p_compare.add_argument("v2", help="Second version (e.g. v2)")
    p_compare.add_argument(
        "--benchmark", "-b", default=None, help="Filter to a specific benchmark"
    )
    p_compare.add_argument(
        "--format",
        default="terminal",
        choices=["terminal", "html", "markdown"],
        help="Output format (default: terminal)",
    )

    # trend
    p_trend = subparsers.add_parser("trend", help="Show metric trends across all versions")
    p_trend.add_argument(
        "--format",
        default="terminal",
        choices=["terminal", "html", "markdown"],
        help="Output format (default: terminal)",
    )

    return parser


def main() -> None:
    """Main entry point for the prompt-vc CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    handler = _HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))
