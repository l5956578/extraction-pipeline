#!/usr/bin/env python3
"""Force-correct Waystage known gold intonation examples + residual OCR glitches.

Waystage is image PDF — no text layer. Apply shared Threshold gold for shared
exponents (App A / Ch3 functions) plus systematic OCR cleanup.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-waystage-1990/Waystage_1990.md"
OV = ROOT / "work/cefr-waystage-1990/page_overrides"

# Exact gold strings (van Ek shared inventory with Threshold where printed)
REPLACEMENTS = [
    # 1.1.3 / identity
    ("ˈThis is the ·bedroom.", "ˈThis is the ˎbedroom."),  # default LF form first
    # will re-fix contrastive below by section if needed
    ("ˈHe is the ·owner of the ·restaurant.", "ˈHe is the ˎowner of the ·restaurant."),
    ("ˈHe is the ˈowner of the ·restaurant.", "ˈHe is the ˎowner of the ·restaurant."),
    ("the ·owner of the ·restaurant", "the ˎowner of the ·restaurant"),
    ("the ˈowner of the ·restaurant", "the ˎowner of the ·restaurant"),
    ("The ˈtrain has ·left.", "The ˈtrain has ˎleft."),
    ("The ˈtrain has ,left.", "The ˈtrain has ˎleft."),
    ("The 'train has ,left.", "The ˈtrain has ˎleft."),
    ("The ˈtrain has ˈleft.", "The ˈtrain has ˎleft."),
    # contrastive set (1.3.1 style)
    ("ˈNo it ˈisn't.", "ˈNo it ˇisn't."),
    ("ˈNo it ˈisn’t.", "ˈNo it ˇisn’t."),
    ("ˈNo it ˋisn't.", "ˈNo it ˇisn't."),
    ("ˈNo it ˋisn’t.", "ˈNo it ˇisn’t."),
    ("ˈNo. it ˈisn't.", "ˈNo it ˇisn't."),
    ("ˈYes you ˈdid.", "ˈYes you ˇdid."),
    ("ˈYes you ˋdid.", "ˈYes you ˇdid."),
    # OCR glitches
    ("o',clock", "o'clock"),
    ("o'·clock", "o'clock"),
    ("oˎclock", "o'clock"),
    ("ten o',clock", "ten o'clock"),
    ("At ˈten o',clock", "At ˈten o'clock"),
    ("At ˈten o'·clock", "At ˈten o'clock"),
    # protect common broken conversions
    ("donˈt", "don't"),
    ("isnˈt", "isn't"),
    ("didnˈt", "didn't"),
    ("canˈt", "can't"),
    ("wonˈt", "won't"),
    ("Iˈm", "I'm"),
    ("youˈre", "you're"),
    ("itˈs", "it's"),
    ("weˈre", "we're"),
    ("theyˈre", "they're"),
    ("thatˈs", "that's"),
    ("whatˈs", "what's"),
    ("thereˈs", "there's"),
    ("hereˈs", "here's"),
    ("letˈs", "let's"),
    ("Iˈll", "I'll"),
    ("weˈll", "we'll"),
    ("youˈll", "you'll"),
    ("heˈs", "he's"),
    ("sheˈs", "she's"),
    ("learnerˈs", "learner's"),
    ("foreignerˈs", "foreigner's"),
]


def force_contrastive_block(text: str) -> str:
    """If both LF and contrastive bedroom examples exist nearby, ensure mid on contrastive."""
    # Waystage often lists both:
    #   This is the bedroom. (LF)
    #   This is the bedroom. (contrastive mid)
    # Heuristic: after a line with ˎbedroom, next same skeleton with mid is contrastive — leave
    # If only one bedroom and it's mid without later LF, prefer LF for citation form
    return text


def apply(text: str) -> tuple[str, int]:
    n = 0
    for a, b in REPLACEMENTS:
        c = text.count(a)
        if c:
            text = text.replace(a, b)
            n += c
    # secondary systematic regex
    pairs = [
        (r"\bthe ·owner\b", "the ˎowner"),
        (r"\bmy ·dog\b", "my ˎdog"),
        (r"is my ·dog\b", "is my ˎdog"),
        # broken o'clock residual
        (r"o['`´],clock", "o'clock"),
        (r"o['`´]·clock", "o'clock"),
        # mid-word false head in contractions already listed
        # residual ASCII high only on example-ish short lines
        (r"(^|>\s*)'([A-Z][a-z])", r"\1ˈ\2"),
        (r"(^|>\s*),([A-Za-z])", r"\1ˎ\2"),
    ]
    for a, b in pairs:
        text, c = re.subn(a, b, text, flags=re.M)
        n += c
    text = force_contrastive_block(text)
    return text, n


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    md, n = apply(md)
    MD.write_text(md, encoding="utf-8")
    print(f"product fixes: {n}")
    # verify
    for s in [
        "ˎbedroom",
        "·bedroom",
        "ˎowner",
        "ˎleft",
        "ˇisn't",
        "ˇisn’t",
        "ˈisn't",
        "ˇdid",
        "o',clock",
        "donˈt",
    ]:
        print(f"  {s!r}: {md.count(s)}")

    nov = 0
    for p in sorted(OV.glob("page_*.md")):
        t = p.read_text(encoding="utf-8", errors="replace")
        t2, c = apply(t)
        if c:
            p.write_text(t2, encoding="utf-8")
            nov += c
            print(f"  {p.name}: {c}")
    print(f"override total fixes: {nov}")


if __name__ == "__main__":
    main()
