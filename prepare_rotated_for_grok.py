#!/usr/bin/env python3
"""Prepare all rotated-table PNG handoffs from inventories (before agent vision)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(description="Prepare rotated table PNGs for agent vision")
    add_job_argument(parser)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-crop PNGs even if they already exist",
    )
    args = parser.parse_args()

    ctx = bootstrap_job(args.job, force_draft=args.force_draft)
    print(f"Job: {ctx.job_id}\n")

    from pipeline.extractors.rotated_grok_vision import (
        get_pending_rotated_tables,
        prepare_all_rotated_from_inventories,
        refresh_manifest_statuses,
    )

    print("=== Prepare rotated tables for agent vision (no chat Grok) ===\n")
    prepared = prepare_all_rotated_from_inventories(force=args.force)
    manifest = refresh_manifest_statuses()
    pending = get_pending_rotated_tables()

    rot_for = ctx.rotated_for_grok_dir
    rot_from = ctx.rotated_from_grok_dir
    print(f"Prepared/verified: {len(prepared)} table page(s)")
    print(f"Handoff dir: {rot_for}")
    print(f"Manifest: {rot_for / 'manifest.json'}")
    print(f"Pending agent markdown: {len(pending)}")
    print(f"Ready agent markdown: {manifest.get('received', 0)}")

    if pending:
        print("\n--- Coding agent must vision-read PNGs (user not in loop) ---")
        for row in pending[:30]:
            slug = row.get("slug", "")
            print(f"  {slug}.png → {rot_from / f'{slug}.md'}")
        if len(pending) > 30:
            print(f"  ... and {len(pending) - 30} more (see manifest.json)")

    print(f"\nREADME: {rot_for / 'README.txt'}")
    print(f"Brief:  {ctx.metadata_dir / 'ROTATED_TABLES_AGENT_VISION.md'}")


if __name__ == "__main__":
    main()
