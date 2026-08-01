#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
NOTN = ROOT / "docs/vision_extract/INTONATION_NOTATION.md"
CAT = ROOT / "docs/vision_extract/INTONATION_WORD_CATALOG_LEAF034.md"

md = MD.read_text(encoding="utf-8")
md = md.replace(
    "You ˈare ˎcoming, | ˎaren't you? with low-rising intonation non-conductive",
    "You ˈare ˎcoming, | ˏaren't you? with low-rising intonation non-conductive",
)
md = md.replace(
    "You ˈare ˎcoming, | ˎaren’t you? with low-rising intonation non-conductive",
    "You ˈare ˎcoming, | ˏaren’t you? with low-rising intonation non-conductive",
)
md = md.replace("You are German, | ˎaren't you?", "You are German, | ˏaren't you?")
md = md.replace("You are German, | ˎaren’t you?", "You are German, | ˏaren’t you?")
MD.write_text(md, encoding="utf-8")
print("MD LR tag patches done")
for s in [
    "ˋThis is the ·bedroom",
    "The ·train ˋhas ·left",
    "ˊDid you ˎsee him",
    "ˏdidn’t they",
    "ˊPlease can you",
    "ˏaren't you",
    "ˏaren’t you",
]:
    print(f"  {s!r}: {md.count(s)}")

if CAT.exists():
    c = CAT.read_text(encoding="utf-8")
    c = c.replace(
        "| This | `ˈ` | high upright (contrastive head) |",
        "| This | `ˋ` | high fall diagonal above (contrastive) |",
    )
    c = c.replace(
        "| has | `ˈ` | high upright contrastive |",
        "| has | `ˋ` | high fall diagonal above (contrastive) |",
    )
    c = c.replace(
        "ˈThis is the ·bedroom.\nThe ·train ˈhas ·left.",
        "ˋThis is the ·bedroom.\nThe ·train ˋhas ·left.",
    )
    # also if already partially updated
    c = c.replace(
        "This | `ˈ` | high upright (contrastive head)",
        "This | `ˋ` | high fall diagonal above (contrastive)",
    )
    CAT.write_text(c, encoding="utf-8")
    print("catalog patched")

t = NOTN.read_text(encoding="utf-8")
if "Paper Capture collapses" not in t and "PDF text-layer trap" not in t:
    insert = """
## PDF text-layer trap (Threshold Paper Capture)

The PDF text layer is a **hint**, not the mark inventory:

| PDF char | Collapses | Must Vision-disambiguate |
|----------|-----------|--------------------------|
| `'` above syllable | head `ˈ` · high fall `ˋ` · high rise `ˊ` | vertical vs falling diagonal vs rising tick; **contrastive → often `ˋ`**; **high-rising heading → `ˊ`** |
| `,` below syllable | low fall `ˎ` · low rise `ˏ` | stroke direction; **confirmation tags often `ˏ`** (agreement tags falling) |
| `"` / v | fall-rise `ˇ` | |
| `.` mid | secondary `·` | |

**Failed pattern (2026-07-31):** always mapping `'`→`ˈ` and `,`→`ˎ` corrupted **1.3.1**, **1.4.1.1**, **1.4.1.3**, **1.4.2.2**.

Word catalogs: `INTONATION_WORD_CATALOG_LEAF034.md`, `INTONATION_WORD_CATALOG_LEAF034_035.md`.

"""
    t = t.replace("## Forbidden encodings", insert + "## Forbidden encodings")
    # fix worked example 1.3.1
    t = t.replace(
        "| 1.3.1 | `ˈThis is the ·bedroom.` / `The ·train ˈhas ·left.` (contrastive: mid on bedroom/left; high on This/has) |",
        "| 1.3.1 | `ˋThis is the ·bedroom.` / `The ·train ˋhas ·left.` (contrastive: mid on bedroom/left; **high fall** on This/has) |",
    )
    NOTN.write_text(t, encoding="utf-8")
    print("notation trap + 1.3.1 example updated")
else:
    print("notation already has trap note")
