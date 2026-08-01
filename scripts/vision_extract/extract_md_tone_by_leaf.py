#!/usr/bin/env python3
"""Extract product MD tone lines keyed by document page / PDF leaf (doc = leaf-6)."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
OUT = ROOT / "work/cefr-threshold-1990/intonation_hires/primary_all/md_tones_by_leaf.txt"

LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    bodies: dict[int, str] = {}
    for m in re.finditer(r"<!-- page:(\d+) -->", md):
        doc = int(m.group(1))
        prev = list(re.finditer(r"<!-- page:(\d+|front-[^\s]+) -->", md[: m.start()]))
        start = prev[-1].end() if prev else 0
        bodies[doc] = md[start : m.start()]

    lines_out = []
    for leaf in LEAVES:
        doc = leaf - 6
        body = bodies.get(doc, "")
        tone_lines = [
            ln.strip()
            for ln in body.splitlines()
            if re.search(r"[ˈˎˋˏˊˇ·]", ln)
        ]
        lines_out.append(f"===== LEAF {leaf} DOC {doc} n={len(tone_lines)} =====")
        lines_out.extend(tone_lines)
        lines_out.append("")
        print(f"leaf {leaf} doc {doc}: {len(tone_lines)} tone lines")
    OUT.write_text("\n".join(lines_out), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
