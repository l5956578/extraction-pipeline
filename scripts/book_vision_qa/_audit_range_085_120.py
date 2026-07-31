#!/usr/bin/env python3
"""One-shot audit MD vs PDF for pages 85-120."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]


def page_body(md: str, n: int) -> str | None:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return None


def norm_words(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return {w for w in s.split() if len(w) >= 5}


def main() -> int:
    md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
        encoding="utf-8"
    )
    doc = fitz.open(ROOT / "input/cefr-companion-2020/source.pdf")
    md_all = norm_words(md)
    rows = []
    for n in range(85, 121):
        body = page_body(md, n)
        if body is None:
            rows.append({"page": n, "error": "no marker"})
            continue
        body_core = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        body_core = re.sub(r"\*[^\n]*Page[^\n]*\*", "", body_core).strip()
        pdf_text = doc[n - 1].get_text("text") or ""
        pdf_words = norm_words(pdf_text)
        local_overlap = len(pdf_words & norm_words(body)) / max(1, len(pdf_words))
        global_overlap = len(pdf_words & md_all) / max(1, len(pdf_words))
        phrases = [
            ln.strip()
            for ln in pdf_text.splitlines()
            if len(ln.strip()) > 45
            and not re.search(r"Page\s+\d+|Companion volume", ln, re.I)
        ][:8]
        missing_in_md = [p for p in phrases if p.lower() not in md.lower()]
        missing_local = [p for p in phrases if p.lower() not in body.lower()]
        has_table = "|" in body and "---" in body
        has_scale = "descriptor_scale" in body or "scale_" in body
        has_callout = body.strip().startswith(">") or "\n>" in body
        has_figure = "![" in body or "figure_" in body or "text_diagram" in body
        has_heading = bool(re.search(r"^#{1,4}\s", body, re.M))
        md_lines = [ln for ln in body.splitlines() if ln.strip()][:6]
        pdf_lines = [ln for ln in pdf_text.splitlines() if ln.strip()][:8]
        chrome_only = len(body_core) <= 120
        if chrome_only:
            if len(pdf_text.strip()) < 100:
                cls = "blank_or_cover"
            elif global_overlap > 0.55 and not missing_in_md:
                cls = "multipage_collapsed"
            elif missing_in_md:
                cls = "truly_missing"
            else:
                cls = "weak_overlap_review"
        else:
            if missing_in_md:
                cls = "content_present_partial_missing"
            else:
                cls = "content_present"
        rows.append(
            {
                "page": n,
                "md_core_chars": len(body_core),
                "pdf_chars": len(pdf_text),
                "local_overlap": round(local_overlap, 3),
                "global_overlap": round(global_overlap, 3),
                "chrome_only": chrome_only,
                "class": cls,
                "has_table": has_table,
                "has_scale": has_scale,
                "has_callout": has_callout,
                "has_figure": has_figure,
                "has_heading": has_heading,
                "missing_in_md": missing_in_md[:3],
                "missing_local_only": [p for p in missing_local if p not in missing_in_md][
                    :2
                ],
                "md_head": md_lines[:4],
                "pdf_head": pdf_lines[:5],
            }
        )

    doc.close()
    out = ROOT / "work/cefr-companion-2020/metadata/book_qa/vision/_audit_085_120.json"
    out.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    c = Counter(r.get("class", r.get("error")) for r in rows)
    print("classes", dict(c))
    for r in rows:
        if "error" in r:
            print(f"p{r['page']:03d} ERROR {r['error']}")
            continue
        print(
            f"p{r['page']:03d} {r['class']:32s} md={r['md_core_chars']:5d} "
            f"pdf={r['pdf_chars']:5d} loc={r['local_overlap']:.2f} "
            f"glob={r['global_overlap']:.2f} miss={len(r['missing_in_md'])}"
        )
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
