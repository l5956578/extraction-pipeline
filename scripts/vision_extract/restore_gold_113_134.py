#!/usr/bin/env python3
"""Restore Threshold 1.1.3–1.3.4 gold after fuzzy letter-skeleton collapse.

Always delegates to gold_intonation_locks (section-aware). Re-running native
convert / merge cannot re-break these forms if this runs after them.
"""

from __future__ import annotations

from pathlib import Path

from gold_intonation_locks import (
    THR_MD,
    apply_section_locks,
    gold_counts,
    residual_assertions,
    sync_override_leaves,
)

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    md = THR_MD.read_text(encoding="utf-8")
    md, ops = apply_section_locks(md)
    THR_MD.write_text(md, encoding="utf-8")
    print("ops:", ops or ["noop (already gold)"])
    counts = gold_counts(md)
    for s in [
        "ˈThis is the ˎbedroom",
        "ˋThis is the ·bedroom",
        "The ˈtrain has ˎleft",
        "The ·train ˋhas ·left",
        "ˎowner",
        "my ˎdog",
        "ˇisn",
        "ˇdid",
        "The ˇanimal",
        "ˊDid you ˎsee him",
        "ˈPlease can you",
    ]:
        print(f"  {s!r}: {counts.get(s, md.count(s))}")
    fails = residual_assertions(md)
    if fails:
        print("RESIDUAL FAILS:")
        for f in fails:
            print(f"  - {f}")
    else:
        print("residual assertions: PASS")
    n = sync_override_leaves([34, 35])
    print(f"overrides 34-35: {n}")


if __name__ == "__main__":
    main()
