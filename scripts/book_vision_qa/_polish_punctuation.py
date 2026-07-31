#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

MD = Path(__file__).resolve().parents[2] / "output/cefr-companion-2020/CEFR_Companion_Volume.md"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    for a, b in [
        ("descripteurs”,respectively.", "descripteurs”, respectively."),
        ('descripteurs",respectively.', 'descripteurs", respectively.'),
    ]:
        if a in md:
            md = md.replace(a, b)
            print("fixed", a[:50])
    md2, n = re.subn(r'([”"]),([A-Za-z])', r"\1, \2", md)
    print("comma_glue", n)
    # missing space after closing paren before capital
    md2, n2 = re.subn(r"\)([A-Z])", r") \1", md2)
    print("paren_cap", n2)
    MD.write_text(md2, encoding="utf-8")


if __name__ == "__main__":
    main()
