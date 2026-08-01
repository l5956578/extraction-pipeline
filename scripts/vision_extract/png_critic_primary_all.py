#!/usr/bin/env python3
"""PNG-critic fix pass for Threshold primary intonation leaves.

Applies only high-confidence glyph fixes with PNG/PDF evidence:
  - mid-word ASCII comma residue → ˎ (low fall mid-syllable)
  - secondary-stress ASCII hyphen → · on known exponent example lines
  - broken Thatˈll contractions → That'll
  - do NOT touch gold 1.1.3–1.4.2.2 multi-form locks

After product MD write, re-apply gold locks + residual_assertions.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gold_intonation_locks import (  # noqa: E402
    THR_MD,
    THR_OV,
    apply_section_locks,
    residual_assertions,
    gold_counts,
    sync_override_leaves,
)

LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)

# Mid-word ASCII comma → low fall (PDF ar,rive; PNG below-line fall). Never invent ˏ.
MID_COMMA_WORDS = [
    ("ar,rive", "arˎrive"),
    ("Ar,rive", "Arˎrive"),
    ("pre,fer", "preˎfer"),
    ("Pre,fer", "Preˎfer"),
    ("at,tention", "atˎtention"),
    ("At,tention", "Atˎtention"),
    ("ad,dress", "adˎdress"),
    ("Ad,dress", "Adˎdress"),
    ("down,stairs", "downˎstairs"),
    ("up,stairs", "upˎstairs"),
    ("maga,zines", "magaˎzines"),
    ("de,clare", "deˎclare"),
    ("de,cided", "deˎcided"),
    ("De,cided", "Deˎcided"),
    ("a,gree", "aˎgree"),  # only mid-word form if residual
    ("cor,rect", "corˎrect"),
    ("E,xactly", "Eˎxactly"),
    ("e,xactly", "eˎxactly"),
    ("o,pinion", "oˎpinion"),
    ("a,fraid", "aˎfraid"),
]

# Secondary stress often OCR'd as ASCII hyphen before syllable on example lines.
# Only replace when line already carries Unicode tones (avoid ice-cream etc.).
SEC_DASH = [
    (r"(Don't you )-think", r"\1·think"),
    (r"(she is )-dead", r"\1·dead"),
    (r"(When )-have we", r"\1·have we"),
    (r"(Would you )-like", r"\1·like"),
    (r"(like )-this\?", r"\1·this?"),
    (r"(do you )-mean", r"\1·mean"),
    (r"(Can you )-call me", r"\1·call me"),
    (r"(ˎsix, )-please", r"\1·please"),
    (r"(Shall we )-sit", r"\1·sit"),
    (r"(you )-work ", r"\1·work "),
    (r"(Don't you )-eat", r"\1·eat"),
    (r"(Do you )-know", r"\1·know"),
    (r"(Do you )-like", r"\1·like"),
    (r"(Could you )-open", r"\1·open"),
    (r"(Would you )-close", r"\1·close"),
    (r"(Would you )-come", r"\1·come"),
    (r"(May \| )-have", r"\1·have"),
    (r"(May I )-have", r"\1·have"),
    (r"(May \| )-drive", r"\1·drive"),
    (r"(May I )-drive", r"\1·drive"),
    (r"(Do )-sit ", r"\1·sit "),
    (r"(Can you )-do ", r"\1·do "),
    (r"(How )-much ", r"\1·much "),
    (r"(How )-far ", r"\1·far "),
    (r"(All the )-guests", r"\1·guests"),
    (r"(other )-leg", r"\1·leg"),
    (r"(strange )-man", r"\1·man"),
    (r"( -last night)", r" ·last night"),
    (r"( -last year)", r" ·last year"),
    (r"( -please\?)", r" ·please?"),
    (r"( -please\.)", r" ·please."),
    (r"( -please,)", r" ·please,"),
    (r"( -doctor)", r" ·doctor"),
    (r"( -course )", r" ·course "),
    (r"( -dinner)", r" ·dinner"),
    (r"( -London)", r" ·London"),
    (r"( -class)", r" ·class"),
    (r"( -work\.)", r" ·work."),
    (r"( -pass )", r" ·pass "),
    (r"( -where )", r" ·where "),
    (r"( -those )", r" ·those "),
    (r"( -first )", r" ·first "),
    (r"( -next )", r" ·next "),
    (r"( -shade)", r" ·shade"),
    (r"( -mean )", r" ·mean "),
    (r"( -little\.)", r" ·little."),
    (r"( -year\.)", r" ·year."),
    (r"( -ago\.)", r" ·ago."),
    (r"( -TˎV)", r" ·TˎV"),
    (r"( -soup)", r" ·soup"),
    (r"( -come\.)", r" ·come."),
    (r"( -there\.)", r" ·there."),
    (r"( -now\.)", r" ·now."),
    (r"( -hard\.)", r" ·hard."),
    (r"( -Please)", r" ·Please"),
    (r"( -Thank )", r" ·Thank "),
]

# Exact phrase PNG-verified / high-confidence from prior gold + mid-comma PDF
EXACT_PHRASE_FIXES = [
    # broken contraction tone
    ("Thatˈll", "That'll"),
    ("thatˈll", "that'll"),
    ("Iˈlike", "I ˈlike"),  # space + head if glued
    # known mid-comma phrases (also covered by MID_COMMA_WORDS)
    ("ar,rive", "arˎrive"),
    ("pre,fer", "preˎfer"),
    ("at,tention", "atˎtention"),
    ("ad,dress", "adˎdress"),
    ("down,stairs", "downˎstairs"),
    ("up,stairs", "upˎstairs"),
    ("maga,zines", "magaˎzines"),
    ("de,clare", "deˎclare"),
    ("de,cided", "deˎcided"),
]


def is_primary_page_body_line(line: str, in_primary: bool) -> bool:
    return in_primary


def page_leaf_map(md: str) -> dict[int, tuple[int, int]]:
    """doc page → (start, end) spans; also return leaf via doc+6."""
    spans: dict[int, tuple[int, int]] = {}
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        doc = int(m.group(1))
        start = m.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(md)
        spans[doc] = (start, end)
    return spans


def fix_text(text: str, primary_only: bool = False) -> tuple[str, list[str]]:
    ops: list[str] = []
    if not primary_only:
        for a, b in EXACT_PHRASE_FIXES:
            c = text.count(a)
            if c:
                text = text.replace(a, b)
                ops.append(f"{a!r}→{b!r} x{c}")
        for a, b in MID_COMMA_WORDS:
            c = text.count(a)
            if c and a not in dict(EXACT_PHRASE_FIXES):
                text = text.replace(a, b)
                ops.append(f"midcomma {a}→{b} x{c}")
        lines = []
        n_dash = 0
        for ln in text.splitlines(keepends=True):
            if re.search(r"[ˈˎˋˏˊˇ·]", ln) or ln.lstrip().startswith(">"):
                orig = ln
                for pat, rep in SEC_DASH:
                    ln2 = re.sub(pat, rep, ln)
                    if ln2 != ln:
                        n_dash += 1
                        ln = ln2
                lines.append(ln)
            else:
                lines.append(ln)
        if n_dash:
            text = "".join(lines)
            ops.append(f"sec_dash fixes lines~{n_dash}")
        else:
            text = "".join(lines) if lines else text
        return text, ops

    # primary-only: only rewrite bodies for primary leaves
    spans = page_leaf_map(text)
    primary_docs = {leaf - 6 for leaf in LEAVES}
    # rebuild by splicing
    # simpler: apply global but only within primary doc page spans
    chars = list(text)
    # work on string with span-local replace
    pieces = []
    last = 0
    markers = list(re.finditer(r"<!-- page:(\d+) -->", text))
    if not markers:
        return fix_text(text, primary_only=False)

    # content before first page marker
    pieces.append(text[: markers[0].start()])
    for i, m in enumerate(markers):
        doc = int(m.group(1))
        start = m.start()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        chunk = text[start:end]
        if doc in primary_docs:
            chunk2, cops = fix_text(chunk, primary_only=False)
            if cops:
                ops.append(f"doc{doc}/leaf{doc+6}: {', '.join(cops)}")
            pieces.append(chunk2)
        else:
            pieces.append(chunk)
    return "".join(pieces), ops


def apply_to_file(path: Path, primary_only: bool = True) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    fixed, ops = fix_text(raw, primary_only=primary_only)
    if fixed != raw:
        path.write_text(fixed, encoding="utf-8")
    return ops


def main() -> None:
    print("=== PNG critic primary fix pass ===")
    ops = apply_to_file(THR_MD, primary_only=True)
    for o in ops:
        print(f"  MD: {o}")
    if not ops:
        print("  MD: no changes")

    n_ov = 0
    for leaf in LEAVES:
        p = THR_OV / f"page_{leaf:03d}.md"
        if not p.exists():
            continue
        o = apply_to_file(p, primary_only=False)
        if o:
            n_ov += 1
            print(f"  OV leaf {leaf}: {o}")
    print(f"overrides touched: {n_ov}")

    # re-lock gold + residual
    md = THR_MD.read_text(encoding="utf-8")
    md2, gops = apply_section_locks(md)
    if md2 != md:
        THR_MD.write_text(md2, encoding="utf-8")
        print("gold ops:", gops)
    fails = residual_assertions(THR_MD.read_text(encoding="utf-8"))
    print("counts:", gold_counts(THR_MD.read_text(encoding="utf-8")))
    print("residual:", fails or "PASS")
    sync_override_leaves([34, 35])


if __name__ == "__main__":
    main()
