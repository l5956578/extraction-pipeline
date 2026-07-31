#!/usr/bin/env python3
"""Book-wide structural PDF ↔ MD audit (no pipeline re-extract).

Compares every page of the Companion PDF to the live deliverable MD.
Emits work/<job>/metadata/book_qa/structural_findings.jsonl + summary.json

This is the first pass before Vision; flags missing bulk text, empty pages,
post-diagram leaf soup, and extreme length mismatches for human/Vision review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _page_bodies_md(md: str) -> dict[int, str]:
    """Body for page N = content before <!-- page:N --> (pipeline convention)."""
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    out: dict[int, str] = {}
    for i, m in enumerate(markers):
        n = int(m.group(1))
        start = markers[i - 1].end() if i else 0
        out[n] = md[start : m.start()]
    return out


def _normalize(s: str) -> str:
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"!\[.*?\]\([^)]+\)", " ", s)
    s = re.sub(r"[|`#>*_\-\[\]()]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def _word_set(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{4,}", _normalize(s))}


# Leaves that must not appear as bare lines after ```text fences
_LEAF_SOUP = re.compile(
    r"(?m)^(?:\*\*)?(?:"
    r"Public announcements|Planning|Compensating|Monitoring and repair|"
    r"Addressing audiences|Creative writing|Reports and essays|"
    r"Reception activities|Reception strategies|Production activities|"
    r"Production strategies|Interaction activities|Interaction strategies"
    r")(?:\*\*)?\s*$"
)


def audit_page(page: int, pdf_text: str, md_body: str) -> list[dict]:
    findings: list[dict] = []
    pdf_n = _normalize(pdf_text)
    md_n = _normalize(md_body)
    pdf_words = _word_set(pdf_text)
    md_words = _word_set(md_body)
    pdf_chars = len(pdf_n)
    md_chars = len(md_n)

    if pdf_chars > 200 and md_chars < 80:
        findings.append(
            {
                "page": page,
                "severity": "critical",
                "kind": "empty_or_near_empty_md",
                "detail": f"PDF ~{pdf_chars} norm chars; MD body ~{md_chars}",
            }
        )

    # Significant PDF vocabulary missing from MD (missing paragraphs)
    if len(pdf_words) > 40:
        missing = pdf_words - md_words
        ratio = len(missing) / max(1, len(pdf_words))
        if ratio > 0.35 and len(missing) > 25:
            sample = sorted(missing)[:12]
            findings.append(
                {
                    "page": page,
                    "severity": "critical" if ratio > 0.5 else "major",
                    "kind": "missing_pdf_vocabulary",
                    "detail": (
                        f"~{ratio:.0%} of PDF content words absent from MD "
                        f"({len(missing)} words). sample={sample}"
                    ),
                }
            )

    # Extra soup after text_diagram fence
    if "```" in md_body:
        # after last closing fence before el:end
        parts = md_body.split("```")
        if len(parts) >= 3:
            after = parts[-1] if not parts[-1].strip().startswith("text") else ""
            # parts: before, fence content, after, ...
            # find after each text fence
            i = 0
            while i < len(parts) - 1:
                if parts[i].rstrip().endswith("") and i + 1 < len(parts):
                    # odd indices are fence bodies when split by ```
                    pass
                i += 1
            for j in range(1, len(parts), 2):
                # content after this fence is parts[j+1] until next
                if j + 1 < len(parts):
                    after_fence = parts[j + 1]
                    # only until el:end
                    after_fence = after_fence.split("<!-- el:end")[0]
                    soup = _LEAF_SOUP.findall(after_fence)
                    # findall with alternation returns the group - fix
                    soup_lines = [
                        ln.strip()
                        for ln in after_fence.splitlines()
                        if _LEAF_SOUP.match(ln.strip() or "")
                    ]
                    if soup_lines:
                        findings.append(
                            {
                                "page": page,
                                "severity": "major",
                                "kind": "post_diagram_leaf_soup",
                                "detail": f"bare dual-emit lines after ```: {soup_lines[:8]}",
                            }
                        )
                        break

    # Known critical phrases that must exist on specific pages (from PDF ground truth)
    page_must = {
        61: [
            ("rather than dialogue", "trailing oral-production section after Fig 12"),
            ("3.2.1", "section 3.2.1 Production activities"),
        ],
        47: [
            ("Reception involves", "3.1 reception lead after Fig 11"),
        ],
        71: [
            ("3.3.1", "section 3.3.1 Interaction activities"),
        ],
    }
    for needle, label in page_must.get(page, []):
        if needle.lower() not in md_body.lower() and needle.lower() in pdf_text.lower():
            findings.append(
                {
                    "page": page,
                    "severity": "critical",
                    "kind": "missing_required_phrase",
                    "detail": f"PDF has {label!r} ({needle!r}); MD does not",
                }
            )

    # MD much longer than PDF → possible dual-emit bloat
    if pdf_chars > 100 and md_chars > pdf_chars * 2.2:
        findings.append(
            {
                "page": page,
                "severity": "minor",
                "kind": "md_much_longer_than_pdf",
                "detail": f"MD norm {md_chars} vs PDF {pdf_chars} (possible dual-emit)",
            }
        )

    return findings


def main() -> int:
    from pipeline.bootstrap import bootstrap_job
    import fitz

    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default="cefr-companion-2020")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=0, help="0 = last page")
    args = parser.parse_args()
    ctx = bootstrap_job(args.job, force_draft=True)

    md_path = ctx.final_dir / ctx.markdown_name
    md = md_path.read_text(encoding="utf-8")
    bodies = _page_bodies_md(md)

    doc = fitz.open(ctx.pdf_path)
    end = args.end or len(doc)
    out_dir = ctx.metadata_dir / "book_qa"
    out_dir.mkdir(parents=True, exist_ok=True)
    findings_path = out_dir / "structural_findings.jsonl"
    all_f: list[dict] = []

    with findings_path.open("w", encoding="utf-8") as fh:
        for page in range(args.start, end + 1):
            pdf_text = doc[page - 1].get_text("text") or ""
            md_body = bodies.get(page, "")
            page_findings = audit_page(page, pdf_text, md_body)
            for f in page_findings:
                fh.write(json.dumps(f, ensure_ascii=False) + "\n")
                all_f.append(f)
            if page % 50 == 0:
                print(f"… audited through page {page}", flush=True)

    doc.close()
    by_kind = Counter(f["kind"] for f in all_f)
    by_sev = Counter(f["severity"] for f in all_f)
    pages_hit = sorted({f["page"] for f in all_f})
    summary = {
        "job_id": ctx.job_id,
        "md_path": str(md_path),
        "pdf_path": str(ctx.pdf_path),
        "pages_audited": end - args.start + 1,
        "finding_count": len(all_f),
        "pages_with_findings": len(pages_hit),
        "by_kind": dict(by_kind),
        "by_severity": dict(by_sev),
        "critical_pages": sorted(
            {f["page"] for f in all_f if f["severity"] == "critical"}
        ),
        "major_pages": sorted({f["page"] for f in all_f if f["severity"] == "major"}),
        "findings_path": str(findings_path),
    }
    (out_dir / "structural_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
