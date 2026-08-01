#!/usr/bin/env python3
"""Force-correct Threshold product MD example lines using PDF text-layer conversion.

SAFETY: letter-skeleton merge skips PROTECTED_SKELETONS; always re-applies
section-aware gold locks and hard-fails on residual_assertions.

Prefer `full_md_vs_pdf_intonation.py` (multi-iter residual gate) for full passes.
This script remains as a thin native-hint patch + lock wrapper.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

from gold_intonation_locks import (
    PROTECTED_SKELETONS,
    THR_MD,
    apply_section_locks,
    gold_counts,
    residual_assertions,
    strip_skel,
    sync_override_leaves,
)

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-threshold-1990/source.pdf"
MD = THR_MD

LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)


def convert_marks(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    s = re.sub(r'(^|[\s(|])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    s = re.sub(r"(^|[\s(|])['`´]+(?=[A-Za-z])", r"\1ˈ", s)
    s = re.sub(r"(^|[\s(|]),(?=[A-Za-z])", r"\1ˎ", s)
    s = re.sub(r"(^|[\s(|])\.(?=[A-Za-z])", r"\1·", s)
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    s = re.sub(r"\s+[I|]\s+", " | ", s)
    s = s.replace('"', "ˇ")
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


def collect_gold() -> list[str]:
    doc = fitz.open(PDF)
    gold = []
    for leaf in LEAVES:
        if leaf > doc.page_count:
            continue
        for raw in doc[leaf - 1].get_text("text").splitlines():
            line = raw.strip()
            if not line:
                continue
            if not re.search(r"['`,\.\"][A-Za-z]|[A-Za-z]['\"]", line) and '"' not in line:
                continue
            if len(line) < 4 or len(line) > 100:
                continue
            if line.count("'") + line.count(",") + line.count(".") + line.count('"') < 1:
                continue
            g = convert_marks(line)
            if re.search(r"[ˈˎˋˏˊˇ·]", g) and re.search(r"[A-Za-z]{2,}", g):
                gold.append(g)
    seen = set()
    out = []
    for g in gold:
        k = strip_skel(g)
        if k in seen or len(k) < 6 or k in PROTECTED_SKELETONS:
            continue
        seen.add(k)
        out.append(g)
    doc.close()
    return out


def replace_blockquote_lines(md: str, gold: list[str]) -> tuple[str, int]:
    """Replace > example lines when letter-skeleton matches gold.

    Skips PROTECTED multi-form pairs (bedroom, train, Did/Please tags, …).
    """
    gold_map = {strip_skel(g): g for g in gold}
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        prefix, body = m.group(1), m.group(2).strip()
        key = strip_skel(body)
        if key in PROTECTED_SKELETONS:
            return m.group(0)
        if key in gold_map:
            g = gold_map[key]
            if g != body and re.search(r"[ˈˎˋˏˊˇ·]", g):
                n += 1
                return f"{prefix}{g}"
        return m.group(0)

    md2 = re.sub(r"^(>\s*)(.+)$", repl, md, flags=re.M)
    return md2, n


def systematic_fixes(md: str) -> tuple[str, int]:
    pairs = [
        (r"\bthe ·owner\b", "the ˎowner"),
        (r"\bmy ·dog\b", "my ˎdog"),
        (r"ˈNo it ˋisn(['’]?t)", r"ˈNo it ˇisn\1"),
        (r"ˈYes you ˋdid\b", "ˈYes you ˇdid"),
        (r"The \" animal", "The ˇanimal"),
        (r'The " animal', "The ˇanimal"),
    ]
    n = 0
    for a, b in pairs:
        md2, c = re.subn(a, b, md)
        if c:
            md = md2
            n += c
    return md, n


def main() -> None:
    print(
        "NOTE: prefer full_md_vs_pdf_intonation.py for full multi-iter passes; "
        "this script is a native-hint patch + gold-lock wrapper."
    )
    gold = collect_gold()
    print(f"gold examples (non-protected): {len(gold)}")
    md = MD.read_text(encoding="utf-8")
    md, n1 = replace_blockquote_lines(md, gold)
    md, n2 = systematic_fixes(md)
    md, lock_ops = apply_section_locks(md)
    print(f"blockquote replacements: {n1}, systematic: {n2}, locks: {lock_ops or ['noop']}")
    MD.write_text(md, encoding="utf-8")
    sync_override_leaves([34, 35])

    fails = residual_assertions(md)
    counts = gold_counts(md)
    for s in [
        "ˈThis is the ˎbedroom",
        "ˋThis is the ·bedroom",
        "The ˈtrain has ˎleft",
        "The ·train ˋhas ·left",
        "ˊDid you ˎsee him",
        "ˈPlease can you",
        "ˎowner",
        "my ˎdog",
    ]:
        print(f"  {s!r}: {counts.get(s, md.count(s))}")
    if fails:
        print("RESIDUAL FAIL:")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    print("residual assertions: PASS")


if __name__ == "__main__":
    main()
