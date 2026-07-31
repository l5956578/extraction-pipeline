#!/usr/bin/env python3
"""Appendix 5: stitch domain-example scales into full tables + section prose.

User decisions (2026-07-30):
- Dropped spanning cell "Situation (and roles)" is OK in MD; note once as prose (p.191).
- Keep four domain columns (Personal/Public/Occupational/Educational).
- Keep scale name as column header; *also* mark Online interaction / Mediating a text /
  Mediating concepts / Mediating communication shifts in inline prose (PDF under-delineates).
- Merge multipage level halves for each scale into one full table on the scale's start page.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
LOG = ROOT / "work/cefr-companion-2020/metadata/book_qa/APPENDIX5_STITCH.md"

LEVEL_ORDER = [
    "C2",
    "C1",
    "B2+",
    "B2",
    "B1+",
    "B1",
    "A2+",
    "A2",
    "A1",
    "Pre-A1",
]
LEVEL_RANK = {lv: i for i, lv in enumerate(LEVEL_ORDER)}

# Umbrella sections for prose guides (first scale page that belongs to each)
UMBRELLA: list[tuple[str, str, list[str]]] = [
    (
        "online_interaction",
        "Online interaction",
        [
            "Online conversation and discussion",
            "Goal-oriented online transactions and collaboration",
        ],
    ),
    (
        "mediating_a_text",
        "Mediating a text",
        [
            "Relaying specific information in speech or sign",
            "Relaying specific information in writing",
            "Explaining data (in graphs, diagrams, etc.) in speech or sign",
            "Explaining data (in graphs, diagrams, etc.) in writing",
            "Processing text in speech or sign",
            "Processing text in writing",
            "Translating a written text in speech or sign",
            "Translating a written text in writing",
            "Note-taking (lectures, seminars, meetings, etc.)",
            "Expressing a personal response to creative texts (including literature)",
            "Analysis and criticism of creative texts (including literature)",
        ],
    ),
    (
        "mediating_concepts",
        "Mediating concepts",
        [
            "Facilitating collaborative interaction with peers",
            "Collaborating to construct meaning",
            "Managing interaction",
            "Encouraging conceptual talk",
        ],
    ),
    (
        "mediating_communication",
        "Mediating communication",
        [
            "Facilitating pluricultural space",
            "Acting as intermediary in informal situations (with friends and colleagues)",
            "Facilitating communication in delicate situations and disagreements",
        ],
    ),
]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")[:80]


def extract_tables(body: str, page: int) -> list[dict]:
    out = []
    pat = re.compile(
        r"(?:### ([^\n]+)\n\n)?"
        r"(\| Level \| ([^|\n]+) \| Personal \| Public \| Occupational \| Educational \|\n"
        r"\|[-| :]+\|\n"
        r"((?:\|[^\n]+\|\n?)+))",
        re.M,
    )
    for m in pat.finditer(body):
        scale = m.group(3).strip()
        table = m.group(2).strip()
        rows = table.splitlines()[2:]  # data rows
        out.append(
            {
                "page": page,
                "scale": scale,
                "title_line": (m.group(1) or "").strip(),
                "header": table.splitlines()[0],
                "sep": table.splitlines()[1],
                "rows": rows,
                "raw": table,
            }
        )
    return out


def row_level(row: str) -> str:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells[0] if cells else ""


def merge_rows(row_lists: list[list[str]]) -> list[str]:
    """Concatenate page-order rows; drop exact duplicates; keep blank-level trails."""
    seen: set[str] = set()
    out: list[str] = []
    for rows in row_lists:
        for r in rows:
            key = re.sub(r"\s+", " ", r.strip())
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
    # Soft reorder: keep relative order but ensure levels don't go high after low wrongly
    # (domain tables are already high→low within each page; concat in page order is correct)
    return out


def build_table(scale: str, header: str, sep: str, rows: list[str]) -> str:
    # Normalize header scale name
    header = f"| Level | {scale} | Personal | Public | Occupational | Educational |"
    sep = "|-------|" + "-" * (len(scale) + 2) + "|----------|--------|--------------|-------------|"
    # simpler fixed sep
    sep = "|-------|" + "-" * max(20, len(scale) + 2) + "|----------|--------|--------------|-------------|"
    return "\n".join([header, sep] + rows)


def umbrella_for(scale: str) -> tuple[str, str] | None:
    for key, title, scales in UMBRELLA:
        for s in scales:
            if scale.startswith(s[:40]) or s.startswith(scale[:40]) or scale == s:
                return key, title
        # fuzzy
        for s in scales:
            if slug(scale) == slug(s) or slug(scale) in slug(s) or slug(s) in slug(scale):
                return key, title
    return None


def match_scale(scale: str, candidates: list[str]) -> str | None:
    """Exact or full-slug match only — never prefix-collide speech/sign vs writing."""
    sc = re.sub(r"\s+", " ", scale).strip()
    for s in candidates:
        if sc == s:
            return s
        if slug(sc) == slug(s):
            return s
    return None


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    report: list[str] = []

    # Collect all tables
    by_scale: OrderedDict[str, list[dict]] = OrderedDict()
    all_scales_order: list[str] = []
    for p in range(191, 242):
        for t in extract_tables(page_body(md, p), p):
            key = t["scale"]
            # normalize minor OCR variance
            key_n = re.sub(r"\s+", " ", key).strip()
            t["scale"] = key_n
            if key_n not in by_scale:
                by_scale[key_n] = []
                all_scales_order.append(key_n)
            by_scale[key_n].append(t)

    # Merge each scale
    merged: OrderedDict[str, dict] = OrderedDict()
    for scale, parts in by_scale.items():
        pages = [p["page"] for p in parts]
        rows = merge_rows([p["rows"] for p in parts])
        levels = [row_level(r) for r in rows if row_level(r) in LEVEL_RANK]
        start = min(pages)
        end = max(pages)
        table_md = build_table(scale, parts[0]["header"], parts[0]["sep"], rows)
        merged[scale] = {
            "scale": scale,
            "start": start,
            "end": end,
            "pages": pages,
            "levels": levels,
            "table": table_md,
            "id": f"table_app5_{slug(scale)}",
        }
        report.append(
            f"MERGE {scale!r} pages {start}-{end} ({len(parts)} slices) → {len(rows)} rows levels={levels}"
        )

    # Map start page → list of scales that start there (in order of first appearance)
    start_map: dict[int, list[str]] = {}
    for scale in all_scales_order:
        st = merged[scale]["start"]
        start_map.setdefault(st, []).append(scale)

    # Umbrella intro prose
    situations_note = (
        "Domain examples use four columns that all fall under **Situation (and roles)** "
        "(CEFR 2001 Section 4.1.1): **Personal**, **Public**, **Occupational**, and **Educational**. "
        "Markdown cannot represent the PDF’s spanning header over those four columns, so that label "
        "is stated here once for the whole appendix rather than as a merged table cell. "
        "The four column headers are repeated on each scale table below."
    )

    online_intro = (
        "## Online interaction\n\n"
        "Online interaction is the first umbrella group in this appendix. It covers more than one "
        "illustrative scale: as the tables change, the **type of online interaction** changes "
        "(conversation and discussion → goal-oriented transactions and collaboration). "
        "Each table’s second column still names the scale; the headings between tables mark the shift."
    )

    mediating_text_intro = (
        "## Mediating a text\n\n"
        "Mediating a text holds the same structural role for mediation that **Online interaction** "
        "held above: several related scales share the four domain columns (**Situation (and roles)**: "
        "Personal / Public / Occupational / Educational). As scales change, the **type of text** and "
        "mediation activity changes (relaying information, explaining data, processing text, translating, "
        "note-taking, responding to creative texts, analysis and criticism). Column headers name each scale; "
        "section prose marks those shifts so the reader can delineate tables more clearly than the PDF layout alone."
    )

    mediating_concepts_intro = (
        "## Mediating concepts\n\n"
        "Still under domain examples with **Situation (and roles)** columns. Mediating concepts groups scales "
        "for collaborative interaction, constructing meaning, managing interaction, and encouraging conceptual talk. "
        "As tables change, the **mediation activity type** changes; column headers name each scale."
    )

    mediating_comm_intro = (
        "## Mediating communication\n\n"
        "The last umbrella group: pluricultural space, informal intermediary roles, and delicate situations / "
        "disagreements. Domain columns remain **Situation (and roles)**. Scale titles in the table header mark "
        "each activity type."
    )

    scale_shift_blurb = {
        "Goal-oriented online transactions and collaboration": (
            "Still under **Online interaction**. Descriptors now concern **goal-oriented online transactions "
            "and collaboration** rather than open conversation and discussion. Domain columns remain "
            "Situation (and roles): Personal / Public / Occupational / Educational."
        ),
        "Relaying specific information in writing": (
            "Still under **Mediating a text**. Shift from relaying in speech/sign to **relaying specific "
            "information in writing**. Domain columns unchanged (Situation and roles)."
        ),
        "Explaining data (in graphs, diagrams, etc.) in writing": (
            "Still under **Mediating a text**. Shift to **explaining data in writing** (after speech/sign)."
        ),
        "Processing text in writing": (
            "Still under **Mediating a text**. Shift to **processing text in writing**."
        ),
        "Translating a written text in writing": (
            "Still under **Mediating a text**. Shift to **translating a written text in writing**."
        ),
        "Collaborating to construct meaning": (
            "Still under **Mediating concepts**. Shift from facilitating collaborative interaction to "
            "**collaborating to construct meaning**."
        ),
        "Managing interaction": (
            "Still under **Mediating concepts**. Shift to **managing interaction**."
        ),
        "Encouraging conceptual talk": (
            "Still under **Mediating concepts**. Shift to **encouraging conceptual talk**."
        ),
        "Acting as intermediary in informal situations (with friends and colleagues)": (
            "Still under **Mediating communication**. Shift from pluricultural space to **acting as an "
            "intermediary in informal situations**."
        ),
        "Facilitating communication in delicate situations and disagreements": (
            "Still under **Mediating communication**. Shift to **facilitating communication in delicate "
            "situations and disagreements**."
        ),
    }

    # First scales of each umbrella get the big intro
    first_of_umbrella = {
        "Online conversation and discussion": online_intro,
        "Relaying specific information in speech or sign": mediating_text_intro,
        "Facilitating collaborative interaction with peers": mediating_concepts_intro,
        "Facilitating pluricultural space": mediating_comm_intro,
    }

    # Build page content
    page_content: dict[int, list[str]] = {p: [] for p in range(191, 242)}

    # p191 intro (keep appendix chrome + existing intro prose, replace situations note)
    intro = """<!-- el:start type=prose id=prose_p191_appendix5_intro page=191 -->
