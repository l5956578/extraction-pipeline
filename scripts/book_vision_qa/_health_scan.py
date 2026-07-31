#!/usr/bin/env python3
"""Quick deliverable health scan."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    print("chars", len(md))
    print("pages", len(re.findall(r"<!-- page:\d+ -->", md)))
    print("literal_backslash_n", md.count("\\n"))
    print("zwsp", md.count("\u200b"), "nbsp", md.count("\u00a0"))
    print("el_start", md.count("el:start"), "el_end", md.count("el:end"))
    rev = [
        t
        for t in (
            "noitpircsed",
            "sesoprup",
            "cfiiceps",
            "ssenetairporppa",
            "smerp",
            "nettirw",
            "erutcurts",
        )
        if t in md.lower()
    ]
    print("rev_tokens", rev)
    pins = {
        "dialogue": "rather than dialogue" in md,
        "oral": "Oral interaction is understood" in md,
        "grid_a1": "I can recognise familiar" in md,
        "grid_c2": "I have no difficulty" in md,
        "reception": "3.1. RECEPTION" in md,
        "table_05": "table_05_descriptor_use" in md,
    }
    print("pins", pins)
    # mojibake-ish
    moji = re.findall(r"(?:Ã.|Â.|â€™|â€){1,}", md)
    print("mojibake_hits", len(moji), moji[:5])


if __name__ == "__main__":
    main()
