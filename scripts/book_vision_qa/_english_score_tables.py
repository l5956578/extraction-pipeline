#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
md = MD.read_text(encoding="utf-8")

COMMON = set(
    """
    the of and to a in is is that for it as was with be by on not he i this from or have an they
    which one you were her all she there would their we him been has when who will more if no out
    so what up said its about into than them can could only other new some time these two may then
    do first any my now such over even most made after also did many before must through back years
    where much your way well down should because each just those people little state good very make
    world still own see work long get here between both life being under never day same another know
    while last might us great old year off come since against go came right take three few found house
    use during without again place around however home small number part system order end understand
    express themselves language level descriptors scale available learner user spoken written signed
    """.split()
)


def score(text: str) -> float:
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    if len(words) < 30:
        return 1.0
    return sum(1 for w in words if w in COMMON) / len(words)


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def main() -> None:
    low = []
    for n in range(1, 279):
        b = page_body(n)
        if "|" not in b or len(b) < 800:
            continue
        sc = score(b)
        if sc < 0.12:
            low.append((n, round(sc, 3), len(b)))
    print("low_score", low)


if __name__ == "__main__":
    main()
