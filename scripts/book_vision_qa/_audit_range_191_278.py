#!/usr/bin/env python3
"""Structural+content audit for Book Vision QA pages 191-278."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
PDF = ROOT / "input/cefr-companion-2020/source.pdf"
RF = ROOT / "work/cefr-companion-2020/metadata/rotated_from_grok"
OUT = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision/_audit_191_278.json"


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def core_chars(body: str) -> int:
    body_core = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    body_core = re.sub(r"\*[^\n]*Page[^\n]*\*", "", body_core)
    body_core = re.sub(r"^Page \*\*\d+\*\*\s*$", "", body_core, flags=re.M)
    body_core = re.sub(r"^---+\s*$", "", body_core, flags=re.M)
    return len(body_core.strip())


def norm_words(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return {w for w in s.split() if len(w) >= 5}


def table_overlap(md_body: str, rf_text: str) -> float:
    md_table = "\n".join(ln for ln in md_body.splitlines() if ln.strip().startswith("|"))
    rw = set(re.findall(r"[a-zA-Z]{5,}", rf_text.lower()))
    mw = set(re.findall(r"[a-zA-Z]{5,}", md_table.lower()))
    if not rw:
        return 1.0
    return len(rw & mw) / len(rw)


def has_ocr_soup(body: str) -> bool:
    markers = (
        "as the lead researcher",
        "**C2 C1**",
        "or master’s dissertation",
        "or master's dissertation",
        "classroom simulation**Educational**",
        "### Mediating a text**Personal**",
        "### Mediating concepts**Personal",
    )
    return any(m in body for m in markers)


def main() -> int:
    md = MD.read_text(encoding="utf-8")
    doc = fitz.open(PDF)
    md_all_words = norm_words(md)
    rows = []

    for n in range(191, 279):
        body = page_body(md, n)
        pdf_text = doc[n - 1].get_text("text") or ""
        cc = core_chars(body)
        pdf_chars = len(pdf_text.strip())
        local = len(norm_words(pdf_text) & norm_words(body)) / max(
            1, len(norm_words(pdf_text))
        )
        global_ov = len(norm_words(pdf_text) & md_all_words) / max(
            1, len(norm_words(pdf_text))
        )
        has_table = "| Level |" in body or re.search(r"^\|.+\|$", body, re.M) is not None
        soup = has_ocr_soup(body)
        mega = len(body) > 50000
        rf_files = list(RF.glob(f"page_{n:03d}_*.md"))
        rf_ov = None
        if rf_files:
            rf_text = rf_files[0].read_text(encoding="utf-8")
            rf_ov = round(table_overlap(body, rf_text), 3)

        # classify
        if pdf_chars < 80 and cc < 80:
            cls = "blank_both"
        elif pdf_chars < 80 and cc >= 80:
            cls = "md_has_content_pdf_blank"
        elif cc < 120 and pdf_chars >= 100:
            if global_ov > 0.55:
                cls = "chrome_only_content_elsewhere"
            else:
                cls = "truly_missing"
        elif soup:
            cls = "ocr_soup"
        elif mega:
            cls = "mega_dual_emit"
        elif rf_files and rf_ov is not None and rf_ov < 0.85:
            cls = "rotated_mismatch"
        elif rf_files and rf_ov is not None and rf_ov >= 0.85:
            cls = "appendix_table_ok"
        elif has_table:
            cls = "table_present"
        elif "figure" in body.lower() or "```mermaid" in body or "![" in body:
            cls = "figure_page"
        else:
            cls = "prose_ok" if local > 0.35 or global_ov > 0.5 else "prose_weak"

        # sample missing long PDF phrases
        phrases = [
            ln.strip()
            for ln in pdf_text.splitlines()
            if len(ln.strip()) > 50
            and not re.search(r"Page\s+\d+|Companion volume", ln, re.I)
        ][:6]
        missing_local = [p for p in phrases if p.lower() not in body.lower()][:2]

        row = {
            "page": n,
            "class": cls,
            "md_core": cc,
            "md_chars": len(body),
            "pdf_chars": pdf_chars,
            "local_overlap": round(local, 3),
            "global_overlap": round(global_ov, 3),
            "has_table": has_table,
            "soup": soup,
            "mega": mega,
            "rf_overlap": rf_ov,
            "missing_local": missing_local,
        }
        rows.append(row)

    OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    from collections import Counter

    c = Counter(r["class"] for r in rows)
    print("class counts:", dict(c))
    problems = [
        r
        for r in rows
        if r["class"]
        not in (
            "appendix_table_ok",
            "prose_ok",
            "blank_both",
            "figure_page",
            "table_present",
        )
    ]
    print(f"problem-ish: {len(problems)}")
    for r in problems:
        print(
            f"  p{r['page']}: {r['class']} md_core={r['md_core']} pdf={r['pdf_chars']} "
            f"local={r['local_overlap']} rf={r['rf_overlap']}"
        )
        if r["missing_local"]:
            print("    missing:", r["missing_local"][0][:80])
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
