#!/usr/bin/env python3
"""Fix remaining soft/hard residuals on Companion deliverable (p.24/25/47)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
GOLDEN_047 = ROOT / "work/cefr-companion-2020/metadata/golden/page_047.json"
PDF_PATH = ROOT / "input/cefr-companion-2020/source.pdf"
GID = "scale_what_is_addressed_in_this_publication"


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def replace_page_region(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def pdf_p25_table_md() -> str:
    with pdfplumber.open(PDF_PATH) as pdf:
        ts = pdf.pages[24].extract_tables() or []
    chunks: list[str] = []
    for table in ts:
        if not table:
            continue
        rows = [
            [("" if c is None else str(c).replace("\n", "<br>").strip()) for c in row]
            for row in table
        ]
        w = max(len(r) for r in rows)
        rows = [r + [""] * (w - len(r)) for r in rows]
        lines = [
            "| " + " | ".join(rows[0]) + " |",
            "| " + " | ".join(["---"] * w) + " |",
        ] + ["| " + " | ".join(r) + " |" for r in rows[1:]]
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


TRAILING_P25 = """\
<!-- el:start type=prose id=prose_p025_s1 page=25 -->
In addition to Chapter 2 “Key aspects of the CEFR for teaching and learning”, and the extended illustrative descriptors included in this publication, users may wish to consult the following two fundamental policy documents related to plurilingual, intercultural and inclusive education:

- **Guide for the development and implementation of curricula for plurilingual and intercultural education** (https://rm.coe.int/16806ae621) (Beacco et al. 2016a), which constitutes an operationalisation and further development of CEFR 2001 Chapter 8 on language diversification and the curriculum;
- **Reference framework of competences for democratic culture** (https://go.coe.int/mWYUH) (Council of Europe 2018), the sources for which inspired some of the new descriptors for mediation included in this publication.

Users concerned with school education may also wish to consult the paper “Education, mobility, otherness – The mediation functions of schools”,20 which helped the conceptualisation of mediation in the descriptor development project.
<!-- el:end id=prose_p025_s1 -->

<!-- el:start type=footnote_zone id=footnote_zone_p025_s2 page=25 -->
20. Coste D. and Cavalli M. (2015) “Education, mobility, otherness – The mediation functions of schools”, Language Policy Unit, Council of Europe, Strasbourg, available at https://rm.coe.int/16807367ee.
<!-- el:end id=footnote_zone_p025_s2 -->

*Introduction ▶ Page **25***
"""


def fix_p24(body: str) -> str:
    if GID in body:
        return body
    old = (
        "<!-- db:id=table_02_summary_descriptor_changes "
        "type=table product_tier=context pages=24-25 -->"
    )
    new = (
        "<!-- db:id=table_02_summary_descriptor_changes "
        "type=table product_tier=context pages=24-25 "
        f"span_group={GID} -->\n"
        f"<!-- span:group_id={GID} role=start pages=24-25 -->"
    )
    if old in body:
        return body.replace(old, new, 1)
    needle = "id=table_02_summary_descriptor_changes page=24 -->"
    if needle in body:
        return body.replace(
            needle,
            needle + f"\n<!-- span:group_id={GID} role=start pages=24-25 -->",
            1,
        )
    return body


def fix_p25(_body: str) -> str:
    """Table continuation first, trailing prose after last table pipe (soft validator)."""
    table = pdf_p25_table_md()
    return (
        f"<!-- book-qa p25 table restore (span end of {GID}) -->\n"
        f"{table}\n\n"
        f"{TRAILING_P25}"
    )


def fix_p47(body: str) -> str:
    # PDF + inventory: "3.1. RECEPTION" (period after 1)
    body = re.sub(r"###\s*3\.1\.?\s*RECEPTION", "### 3.1. RECEPTION", body)
    body = re.sub(r"##\s*3\.1\.?\s*RECEPTION", "## 3.1. RECEPTION", body)
    return body


def fix_golden_047() -> None:
    if not GOLDEN_047.exists():
        return
    data = json.loads(GOLDEN_047.read_text(encoding="utf-8"))
    must = data.get("must_have") or []
    data["must_have"] = [
        "### 3.1. RECEPTION" if x == "### 3.1 RECEPTION" else x for x in must
    ]
    mhc = data.get("max_heading_count") or {}
    if "### 3.1 RECEPTION" in mhc:
        mhc["### 3.1. RECEPTION"] = mhc.pop("### 3.1 RECEPTION")
    data["max_heading_count"] = mhc
    data["notes"] = (
        (data.get("notes") or "")
        + " | header form matches PDF/inventory: 3.1. RECEPTION"
    ).strip(" |")
    GOLDEN_047.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    md = replace_page_region(md, 24, fix_p24(page_body(md, 24)))
    md = replace_page_region(md, 25, fix_p25(page_body(md, 25)))
    md = replace_page_region(md, 47, fix_p47(page_body(md, 47)))
    MD_PATH.write_text(md, encoding="utf-8")
    fix_golden_047()

    md2 = MD_PATH.read_text(encoding="utf-8")
    for n in (24, 25, 47):
        b = page_body(md2, n)
        after_pipe = b.rsplit("|", 1)[-1] if "|" in b else b
        print(
            f"p{n} len={len(b)} span={GID in b} "
            f"trail={'Guide for the development' in b} "
            f"hdr={'3.1. RECEPTION' in b} "
            f"after_pipe_guide={'Guide for the development' in after_pipe} "
            f"pipes={b.count('|')}"
        )


if __name__ == "__main__":
    main()
