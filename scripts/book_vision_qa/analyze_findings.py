"""Summarize structural findings; separate rotated-scale pages from real prose gaps."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
md = (ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md").read_text(
    encoding="utf-8"
)
pdf = fitz.open(ROOT / "input/cefr-companion-2020/source.pdf")
findings = [
    json.loads(l)
    for l in (
        ROOT
        / "work/cefr-companion-2020/metadata/book_qa/structural_findings.jsonl"
    )
    .read_text(encoding="utf-8")
    .splitlines()
    if l.strip()
]


def page_body(n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


# Pages that are primarily rotated descriptor tables (vision MD expected)
rotated_ish = set()
for n in range(1, 279):
    body = page_body(n)
    if re.search(r"rotated|scale_.*\n\|", body) and body.count("| ---") >= 1:
        # many scale pages
        pass
    # thin MD + thin PDF extract = cover/blank
    pt = pdf[n - 1].get_text("text") or ""
    if len(pt.strip()) < 80 and len(body.strip()) < 80:
        rotated_ish.add(n)  # blank-ish

by_page: dict[int, list] = defaultdict(list)
for f in findings:
    by_page[f["page"]].append(f)

print("=== critical missing_required_phrase ===")
for f in findings:
    if f["kind"] == "missing_required_phrase":
        print(f)

print("\n=== post_diagram soup ===")
for f in findings:
    if f["kind"] == "post_diagram_leaf_soup":
        print(f)

print("\n=== empty MD pages (sample analysis) ===")
for p in sorted({f["page"] for f in findings if f["kind"] == "empty_or_near_empty_md"})[
    :15
]:
    body = page_body(p)
    pt = pdf[p - 1].get_text("text") or ""
    print(
        f"p{p}: pdf={len(pt)} md={len(body)} pipes={body.count('|')} "
        f"scales={'scale_' in body}"
    )

print("\n=== major/critical vocab missing (non-scale-looking) ===")
for p in sorted(by_page):
    kinds = {x["kind"] for x in by_page[p]}
    if "missing_pdf_vocabulary" not in kinds:
        continue
    body = page_body(p)
    if body.count("| ---") >= 2 and "scale_" in body:
        continue  # likely scale page false positive
    if len(body) > 1500:
        continue
    print(p, [x["kind"] for x in by_page[p]], "mdlen", len(body))

pdf.close()
