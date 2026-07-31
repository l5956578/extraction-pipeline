#!/usr/bin/env python3
"""Restore missing second tables on multi-table Appendix 5 pages into main MD.

rotated_from_grok pages 195/206/217 only captured the first table; PDF has two.
Do NOT edit rotated_from_grok — restore into deliverable MD only.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

T195_GOAL = """
| Level | Goal-oriented online transactions and collaboration | Personal | Public | Occupational | Educational |
|-------|------------------------------------------------------|----------|--------|--------------|-------------|
| C2 | Can resolve misunderstandings and deal effectively with frictions that arise during the collaborative process.<br>Can provide guidance and add precision to the work of a group at the redrafting and editing stages of collaborative work. | [not applicable] | as the convenor for a social intervention project organised online (e.g. by a non-governmental organisation) | as the facilitator in an online collaborative project | as the lead researcher in a collaborative research programme requiring online qualitative data collection and evaluation |
| C1 | Can co-ordinate a group that is working on a project online, formulating and revising detailed instructions, evaluating proposals from team members, and providing clarifications in order to accomplish the shared tasks. |  |  | as a project manager using online tools to co-ordinate the introduction of new systems across multiple remote sites |  |
|  | Can deal with complex online transactions in a service role (e.g. applications with complicated requirements), adjusting language flexibly to manage discussions and negotiations. |  | as voluntary moderator of an online citizens' advice service and/or Q&A forum | as personal assistant, travel agent or enrolment secretary for an educational institution | [not applicable] |
|  | Can participate in complex projects requiring collaborative writing and redrafting as well as other forms of online collaboration, following and relaying instructions with precision in order to reach the goal.<br>Can deal effectively with communication problems and cultural issues that arise in an online collaborative or transactional exchange by reformulating, clarifying and providing examples through media (visual, audio, graphic). |  | as the convenor for a social intervention project organised online (e.g. by a non-governmental organisation) | as a participant in a project using online tools to co-ordinate the introduction of new procedures across multiple locations | as a participant in a collaborative research programme requiring online data collection and evaluation |
""".strip()

T206_WRITING = """
| Level | Explaining data (in graphs, diagrams, etc.) in writing | Personal | Public | Occupational | Educational |
|-------|--------------------------------------------------------|----------|--------|--------------|-------------|
| C2 | Can interpret and present in writing (in Language B) various forms of empirical data (with text in Language A) from conceptually complex research on academic or professional topics. | [not applicable] | [not applicable] | data from a company financial report, market research or other corporate report or from research and development activities for senior management | as part of a PhD thesis or master's dissertation that includes empirical data |
""".strip()

T217_WRITING = """
| Level | Translating a written text in writing | Personal | Public | Occupational | Educational |
|-------|--------------------------------------|----------|--------|--------------|-------------|
| C2 | Can translate (into Language B) technical material outside their field of specialisation (written in Language A), provided subject matter accuracy is checked by a specialist in the field concerned. | letters, newspaper articles, commentaries and editorials, specialised articles, or other publications addressed to a general educated readership | a political tract, a public policy document, a legal opinion | professional publications, technical reports, contracts, press releases | academic papers |
""".strip()

PATCHES = {
    195: ("Goal-oriented online transactions and collaboration", T195_GOAL),
    206: ("Explaining data (in graphs, diagrams, etc.) in writing", T206_WRITING),
    217: ("Translating a written text in writing", T217_WRITING),
}


def page_span(md: str, n: int) -> tuple[int, int, str]:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return start, m.start(), md[start : m.start()]
    raise KeyError(n)


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    for p, (needle, table) in PATCHES.items():
        start, end, body = page_span(md, p)
        if needle in body and "| C2 |" in body[body.find(needle) : body.find(needle) + 500]:
            # crude already-present check
            if body.count("| Level |") >= 2:
                print(f"p{p}: already has 2+ tables, skip")
                continue
        m = re.search(r"(<!-- el:end id=[^>]+-->)", body)
        if not m:
            print(f"p{p}: no el:end, abort")
            continue
        insert_at = m.start()
        addition = (
            "\n\n<!-- book-qa: second table restored from PDF vision "
            "(missing from rotated_from_grok) -->\n"
            f"{table}\n"
        )
        new_body = body[:insert_at] + addition + body[insert_at:]
        md = md[:start] + new_body + md[end:]
        print(f"p{p}: inserted second table ({needle})")

    MD.write_text(md, encoding="utf-8")
    md2 = MD.read_text(encoding="utf-8")
    for p in (195, 206, 217):
        _s, _e, b = page_span(md2, p)
        n_level = b.count("| Level |")
        print(f"p{p}: Level headers={n_level} chars={len(b)}")


if __name__ == "__main__":
    main()
