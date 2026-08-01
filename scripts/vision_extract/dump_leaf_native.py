#!/usr/bin/env python3
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]


def convert_marks(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = re.sub(r'(^|[\s(|])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    s = re.sub(r"(^|[\s(|])['`´]+(?=[A-Za-z])", r"\1ˈ", s)
    s = re.sub(r"(^|[\s(|]),(?=[A-Za-z])", r"\1ˎ", s)
    s = re.sub(r"(?<=[A-Za-z]),(?=[A-Za-z])", "ˎ", s)
    s = re.sub(r"(^|[\s(|])\.(?=[A-Za-z])", r"\1·", s)
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    s = re.sub(r"\s+I\s+", " | ", s)
    return s


def main() -> None:
    leaves = [int(x) for x in sys.argv[1:]] or [34, 35]
    doc = fitz.open(ROOT / "input/cefr-threshold-1990/source.pdf")
    for leaf in leaves:
        print(f"===== LEAF {leaf} =====")
        text = doc[leaf - 1].get_text("text")
        print(text)
        print("--- converted mark lines ---")
        for line in text.splitlines():
            if re.search(r"['`,.\"][A-Za-z]|bedroom|train|see him|match|station|saw|didn", line, re.I):
                print(repr(line.strip()), "=>", convert_marks(line.strip()))


if __name__ == "__main__":
    main()
