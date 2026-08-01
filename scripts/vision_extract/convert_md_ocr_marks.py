#!/usr/bin/env python3
"""Convert OCR/Paper-Capture style intonation marks already present in MD to Unicode.

Use for Waystage (image PDF, OCR leftovers) and residual Threshold lines.
Only rewrites lines that already look mark-bearing — does not invent marks.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def convert_marks(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\$+(?=[A-Za-z])", "ˎ", s)
    # fall-rise
    s = re.sub(r'(^|[\s(|/>*])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    # high mark at token start — NOT mid-word contractions (don't, it's, learner's)
    s = re.sub(r"(^|[\s(|/>*])['`´]+(?=[A-Za-z])", r"\1ˈ", s)
    # low fall comma at token start
    s = re.sub(r"(^|[\s(|/>*]),(?=[A-Za-z])", r"\1ˎ", s)
    # mid-word comma LF
    s = re.sub(r"(?<=[A-Za-z]),(?=[A-Za-z])", "ˎ", s)
    # mid-dot at token start
    s = re.sub(r"(^|[\s(|/>*])\.(?=[A-Za-z])", r"\1·", s)
    # mid-word period secondary
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    s = s.replace("/.", "/·")
    s = re.sub(r"\s+I\s+", " | ", s)
    s = re.sub(r"(?<=[\s(|])\"+(?=[A-Za-z])", "ˇ", s)
    s = re.sub(r" {2,}", " ", s)
    return s


def line_looks_mark_bearing(line: str) -> bool:
    """True if line has OCR tone encoding (not ordinary English apostrophes alone)."""
    # strong signals
    if re.search(r"(^|[\s>|*(])['`´][A-Za-z]", line):
        # exclude pure quote-style 'word' pairs that are not tones
        if re.search(r"(^|[\s>|*(])['`´][A-Za-z].*['`´](\s|$|[.,;:)])", line):
            # still might be tones; keep if also has ,word or .word
            if not re.search(r"(^|[\s>|*(]),[A-Za-z]|(^|[\s>|*(])\.[A-Za-z]|[A-Za-z],[A-Za-z]", line):
                # 'reading' and 'listening' style — skip if multiple quoted words in prose
                if line.count("'") >= 2 and not re.search(r"[ˎˋˈ]|,[A-Za-z]|\.[A-Za-z]", line):
                    return False
        return True
    if re.search(r"(^|[\s>|*(]),[A-Za-z]", line):
        return True
    if re.search(r"(^|[\s>|*(])\.[A-Za-z]", line):
        return True
    if re.search(r"[A-Za-z],[A-Za-z]", line) and re.search(
        r"[A-Za-z]{2,},[A-Za-z]{2,}", line
    ):
        # ad,dress style — careful with lists
        return True
    if re.search(r'(^|[\s>|*(])"[A-Za-z]', line):
        return True
    return False


def convert_file(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    n = 0
    out = []
    for line in lines:
        # don't convert HTML comments / front matter noise
        if line.lstrip().startswith("<!--"):
            out.append(line)
            continue
        body = line.rstrip("\n\r")
        nl = line[len(body) :]
        if line_looks_mark_bearing(body):
            conv = convert_marks(body)
            if conv != body:
                n += 1
                out.append(conv + nl)
                continue
        out.append(line)
    new = "".join(out)
    # systematic leftovers
    pairs = [
        (r"\bthe ·owner\b", "the ˎowner"),
        (r"\bmy ·dog\b", "my ˎdog"),
        (r"ˈNo it ˋisn(['’]?t)", r"ˈNo it ˇisn\1"),
        (r"(?<=\s)ˌ(?=[A-Za-z])", "ˎ"),
    ]
    n2 = 0
    for a, b in pairs:
        new, c = re.subn(a, b, new)
        n2 += c
    if n or n2:
        path.write_text(new, encoding="utf-8")
    return n, n2


def convert_dir(d: Path, pattern: str = "page_*.md") -> int:
    total = 0
    if not d.exists():
        return 0
    for p in sorted(d.glob(pattern)):
        n, n2 = convert_file(p)
        if n or n2:
            print(f"  {p.name}: lines={n} sys={n2}")
            total += n + n2
    return total


def main() -> None:
    print(
        "NOTE: OCR convert is ASCII→tone hint only. "
        "After Threshold product write, gold locks + residual gate run."
    )
    targets = [
        ROOT / "output/cefr-waystage-1990/Waystage_1990.md",
        ROOT / "output/cefr-threshold-1990/Threshold_1990.md",
    ]
    for t in targets:
        if t.exists():
            n, n2 = convert_file(t)
            print(f"{t.name}: converted_lines={n} systematic={n2}")
            if "Threshold" in t.name:
                try:
                    from gold_intonation_locks import (
                        apply_section_locks,
                        residual_assertions,
                    )
                    import sys

                    md = t.read_text(encoding="utf-8")
                    md, ops = apply_section_locks(md)
                    t.write_text(md, encoding="utf-8")
                    print(f"  gold locks: {ops or ['noop']}")
                    fails = residual_assertions(md)
                    if fails:
                        print("  RESIDUAL FAIL:")
                        for f in fails:
                            print(f"    - {f}")
                        sys.exit(1)
                    print("  residual: PASS")
                except ImportError:
                    print("  WARNING: gold_intonation_locks unavailable")

    print("Waystage overrides:")
    convert_dir(ROOT / "work/cefr-waystage-1990/page_overrides")
    print("Threshold overrides:")
    convert_dir(ROOT / "work/cefr-threshold-1990/page_overrides")
    print("DONE")


if __name__ == "__main__":
    main()
