#!/usr/bin/env python3
"""Prepare all rotated-table PNG handoffs from inventories (before agent vision)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from pipeline.config import ROTATED_FOR_GROK_DIR
from pipeline.extractors.rotated_grok_vision import (
    get_pending_rotated_tables,
    prepare_all_rotated_from_inventories,
    refresh_manifest_statuses,
)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Prepare rotated table PNGs for agent vision")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-crop PNGs even if they already exist",
    )
    args = parser.parse_args()

    print("=== Prepare rotated tables for agent vision (no chat Grok) ===\n")
    prepared = prepare_all_rotated_from_inventories(force=args.force)
    manifest = refresh_manifest_statuses()
    pending = get_pending_rotated_tables()

    print(f"Prepared/verified: {len(prepared)} table page(s)")
    print(f"Handoff dir: {ROTATED_FOR_GROK_DIR}")
    print(f"Manifest: {ROTATED_FOR_GROK_DIR / 'manifest.json'}")
    print(f"Pending agent markdown: {len(pending)}")
    print(f"Ready agent markdown: {manifest.get('received', 0)}")

    if pending:
        print("\n--- Coding agent must vision-read PNGs (user not in loop) ---")
        for row in pending[:30]:
            slug = row.get("slug", "")
            print(f"  {slug}.png → work/metadata/rotated_from_grok/{slug}.md")
        if len(pending) > 30:
            print(f"  ... and {len(pending) - 30} more (see manifest.json)")

    print(f"\nREADME: {ROTATED_FOR_GROK_DIR / 'README.txt'}")
    print("Brief:  work/metadata/ROTATED_TABLES_AGENT_VISION.md")


if __name__ == "__main__":
    main()
