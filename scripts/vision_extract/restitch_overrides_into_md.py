#!/usr/bin/env python3
"""Replace product MD page bodies from page_overrides for given PDF leaves.

Uses document page markers (after fix_page_numbers): doc = pdf - 6 for 1990 books.
Strips NATIVE-GOLD / cat comment noise from override before insert.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def clean_override(text: str) -> str:
    # drop machine catalogs but keep content
    text = re.sub(r"<!-- cat:.*?-->\n?", "", text)
    text = re.sub(
        r"\n*<!-- NATIVE-GOLD-EXAMPLES[^>]*-->.*?(?=\n<!--|\Z)",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(r"<!-- native-intonation leaf \d+ -->\n?", "", text)
    return text.strip() + "\n"


def restitch(job: str, out_name: str, leaves: list[int] | None = None) -> None:
    ov_dir = ROOT / "work" / job / "page_overrides"
    md_path = ROOT / "output" / job / out_name
    md = md_path.read_text(encoding="utf-8")
    # find all overrides
    if leaves is None:
        leaves = sorted(
            int(p.stem.split("_")[1]) for p in ov_dir.glob("page_*.md")
        )
    n = 0
    for leaf in leaves:
        path = ov_dir / f"page_{leaf:03d}.md"
        if not path.exists():
            continue
        body = clean_override(path.read_text(encoding="utf-8", errors="replace"))
        doc_page = leaf - 6  # Threshold/Waystage
        if doc_page < 1:
            continue
        # Match from previous page end or section to *Page **doc** / <!-- page:doc -->
        # Pattern: content then *Page **N*** \n\n <!-- page:N -->
        # Replace content immediately before the page footer for this doc page
        # Strategy: split on page markers
        pass  # handled below with split

    # Split approach: reassemble using all overrides where present
    parts = re.split(r"(\n\*Page \*\*\d+\*\*\n\n<!-- page:\d+ -->\n)", md)
    # parts[0] is front matter through first page body... actually first chunk is pre-first-footer
    # structure: body0, footer0, body1, footer1, ...
    # Better: use page:N markers
    chunks = re.split(r"(<!-- page:(\d+) -->)", md)
    # chunks: [pre, <!-- page:N -->, N, post_or_body, ...] wait
    # re.split with two groups: [text, fullmatch, group1, text, fullmatch, group1, ...]
    # Actually: (<!-- page:(\d+) -->) gives [before, full, num, after, full, num, ...]
    out = []
    i = 0
    # first segment before any page marker is front + page1 body... markers are AFTER content
    # So: parts of md are: [body_for_page_k, marker_k, body_for_page_k+1, ...]
    # The first chunk is everything before first page marker = frontmatter + first pages bodies

    # Simpler approach: for each doc page, find body between previous marker and this footer
    footers = list(re.finditer(r"\*Page \*\*(\d+)\*\*\n\n<!-- page:\1 -->", md))
    if not footers:
        # try without double newline
        footers = list(re.finditer(r"\*Page \*\*(\d+)\*\*.*?\n<!-- page:\1 -->", md))

    new_md = md
    for leaf in leaves:
        path = ov_dir / f"page_{leaf:03d}.md"
        if not path.exists():
            continue
        body = clean_override(path.read_text(encoding="utf-8", errors="replace"))
        doc_page = leaf - 6
        if doc_page < 1:
            continue
        # Footer is italic+bold: *Page **N***  (three stars after N)
        m = None
        for match in re.finditer(
            rf"\*Page \*\*{doc_page}\*\*\*\r?\n\r?\n<!-- page:{doc_page} -->",
            new_md,
        ):
            m = match
            break
        if not m:
            for match in re.finditer(
                rf"\*Page \*\*{doc_page}\*\*\*\r?\n<!-- page:{doc_page} -->",
                new_md,
            ):
                m = match
                break
        if not m:
            continue
        # body starts after previous page marker (or start)
        prev = list(
            re.finditer(r"<!-- page:(\d+) -->", new_md[: m.start()])
        )
        start = prev[-1].end() if prev else 0
        # if start is 0, keep front matter: find first real content after header block
        # For leaf corresponding early pages, careful
        segment = new_md[start : m.start()]
        # Keep leading newlines after previous marker
        lead = ""
        rest = segment
        if start > 0:
            # after <!-- page:X --> we usually have \n\n then body
            mm = re.match(r"(\n*)", segment)
            lead = mm.group(1) if mm else ""
            rest = segment[len(lead) :]
        # Don't replace if body is huge front matter for page 1 weirdness
        if doc_page == 1 and len(rest) > 50000:
            continue
        new_segment = lead + "\n" + body.strip() + "\n\n"
        new_md = new_md[:start] + new_segment + new_md[m.start() :]
        n += 1
        print(f"  restitched leaf {leaf} -> doc p.{doc_page} ({len(body)} chars)")

    # Whole-page restitch thins mark density without audit — re-apply gold locks
    # when writing Threshold product so 1.1.3/1.3.1 cannot collapse.
    fails: list[str] = []
    if "threshold" in str(md_path).lower():
        try:
            from gold_intonation_locks import apply_section_locks, residual_assertions

            new_md, ops = apply_section_locks(new_md)
            print(f"gold locks after restitch: {ops or ['noop']}")
            fails = residual_assertions(new_md)
            if fails:
                print("RESIDUAL FAIL after restitch (writing for inspection):")
                for f in fails:
                    print(f"  - {f}")
        except ImportError:
            print("WARNING: gold_intonation_locks unavailable after restitch")

    md_path.write_text(new_md, encoding="utf-8")
    print(f"wrote {md_path} pages={n}")
    if fails:
        raise SystemExit(1)


def main() -> None:
    print(
        "WARNING: whole-page restitch is high-risk for intonation density. "
        "Prefer merge_override_tones_into_md.py + full_md_vs_pdf_intonation.py."
    )
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="cefr-threshold-1990")
    ap.add_argument("--out", default="Threshold_1990.md")
    ap.add_argument("--leaves", default="", help="comma ranges e.g. 34-64,66-90")
    args = ap.parse_args()
    leaves = None
    if args.leaves:
        leaves = []
        for part in args.leaves.split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-", 1)
                leaves.extend(range(int(a), int(b) + 1))
            else:
                leaves.append(int(part))
    restitch(args.job, args.out, leaves)


if __name__ == "__main__":
    main()
