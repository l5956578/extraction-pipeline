# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "page_overrides"

for leaf in (58, 59, 60, 61, 62, 63):
    p = ROOT / f"page_{leaf:03d}.md"
    t = p.read_text(encoding="utf-8")
    orig = t
    # ˈword' → 'word' (opening head misread as quote)
    t = re.sub("\u02c8([A-Za-z][^']{0,40})'", "'\\1'", t)
    # any remaining head on pure prose pages → left single quotation mark
    t = t.replace("\u02c8", "\u2018")
    if t != orig:
        p.write_text(t, encoding="utf-8")
        print(f"fixed {leaf} H_left={t.count(chr(0x2C8))}")
    else:
        print(f"no change {leaf}")

# gold checks leaf 22
t = (ROOT / "page_022.md").read_text(encoding="utf-8")
checks = [
    ("ˇisn't", "ˇisn't" in t or "ˇisn" in t),
    ("ˊsaw", "ˊsaw" in t),
    ("ˏAre", "ˏAre" in t),
    ("ˎbedroom", "ˎbedroom" in t),
    ("·restaurant", "·restaurant" in t),
    ("ˎowner", "ˎowner" in t),
    ("header", "word-catalog multipass" in t),
]
for name, ok in checks:
    print(("OK" if ok else "FAIL"), name)
print("done")
