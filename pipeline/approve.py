"""CLI: mark a version under output/<job>/versions/NNN as approved."""

from __future__ import annotations

import argparse
import sys

from pipeline.bootstrap import add_job_argument, bootstrap_job
from pipeline.versioning import get_approved_version_dir, list_version_numbers, mark_approved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Mark output/<job>/versions/NNN as approved for production promotion"
    )
    add_job_argument(parser)
    parser.add_argument(
        "--version",
        default=None,
        help="Version number or folder name (e.g. 1, 001, 003)",
    )
    parser.add_argument("--notes", default="", help="Optional approval notes")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing version numbers and exit",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    ctx = bootstrap_job(args.job, force_draft=True)

    if args.list:
        nums = list_version_numbers(ctx)
        print(f"Job {ctx.job_id} versions: {nums or '(none)'}")
        approved = get_approved_version_dir(ctx)
        print(f"Approved: {approved.name if approved else '(none)'}")
        return 0

    if not args.version:
        parser.error("--version is required unless --list is set")

    path = mark_approved(args.version, ctx, notes=args.notes)
    print(f"Wrote {path}")
    print(f"Approved version: {args.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
