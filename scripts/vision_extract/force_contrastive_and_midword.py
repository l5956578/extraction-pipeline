#!/usr/bin/env python3
"""Force 1.3.1 contrastive examples + mid-word high marks (pre'fer → preˈfer).

Uses gold_intonation_locks so re-runs cannot re-break 1.1.3 / 1.2.1 / 1.3.1.
"""

from __future__ import annotations

from pathlib import Path

from gold_intonation_locks import (
    THR_MD,
    WAY_MD,
    apply_section_locks,
    gold_counts,
    residual_assertions,
    waystage_residual_safety,
)

ROOT = Path(__file__).resolve().parents[2]


def fix_threshold() -> None:
    md = THR_MD.read_text(encoding="utf-8")
    md, ops = apply_section_locks(md)
    THR_MD.write_text(md, encoding="utf-8")
    print(f"Threshold_1990.md: ops={ops}")
    counts = gold_counts(md)
    for s in [
        "ˈThis is the ˎbedroom",
        "ˈThis is the ·bedroom",
        "ˋThis is the ·bedroom",
        "The ·train ˈhas ·left",
        "The ·train ˋhas ·left",
        "The ˈtrain has ˎleft",
        "preˈfer",
        "e'specially",
        "eˈspecially",
        "ˎowner",
        "ˇisn",
    ]:
        print(f"  {s!r}: {counts.get(s, md.count(s))}")
    fails = residual_assertions(md)
    print("residual:", "PASS" if not fails else fails)


def fix_waystage() -> None:
    path = WAY_MD
    if not path.exists():
        return
    md = path.read_text(encoding="utf-8")
    md, ops = waystage_residual_safety(md)
    # Waystage shared LF forms only (do not invent ˋ contrastive without PNG)
    pairs = [
        ("ˈHe is the ·owner of the ·restaurant.", "ˈHe is the ˎowner of the ·restaurant."),
        ("the ·owner of the ·restaurant", "the ˎowner of the ·restaurant"),
        ("The ˈtrain has ·left.", "The ˈtrain has ˎleft."),
        ("ˈNo it ˋisn’t.", "ˈNo it ˇisn’t."),
        ("ˈNo it ˋisn't.", "ˈNo it ˇisn't."),
        ("ˈYes you ˋdid.", "ˈYes you ˇdid."),
    ]
    n = 0
    for a, b in pairs:
        if a in md:
            md = md.replace(a, b)
            n += 1
    path.write_text(md, encoding="utf-8")
    print(f"Waystage_1990.md: residual_ops={ops} pair_ops={n}")
    for s in [
        "ˈThis is the ˎbedroom",
        "ˈThis is the ·bedroom",
        "The ·train ˈhas ·left",
        "The ˈtrain has ˎleft",
        "ˎowner",
        "ˇisn",
    ]:
        print(f"  {s!r}: {md.count(s)}")


def main() -> None:
    fix_threshold()
    fix_waystage()


if __name__ == "__main__":
    main()