Appendix 5

**EXAMPLES OF USE IN DIFFERENT DOMAINS FOR DESCRIPTORS OF ONLINE INTERACTION AND MEDIATION ACTIVITIES**

As an extra resource for users of the scales, the Authoring Group produced the following examples elaborating the descriptors for online interaction and mediation activities for the four domains set out in CEFR 2001 Section 4.1.1. These examples are intended to assist educators in selecting activities appropriate to their learners for each descriptor.

The examples were validated in a series of distance workshops carried out during Phase 3 of the validation, from November to December 2015.

""" + situations_note + """
<!-- el:end id=prose_p191_appendix5_intro -->
"""
    page_content[191].append(intro)

    placed_umbrellas: set[str] = set()
    for scale in all_scales_order:
        info = merged[scale]
        start = info["start"]
        aid = info["id"]
        blocks: list[str] = []

        # Umbrella intro once
        for key, title, scales in UMBRELLA:
            if scale in scales or match_scale(scale, scales):
                if key not in placed_umbrellas:
                    if scale in first_of_umbrella or match_scale(scale, list(first_of_umbrella.keys())):
                        # find matching first-of text
                        for fk, fv in first_of_umbrella.items():
                            if scale == fk or match_scale(scale, [fk]):
                                blocks.append(fv)
                                break
                        else:
                            blocks.append(f"## {title}\n")
                    else:
                        blocks.append(f"## {title}\n")
                    placed_umbrellas.add(key)
                break

        # Scale-shift blurb (exact scale name only)
        if scale in scale_shift_blurb:
            blocks.append(scale_shift_blurb[scale])

        # Artifact block
        blocks.append(
            f"<!-- el:start type=artifact id={aid} page={start} -->\n"
            f"<!-- db:id={aid} type=descriptor_scale product_tier=detailed,context pages={info['start']}-{info['end']} -->\n"
            f"### {scale} | {aid}\n\n"
            f"<!-- book-qa: Appendix 5 stitched full scale (was multipage domain slices); "
            f"Situation (and roles) = Personal/Public/Occupational/Educational columns -->\n\n"
            f"{info['table']}\n"
            f"<!-- el:end id={aid} -->"
        )
        page_content[start].extend(blocks)

        # Continuity on mid pages
        for p in range(start + 1, info["end"] + 1):
            # only if this page does not start another scale that we place fully
            if p in start_map and any(merged[s]["start"] == p for s in start_map[p]):
                # page hosts a full table of another scale; still note continuity if it was mid for this scale
                pass
            note = (
                f"<!-- table-continuity: Appendix 5 full domain-example table for "
                f"**{scale}** lives on page {start} ({aid}); page {p} PDF level-slice not duplicated -->"
            )
            # Avoid duplicate continuity if already have note for same scale
            if not any(aid in x and "table-continuity" in x for x in page_content[p]):
                page_content[p].append(note)

    # Chrome footers for pages
    chrome = {
        191: "*Examples of use in different domains for descriptors of online interaction and mediation activities ▶ Page **191***",
        241: "*Examples of use in different domains for descriptors of online interaction and mediation activities ▶ Page **241***",
    }

    for p in range(191, 242):
        parts = page_content[p]
        # If page only has continuity notes, keep them + page chrome
        body = "\n\n".join(parts)
        if p in chrome and chrome[p] not in body:
            body = body + "\n\n" + chrome[p]
        elif not body.strip():
            body = (
                f"<!-- table-continuity: Appendix 5 domain-example content for this PDF page is "
                f"merged into full scale tables on earlier pages in this appendix -->\n\n"
                f"*Page **{p}** ▶ **CEFR – Companion volume***"
            )
        elif "Page **" not in body and "▶ Page" not in body:
            # even pages style
            if p % 2 == 0:
                body += f"\n\n*Page **{p}** ▶ **CEFR – Companion volume***"
            else:
                body += (
                    f"\n\n*Examples of use in different domains for descriptors of online "
                    f"interaction and mediation activities ▶ Page **{p}***"
                )
        md = replace_page(md, p, body)

    md = re.sub(r"(-->)\n(\|)", r"\1\n\n\2", md)
    MD.write_text(md, encoding="utf-8")

    # Log
    lines = [
        "# Appendix 5 stitch report",
        "",
        "User decision: Situations (and roles) as prose once; keep domain columns; "
        "inline umbrella/scale-type guidance; full-scale tables for grep.",
        "",
        "## Merged scales",
        "",
    ]
    for scale, info in merged.items():
        lines.append(
            f"- **{scale}**: pages PDF {info['start']}–{info['end']} → full table on p.{info['start']}; "
            f"id=`{info['id']}`; levels={info['levels']}"
        )
    lines += [
        "",
        "## Umbrella prose",
        "- p.191: Situations (and roles) note + Online interaction intro",
        "- Before first Mediating a text scale: mediating-a-text intro",
        "- Before first Mediating concepts scale: concepts intro",
        "- Before first Mediating communication scale: communication intro",
        "- Scale-shift blurbs between related scales within an umbrella",
        "",
        "## Report",
        "",
        *report,
    ]
    LOG.write_text("\n".join(lines), encoding="utf-8")
    for line in report:
        print(line)
    print("wrote", LOG)


if __name__ == "__main__":
    main()
