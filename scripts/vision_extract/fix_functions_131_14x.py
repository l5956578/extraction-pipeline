#!/usr/bin/env python3
"""Restore Threshold 1.3.1 / 1.4.1.x / 1.4.2.2 PNG gold via section locks.

DEPRECATED as a freehand invent path. Previously forced ˏdidn't / ˊPlease from
section titles — that contradicts PNG crops (low fall tag, head on Please).

Now only delegates to gold_intonation_locks (glyph > PDF > section title).
"""

from __future__ import annotations

import sys
from pathlib import Path

from gold_intonation_locks import (
    THR_MD,
    THR_OV,
    apply_section_locks,
    gold_counts,
    residual_assertions,
    sync_override_leaves,
)

ROOT = Path(__file__).resolve().parents[2]
OV34 = THR_OV / "page_034.md"
OV35 = THR_OV / "page_035.md"


def apply_path(path: Path) -> list[str]:
    if not path.exists():
        return []
    t = path.read_text(encoding="utf-8")
    t2, ops = apply_section_locks(t)
    if t2 != t:
        path.write_text(t2, encoding="utf-8")
    print(f"{path.name}: {ops or ['noop']}")
    return ops


def main() -> None:
    print(
        "fix_functions_131_14x: gold_intonation_locks only "
        "(no ˏdidn't / ˊPlease invent)"
    )
    apply_path(THR_MD)
    apply_path(OV34)
    apply_path(OV35)
    n = sync_override_leaves([34, 35])
    print(f"override sync 34-35: {n}")

    md = THR_MD.read_text(encoding="utf-8")
    counts = gold_counts(md)
    for s in [
        "ˋThis is the ·bedroom",
        "The ·train ˋhas ·left",
        "The ˈtrain has ˎleft",
        "ˈThis is the ˎbedroom",
        "ˊDid you ˎsee him",
        "ˈDid you ˎsee him",
        "ˎdidn't they",
        "ˏdidn't they",
        "ˈPlease can you",
        "ˊPlease can you",
    ]:
        print(f"  {s!r}: {counts.get(s, md.count(s))}")
    fails = residual_assertions(md)
    if fails:
        print("RESIDUAL FAIL:")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    print("residual assertions: PASS")


if __name__ == "__main__":
    main()
