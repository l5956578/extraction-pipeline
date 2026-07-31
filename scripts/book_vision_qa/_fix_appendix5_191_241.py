#!/usr/bin/env python3
"""Book Vision QA MD repair for Appendix 5 (pages 191-241).

- Trim p191 mega multipage dual-emit dump to intro + rotated_from_grok p191 table
- Strip OCR soup dual-emit on pages 195/206/217/233; keep rotated_from_grok tables
- Never rewrite rotated_from_grok/*.md
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
RF = ROOT / "work/cefr-companion-2020/metadata/rotated_from_grok"


def page_span(md: str, n: int) -> tuple[int, int, str]:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return start, m.start(), md[start : m.start()]
    raise KeyError(n)


def extract_caption(body: str) -> str:
    lines = body.rstrip().splitlines()
    cap_lines: list[str] = []
    for ln in reversed(lines):
        s = ln.strip()
        if not s:
            if cap_lines:
                break
            continue
        if re.search(r"Page \*\*\d+\*\*", s) or (s.startswith("*") and "Page" in s):
            cap_lines.append(ln)
            continue
        break
    cap_lines.reverse()
    return "\n".join(cap_lines).strip()


def scale_id_for_page(body: str, p: int) -> str:
    m = re.search(r"el:start type=artifact id=([^\s>]+)", body)
    if m:
        return m.group(1)
    if p <= 197:
        return "scale_online_interaction"
    if p <= 224:
        return "scale_mediating_a_text"
    if p <= 234:
        return "scale_mediating_concepts"
    return "scale_mediating_communication"


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    fixes: list[str] = []

    # --- Fix page 191 ---
    start, end, _body = page_span(md, 191)
    rf191 = (RF / "page_191_appendix_5_domain_examples.md").read_text(encoding="utf-8").strip()
    new191 = f"""

<!-- el:start type=prose id=prose_p191_appendix5_intro page=191 -->
Appendix 5

**EXAMPLES OF USE IN DIFFERENT DOMAINS FOR DESCRIPTORS OF ONLINE INTERACTION AND MEDIATION ACTIVITIES**

As an extra resource for users of the scales, the Authoring Group produced the following examples elaborating the descriptors for online interaction and mediation activities for the four domains set out in CEFR 2001 Section 4.1.1. These examples are intended to assist educators in selecting activities appropriate to their learners for each descriptor.

The examples were validated in a series of distance workshops carried out during Phase 3 of the validation, from November to December 2015.
<!-- el:end id=prose_p191_appendix5_intro -->

<!-- el:start type=artifact id=scale_online_interaction page=191 -->
<!-- db:id=scale_online_interaction type=descriptor_scale product_tier=detailed,context pages=191-241 -->
### Online conversation and discussion | scale_online_interaction

<!-- book-qa: per-page table from rotated_from_grok (full multipage dump removed to end dual-emit with p192-241) -->
{rf191}
<!-- el:end id=scale_online_interaction -->

*Examples of use in different domains for descriptors of online interaction and mediation activities ▶ Page **191***

"""
    md = md[:start] + new191 + md[end:]
    fixes.append("p191: trimmed mega multipage dump to intro + rotated p191 table")

    # --- Fix dual-soup pages ---
    for p in (195, 206, 217, 233):
        start, end, body = page_span(md, p)
        cap = extract_caption(body)
        sid = scale_id_for_page(body, p)
        rf_files = list(RF.glob(f"page_{p:03d}_*.md"))
        if not rf_files:
            print(f"NO rotated_from_grok for p{p}")
            continue
        table = rf_files[0].read_text(encoding="utf-8").strip()
        m = re.search(r"\| Level \| ([^|]+) \|", table)
        title = m.group(1).strip() if m else sid
        # multi-table pages (e.g. 233): first title only for heading
        first_title = title.split("\n")[0].strip()
        new_body = f"""

<!-- el:start type=artifact id={sid} page={p} -->
<!-- book-qa: OCR soup dual-emit stripped; table restored from rotated_from_grok/{rf_files[0].name} -->
### {first_title} | {sid}

{table}
<!-- el:end id={sid} -->

{cap if cap else f"Page **{p}**"}

"""
        md = md[:start] + new_body + md[end:]
        fixes.append(f"p{p}: stripped OCR soup dual-emit; kept rotated_from_grok table")

    MD.write_text(md, encoding="utf-8")
    print("Wrote", MD)
    for f in fixes:
        print(" -", f)

    md2 = MD.read_text(encoding="utf-8")
    for p in (191, 195, 206, 217, 233, 192, 241):
        _s, _e, b = page_span(md2, p)
        soup = "as the lead researcher" in b or "**C2 C1**" in b
        mega = len(b) > 50000
        has_table = "| Level |" in b
        print(
            f"p{p}: chars={len(b)} soup={soup} mega={mega} has_table={has_table}"
        )


if __name__ == "__main__":
    main()
