#!/usr/bin/env python3
"""Scan Threshold/Waystage for pages that need high-precision intonation multipass."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Unicode tone inventory + OCR leftovers
UNI = "ˈˎˋˏˊˇ·ˌ"
# Book OCR often uses ' , · before syllables
OCR_MARK = re.compile(
    r"(?:^|[\s>])['`´][A-Za-z]"  # high mark before word
    r"|(?:^|[\s>]),[A-Za-z]"  # low mark as comma
    r"|(?:^|[\s>])·[A-Za-z]"
    r"|[ˎˋˊˏˇˈˌ]"
)


def pdf_to_doc(job: str, pdf: int) -> int | None:
    if job.startswith("cefr-threshold") or job.startswith("cefr-waystage"):
        return None if pdf < 7 else pdf - 6
    return pdf


def page_has_intonation(text: str) -> bool:
    if any(c in text for c in UNI):
        return True
    if OCR_MARK.search(text):
        # avoid false positives on pure apostrophe contractions without mark spacing
        if re.search(r"['`][A-Z]|,\w|·\w|[ˎˋˈˇ]", text):
            return True
    return False


def scan(job: str, n: int) -> list[tuple[int, int | None, str]]:
    ov = ROOT / "work" / job / "page_overrides"
    ocr = ROOT / "work" / job / "page_ocr"
    hits = []
    for i in range(1, n + 1):
        parts = []
        for base in (ov, ocr):
            p = base / f"page_{i:03d}.md" if base == ov else base / f"page_{i:03d}.txt"
            if base.name == "page_overrides":
                p = ov / f"page_{i:03d}.md"
            else:
                p = ocr / f"page_{i:03d}.txt"
            if p.exists():
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
        blob = "\n".join(parts)
        if page_has_intonation(blob):
            hits.append((i, pdf_to_doc(job, i), "yes"))
    return hits


def main() -> None:
    for job, n in [("cefr-threshold-1990", 192), ("cefr-waystage-1990", 120)]:
        hits = scan(job, n)
        print(f"\n=== {job}: {len(hits)} pages ===")
        # group consecutive
        if not hits:
            continue
        start = prev = hits[0][0]
        docs = [hits[0][1]]
        for leaf, doc, _ in hits[1:]:
            if leaf == prev + 1:
                prev = leaf
                docs.append(doc)
            else:
                print(f"  PDF {start}-{prev}  doc {docs[0]}-{docs[-1]}")
                start = prev = leaf
                docs = [doc]
        print(f"  PDF {start}-{prev}  doc {docs[0]}-{docs[-1]}")
        print("  leaves:", ",".join(str(h[0]) for h in hits))


if __name__ == "__main__":
    main()
