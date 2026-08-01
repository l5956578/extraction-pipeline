#!/usr/bin/env python3
import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
pdf = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
keys = ["2.2.3", "2.2.4.1", "2.2.5.2", "3.1.2", "3.1.3", "3.1.5", "4.2.1", "5.4.1"]
for leaf in range(34, 60):
    t = pdf[leaf - 1].get_text("text")
    if not any(k in t for k in keys):
        continue
    print(f"\n===== LEAF {leaf} doc {leaf-6} =====")
    for line in t.splitlines():
        s = line.strip()
        if any(
            x in s
            for x in [
                "2.2.3",
                "2.2.4",
                "2.2.5",
                "3.1.",
                "4.2.1",
                "5.4.1",
                "wrong",
                "horrible",
                "dance",
                "walk",
                "Hallo",
                "train",
                "will",
                "Spinach",
            ]
        ):
            print(repr(s))
