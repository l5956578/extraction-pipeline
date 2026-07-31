#!/usr/bin/env python3
"""Apply user temp table fix for acknowledgements participants.

Temp file page markers are early/offset; map tables to PDF-aligned pages:
  temp p14 (stages tail + org table + thanks) → MD p14 (after live prologue) + p15
  temp p15 (PRO-Sign + Algeria…) → MD p16
  temp p16 → MD p17
  temp p17 → MD p18
  temp p18 → MD p19
  temp p19 (Spain EOI + Sweden…) → MD p20 (split EOI/Sweden as needed)

User note: page numbers in temp are not final; tables > prose density.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
TEMP = Path(r"D:\y\lang-platform\temp only 14-20.txt")


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def strip_chrome(raw: str) -> str:
    b = raw.strip().replace("\t", " ")
    b = re.sub(r"^\*Page[^\n]*\*\s*\n?", "", b, count=1, flags=re.I)
    b = re.sub(
        r"^\*Preface with acknowledgements[^\n]*\*\s*\n?",
        "",
        b,
        count=1,
        flags=re.I,
    )
    b = b.replace("| Equalls", "| Eaquals")
    return b.strip()


def wrap(page: int, inner: str, chrome: str) -> str:
    return (
        f"<!-- el:start type=prose id=prose_p{page:03d}_ack page={page} -->\n"
        f"<!-- book-qa: user temp only 14-20 tables (PDF-aligned remap) -->\n"
        f"{inner.strip()}\n"
        f"<!-- el:end id=prose_p{page:03d}_ack -->\n\n"
        f"{chrome}\n"
    )


def main() -> None:
    md = MD.read_text(encoding="utf-8")

    # Prefer clean prologue from pre-table version 029 if present
    prologue = ""
    v029 = ROOT / "output/cefr-companion-2020/versions/029/CEFR_Companion_Volume.md"
    if v029.exists():
        vmd = v029.read_text(encoding="utf-8")
        live14 = page_body(vmd, 14)
        stages_at = live14.find("The entire process of updating")
        if stages_at > 0:
            prologue = live14[:stages_at].rstrip()
    if not prologue or "modality-inclusive" not in prologue:
        live14 = page_body(md, 14)
        stages_at = live14.find("The entire process of updating")
        if stages_at < 0:
            stages_at = live14.find("Stage 1")
        prologue = live14[:stages_at].rstrip() if stages_at and stages_at > 0 else ""
    if "<!-- el:start" in prologue and "<!-- el:end" not in prologue:
        m = re.search(r"id=(prose_p014[^>\s]+)", prologue)
        eid = m.group(1) if m else "prose_p014_s0"
        prologue = prologue + f"\n<!-- el:end id={eid} -->"

    tmp = TEMP.read_text(encoding="utf-8")
    parts = re.split(r"<!-- page:(\d+) -->", tmp)
    preamble = strip_chrome(parts[0])
    T: dict[int, str] = {}
    for i in range(1, len(parts), 2):
        T[int(parts[i])] = strip_chrome(parts[i + 1])

    # p14: prologue + stages 1–5 (preamble + stage portion of T[14] before org table)
    t14 = T.get(14, "")
    org_at = t14.find("| Organization")
    if org_at < 0:
        org_at = t14.find("| Organization / Project")
    if org_at < 0:
        org_at = t14.find("ALTE")
    stages = (preamble + "\n\n" + (t14[:org_at] if org_at > 0 else t14)).strip()
    org_and_thanks = t14[org_at:].strip() if org_at > 0 else ""

    p14 = (
        (prologue + "\n\n" if prologue else "")
        + "<!-- el:start type=prose id=prose_p014_stages page=14 -->\n"
        + "<!-- book-qa: stages from user temp -->\n"
        + stages
        + "\n<!-- el:end id=prose_p014_stages -->\n\n"
        + "*Page **14** ▶ **CEFR – Companion volume***\n"
    )
    md = replace_page(md, 14, p14)

    # p15: org table + thanks (PDF p15 has ALTE etc.)
    md = replace_page(
        md,
        15,
        wrap(
            15,
            org_and_thanks,
            "*Preface with acknowledgements ▶ Page **15***",
        ),
    )

    # p16: temp p15 (PRO-Sign + Algeria…) — PDF Algeria on 16
    md = replace_page(
        md,
        16,
        wrap(16, T.get(15, ""), "*Page **16** ▶ **CEFR – Companion volume***"),
    )
    # p17 ← temp p16
    md = replace_page(
        md,
        17,
        wrap(
            17,
            T.get(16, ""),
            "*Preface with acknowledgements ▶ Page **17***",
        ),
    )
    # p18 ← temp p17
    md = replace_page(
        md,
        18,
        wrap(18, T.get(17, ""), "*Page **18** ▶ **CEFR – Companion volume***"),
    )
    # p19 ← temp p18
    md = replace_page(
        md,
        19,
        wrap(
            19,
            T.get(18, ""),
            "*Preface with acknowledgements ▶ Page **19***",
        ),
    )
    # p20 ← temp p19 (Spain EOI + Sweden…Uruguay)
    md = replace_page(
        md,
        20,
        wrap(20, T.get(19, ""), "*Page **20** ▶ **CEFR – Companion volume***"),
    )

    MD.write_text(md, encoding="utf-8")
    md2 = MD.read_text(encoding="utf-8")
    for n in range(14, 21):
        b = page_body(md2, n)
        print(
            f"p{n} len={len(b)} "
            f"ALTE={'ALTE' in b} Algeria={'Algeria' in b} "
            f"Sweden={'Sweden' in b} Stage={'Stage 1' in b or 'Stage 1:' in b}"
        )


if __name__ == "__main__":
    main()
