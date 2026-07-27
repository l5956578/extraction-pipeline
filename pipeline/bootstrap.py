"""Shared CLI bootstrap — require --job and load JobContext.

All entry scripts should::

    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(...)
    add_job_argument(parser)
    # ... other args ...
    args = parser.parse_args()
    ctx = bootstrap_job(args.job, force_draft=args.force_draft)

There is no default job id (Phase B).

``bootstrap_job`` enforces engine-ready checks (markdown + PDF source) so draft
jobs registered for ``page_png`` / ``tabular_db`` / ``markdown_import`` fail early
instead of dying mid-extract. Pass ``--force-draft`` only for intentional experiments.
``load_job`` alone still allows inspection of any job.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from pipeline.job_context import (
    JobContext,
    engine_ready_issues,
    load_job,
)


def add_job_argument(parser: argparse.ArgumentParser) -> None:
    """Add required ``--job JOB_ID`` and optional ``--force-draft``."""
    parser.add_argument(
        "--job",
        required=True,
        metavar="JOB_ID",
        help="Job id under input|work|output/<job>/ (required)",
    )
    parser.add_argument(
        "--force-draft",
        action="store_true",
        help=(
            "Allow CLI on jobs whose output.mode/source is not engine-supported "
            "(page_png, tabular_db, markdown_import, non-PDF). Prefer load_job for "
            "inspection; do not use for production extract."
        ),
    )


def bootstrap_job(
    job_id: str,
    *,
    reload: bool = False,
    force_draft: bool = False,
) -> JobContext:
    """Load job, bind config, and enforce engine-ready unless ``force_draft``.

    Exits with code 2 on empty id or unsupported mode/source without force.
    Warns when ``status == draft`` (even if mode is markdown PDF).
    """
    if job_id is None or not str(job_id).strip():
        print("error: --job JOB_ID is required", file=sys.stderr)
        raise SystemExit(2)

    ctx = load_job(str(job_id).strip(), reload=reload)
    issues = engine_ready_issues(ctx)

    if issues and not force_draft:
        print(
            f"error: job {ctx.job_id!r} is not ready for the PDF markdown engine:",
            file=sys.stderr,
        )
        for msg in issues:
            print(f"  - {msg}", file=sys.stderr)
        print(
            "hint: pass --force-draft only for intentional experiments; "
            "use load_job(job_id) for inspection without running extract.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if issues and force_draft:
        print(
            f"warning: --force-draft bypassing engine-ready checks for {ctx.job_id!r}:",
            file=sys.stderr,
        )
        for msg in issues:
            print(f"  - {msg}", file=sys.stderr)

    if (ctx.status or "").lower() == "draft":
        print(
            f"warning: job {ctx.job_id!r} has status=draft "
            f"(layout/extract may be incomplete; not a production deliverable).",
            file=sys.stderr,
        )

    return ctx


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
    ctx = bootstrap_job(args.job, force_draft=bool(getattr(args, "force_draft", False)))
    return args, ctx
