#!/usr/bin/env python3
"""Audit residual intonation issues in product MD."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def audit(path: Path) -> None:
    md = path.read_text(encoding="utf-8")
    print(f"=== {path.name} ===")
    patterns = {
        "unicode_tones": r"[ˈˎˋˏˊˇ·]",
        "blockquote_tones": r"^>.*[ˈˎˋˏˊˇ·]",
        "IPA_secondary_as_LF": r"ˌ[A-Za-z]",
        "HF_isn": r"ˋisn",
        "FR_isn": r"ˇisn",
        "ASCII_high_before_letter": r"(?<=[\s>|])'[A-Za-z]",
        "owner_mid_bad": r"·owner",
        "owner_LF": r"ˎowner",
        "dog_mid_bad": r"my ·dog",
        "dog_LF": r"my ˎdog",
        "bedroom_LF": r"ˎbedroom",
        "bedroom_mid": r"·bedroom",
    }
    for name, p in patterns.items():
        print(f"  {name}: {len(re.findall(p, md, re.M))}")

    pages = re.split(r"<!-- page:(\d+) -->", md)
    c = Counter()
    for i in range(1, len(pages), 2):
        p = int(pages[i])
        body = pages[i + 1]
        n = len(re.findall(r"[ˈˎˋˏˊˇ·]", body))
        if n:
            c[p] = n
    print(f"  doc pages with tones: {len(c)}")
    for p, n in c.most_common(30):
        print(f"    doc p.{p}: {n} marks")

    # residual ASCII high samples
    bad = []
    for line in md.splitlines():
        if re.search(r"(?<=[\s>|])'[A-Za-z]", line):
            bad.append(line.strip()[:120])
    print(f"  residual ASCII high lines: {len(bad)}")
    for b in bad[:20]:
        print(f"    {b}")


def main() -> None:
    audit(ROOT / "output/cefr-threshold-1990/Threshold_1990.md")
    wp = ROOT / "output/cefr-waystage-1990/Waystage_1990.md"
    if wp.exists():
        audit(wp)


if __name__ == "__main__":
    main()
