"""Shared CLI bootstrap — require --job and load JobContext.

All entry scripts should::

    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(...)
    add_job_argument(parser)
    # ... other args ...
    args = parser.parse_args()
    ctx = bootstrap_job(args.job)

There is no default job id (Phase B).
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from pipeline.job_context import JobContext, load_job


def add_job_argument(parser: argparse.ArgumentParser) -> None:
    """Add required ``--job JOB_ID`` to an argparse parser."""
    parser.add_argument(
        "--job",
        required=True,
        metavar="JOB_ID",
        help="Job id under input|work|output/<job>/ (required)",
    )


def bootstrap_job(job_id: str, *, reload: bool = False) -> JobContext:
    """Load job and bind ``pipeline.config`` attributes. Exits on empty id."""
    if job_id is None or not str(job_id).strip():
        print("error: --job JOB_ID is required", file=sys.stderr)
        raise SystemExit(2)
    return load_job(str(job_id).strip(), reload=reload)


def parse_and_load_job(
    argv: Sequence[str] | None = None,
    *,
    description: str | None = None,
) -> tuple[argparse.Namespace, JobContext]:
    """Parse argv for ``--job`` (and unknown args kept on namespace via parse_known).

    Suitable for ``python -m pipeline.adjacent_guard --job cefr-companion-2020``.
    """
    parser = argparse.ArgumentParser(description=description)
    add_job_argument(parser)
    args, remainder = parser.parse_known_args(list(argv) if argv is not None else None)
    # Stash unknown tokens for callers that need extra flags
    args._remainder = remainder  # noqa: SLF001
    ctx = bootstrap_job(args.job)
    return args, ctx
