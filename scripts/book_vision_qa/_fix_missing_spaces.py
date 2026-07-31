#!/usr/bin/env python3
"""Fix common missing-space glues without breaking URLs/code."""

from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    total = 0

    # comma/semicolon missing space before letter.
    # NEVER auto-space after colon: breaks el:start, db:id, page:N, URLs.
    for punct in (",", ";"):
        md2, n = re.subn(rf"{re.escape(punct)}([A-Za-z])", rf"{punct} \1", md)
        print(f"space after {punct!r}", n)
        total += n
        md = md2

    # period missing space before capital (not ellipsis, not decimals)
    md2, n = re.subn(r"(?<=[a-z])\.([A-Z])", r". \1", md)
    print("space after period before cap", n)
    total += n
    md = md2

    MD.write_text(md, encoding="utf-8")
    print("total_edits_applied", total)


if __name__ == "__main__":
    main()
