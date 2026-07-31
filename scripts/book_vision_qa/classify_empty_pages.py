#!/usr/bin/env python3
"""Classify chrome-only MD pages: multipage-collapsed vs truly missing content."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def norm_words(s: str) -> set[str]:
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    return {w for w in s.split() if len(w) >= 5}


def main() -> int:
    md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
        encoding="utf-8"
    )
    doc = fitz.open(ROOT / "input/cefr-companion-2020/source.pdf")
    md_all_words = norm_words(md)

    rows = []
    for n in range(1, len(doc) + 1):
        body = page_body(md, n)
        # chrome-only heuristic
        body_core = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        body_core = re.sub(r"\*[^\n]*Page[^\n]*\*", "", body_core)
        body_core = body_core.strip()
        if len(body_core) > 120:
            continue
        pdf_text = doc[n - 1].get_text("text") or ""
        if len(pdf_text.strip()) < 100:
            rows.append(
                {
                    "page": n,
                    "class": "blank_or_cover",
                    "pdf_chars": len(pdf_text),
                    "md_core_chars": len(body_core),
                }
            )
            continue
        pdf_words = norm_words(pdf_text)
        overlap = len(pdf_words & md_all_words) / max(1, len(pdf_words))
        # sample distinctive phrases from PDF (length > 40)
        phrases = [
            ln.strip()
            for ln in pdf_text.splitlines()
            if len(ln.strip()) > 50 and not re.search(r"Page\s+\d+|Companion", ln)
        ][:5]
        missing_phrases = [p for p in phrases if p.lower() not in md.lower()]
        if overlap > 0.55 and not missing_phrases:
            cls = "multipage_collapsed_content_elsewhere"
        elif missing_phrases:
            cls = "truly_missing_or_paraphrased"
        else:
            cls = "weak_overlap_review"
        rows.append(
            {
                "page": n,
                "class": cls,
                "pdf_chars": len(pdf_text),
                "md_core_chars": len(body_core),
                "vocab_overlap": round(overlap, 3),
                "sample_missing_phrases": missing_phrases[:3],
            }
        )

    doc.close()
    out = ROOT / "work/cefr-companion-2020/metadata/book_qa/empty_page_classification.json"
    out.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    from collections import Counter

    c = Counter(r["class"] for r in rows)
    print("classes", dict(c))
    print("truly_missing sample:")
    for r in rows:
        if r["class"] == "truly_missing_or_paraphrased":
            print(r["page"], r.get("sample_missing_phrases", [])[:1])
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
