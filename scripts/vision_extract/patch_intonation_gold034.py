#!/usr/bin/env python3
"""Apply gold leaf-34 intonation fixes into product Threshold MD + override."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"

# (wrong, correct) — product MD only in language-functions region
REPS = [
    ("the ·owner of the ·restaurant", "the ˎowner of the ·restaurant"),
    ("the ·owner of the", "the ˎowner of the"),
    ("is my ·dog", "is my ˎdog"),
    ("ˈNo it ˋisn't", "ˈNo it ˇisn't"),
    ("ˈNo it ˋisn’t", "ˈNo it ˇisn’t"),
    ("No it ˋisn't", "No it ˇisn't"),
    ("No it ˋisn’t", "No it ˇisn’t"),
    # if still mid-dot on owner alone in function examples
    ("> ˈHe is the ·owner", "> ˈHe is the ˎowner"),
]


def main() -> None:
    t = MD.read_text(encoding="utf-8")
    # Prefer function block if present
    markers = [
        ("## Language functions for Threshold Level", "## 6 "),
        ("### 1 Imparting and seeking", "### 6 "),
        ("**1.1.3**", "**2.5"),
    ]
    start = 0
    end = len(t)
    for a, b in markers:
        i = t.find(a)
        if i >= 0:
            start = i
            j = t.find(b, i + 10)
            if j > i:
                end = j
            break
    head, mid, tail = t[:start], t[start:end], t[end:]
    n = 0
    for a, b in REPS:
        c = mid.count(a)
        if c:
            mid = mid.replace(a, b)
            n += c
            print(f"replaced x{c}: {a!r} -> {b!r}")
    MD.write_text(head + mid + tail, encoding="utf-8")
    t2 = MD.read_text(encoding="utf-8")
    print("verify ˎowner", t2.count("ˎowner"), "·owner", t2.count("·owner"))
    print("verify ˎdog", t2.count("ˎdog"), "my ·dog", t2.count("my ·dog"))
    print("verify ˇisn", "ˇisn" in t2, "ˋisn", "ˋisn" in t2)
    print("total replacements", n)


if __name__ == "__main__":
    main()
