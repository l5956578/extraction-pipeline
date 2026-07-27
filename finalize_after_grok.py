#!/usr/bin/env python3
"""
Re-extract (picks up agent vision markdown), then cleanup + merge.

Run after agent has written work/<job-id>/metadata/rotated_from_grok/page_*_*.md
for pending rotated tables (re-read PNGs with vision first — see
work/<job-id>/metadata/ROTATED_TABLES_AGENT_VISION.md).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    from pipeline.bootstrap import add_job_argument, bootstrap_job

    parser = argparse.ArgumentParser(
        description="Finalize pipeline after agent vision markdown for rotated tables"
    )
    parser.add_argument(
        "chunk_id",
        nargs="?",
        default=None,
        help="Single chunk to re-extract (default: all chunks with rotated tables)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Run cleanup/merge even if some vision markdown is still missing",
    )
    parser.add_argument(
        "--all-chunks",
        action="store_true",
        help="Re-extract every chunk (not only those with rotated tables)",
    )
    add_job_argument(parser)
    args = parser.parse_args()

    ctx = bootstrap_job(args.job)
    print(f"Job: {ctx.job_id}")

    import pipeline.config as cfg
    from pipeline.cleanup import cleanup_file
    from pipeline.extract_chunk import extract_chunk
    from pipeline.extractors.rotated_grok_vision import (
        chunk_has_pending_grok,
        chunks_with_rotated_tables,
        get_pending_rotated_tables,
        refresh_manifest_statuses,
    )
    from pipeline.merge_output import merge_markdown

    refresh_manifest_statuses()
    pending = get_pending_rotated_tables()

    rot_from = ctx.rotated_from_grok_dir
    print("=== Finalize after agent vision (rotated tables) ===\n")
    if pending:
        print(f"Global pending: {len(pending)} table page(s) without .md")
        for row in pending[:20]:
            slug = row.get("slug") or ""
            print(f"  missing: {rot_from / (slug + '.md')}")
        if len(pending) > 20:
            print(f"  ... and {len(pending) - 20} more")

    if args.chunk_id:
        chunk_ids = [args.chunk_id]
    elif args.all_chunks:
        chunk_ids = [
            p.stem.replace("_inventory", "")
            for p in sorted(cfg.INVENTORIES_DIR.glob("chunk_*_inventory.json"))
        ]
    else:
        chunk_ids = chunks_with_rotated_tables()

    still_pending_chunks = [c for c in chunk_ids if chunk_has_pending_grok(c)]
    if still_pending_chunks:
        print(
            f"\nNote: {len(still_pending_chunks)} chunk(s) still missing some agent .md "
            f"(geometry fallback during extract): {', '.join(still_pending_chunks[:8])}"
            + ("..." if len(still_pending_chunks) > 8 else "")
        )
    if args.force:
        print("( --force: continue even if hard placeholders remain )")

    print(f"\n[1/3] Re-extract {len(chunk_ids)} chunk(s)")
    for cid in chunk_ids:
        extract_chunk(cid)
        raw = cfg.RAW_DIR / f"{cid}.md"
        if raw.exists():
            raw_text = raw.read_text(encoding="utf-8")
            if "GROK_VISION_PENDING" in raw_text and "geometry_fallback" not in raw_text:
                if not args.force:
                    print(f"\n{cid} has hard GROK_VISION_PENDING without fallback.")
                    print("Pass --force to continue, or write agent .md files.")
                    sys.exit(1)
            if "AGENT_VISION_PENDING" in raw_text or "geometry_fallback" in raw_text:
                print(f"  note: {cid} used geometry fallback for some rotated tables")

    print("\n[2/3] cleanup (all raw chunks)")
    for raw in sorted(cfg.RAW_DIR.glob("chunk_*.md")):
        cleanup_file(raw, cfg.CLEANED_DIR / raw.name)

    print("\n[3/3] merge")
    merge_markdown()

    final = ctx.final_markdown
    print("\n=== Done ===")
    print(f"  final: {final} ({final.stat().st_size if final.exists() else 0} bytes)")
    print("  next: agent vision for remaining pending PNGs if any")


if __name__ == "__main__":
    main()
