#!/usr/bin/env python3
"""PNG-critic reverts: 1.4.1.3 tag is LF not LR; 1.4.2.2 Please is head not HR."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
paths = [
    ROOT / "output/cefr-threshold-1990/Threshold_1990.md",
    ROOT / "work/cefr-threshold-1990/page_overrides/page_035.md",
    ROOT / "docs/vision_extract/INTONATION_WORD_CATALOG_LEAF034_035.md",
]
pairs = [
    ("ˏdidn’t they?", "ˎdidn’t they?"),
    ("ˏdidn't they?", "ˎdidn't they?"),
    ("ˊPlease can you ·tell me the ·way to the ˎstation?",
     "ˈPlease can you ·tell me the ·way to the ˎstation?"),
]
for p in paths:
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    n = 0
    for a, b in pairs:
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n += c
            print(f"{p.name}: {c}x {a[:50]!r}")
    p.write_text(t, encoding="utf-8")
    print(f"{p.name} ops={n}")

md = (ROOT / "output/cefr-threshold-1990/Threshold_1990.md").read_text(encoding="utf-8")
checks = [
    "ˋThis is the ·bedroom",
    "The ·train ˋhas ·left",
    "ˊDid you ˎsee him",
    "You ˊsaw him",
    "ˎdidn’t they",
    "ˏdidn’t they",
    "ˈPlease can you",
    "ˊPlease can you",
    "You ˇdid ·go",
    "arˎrive",
]
print("--- final ---")
for s in checks:
    print(f"  {s!r}: {md.count(s)}")
