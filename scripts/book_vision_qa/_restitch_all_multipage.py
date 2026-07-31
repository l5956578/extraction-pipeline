#!/usr/bin/env python3
"""Merge multipage descriptor scales into one full table on the start page.

Removes mid-page continuation slices (keeps unique prose / footnotes / chrome).
Does NOT auto-merge Appendix 5 domain-example series (listed for user review).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

# (start_page, end_page, title_substr) — complementary high+low halves
MERGE_SPANS: list[tuple[int, int, str]] = [
    (54, 55, "Reading correspondence"),
    (55, 56, "Reading for orientation"),
    (56, 57, "Reading for information and argument"),
    (62, 63, "Sustained monologue: describing experience"),
    (65, 66, "Addressing audiences"),
    (73, 74, "Conversation"),
    (82, 83, "Correspondence"),
    (86, 87, "Goal-oriented online transactions and collaboration"),
    (88, 89, "Co-operating"),
    (107, 108, "Analysis and criticism of creative texts"),
    (141, 142, "Propositional precision"),
]

# Start already has full level span; mid is pure duplicate lower band
STRIP_DUP_MIDS: list[tuple[int, int, str]] = [
    (85, 86, "Online conversation and discussion"),
    (91, 92, "Overall mediation"),
    (106, 107, "Expressing a personal response to creative texts"),
    (114, 115, "Facilitating pluricultural space"),
]

# Already stitched earlier (continuity notes); re-assert strip if table reappears
ALREADY_STRIPPED_MIDS = [
    25, 95, 100, 101, 104, 111, 120, 135, 147, 148, 151, 152, 155, 156,
    159, 160, 163, 165, 169, 178, 179, 180, 181, 184, 185, 188, 189,
]

APPX5_NEEDS_USER = [
    (191, 197, "online interaction domain examples"),
    (198, 224, "mediating a text domain examples"),
    (225, 234, "mediating concepts domain examples"),
    (235, 241, "mediating communication domain examples"),
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
    if idx < 0:
        raise RuntimeError(f"missing page marker {page}")
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def find_scale_table(body: str, title_substr: str) -> re.Match[str] | None:
    """Match a markdown table whose header cell contains title_substr."""
    pat = re.compile(
        r"(?:### [^\n]*"
        + re.escape(title_substr[:40])
        + r"[^\n]*\n\n)?"
        r"(\| \| [^\n]*"
        + re.escape(title_substr[:30])
        + r"[^\n]*\|\n\|[-:| ]+\|(?:\n\|[^\n]+\|)+)",
        re.I,
    )
    m = pat.search(body)
    if m:
        return m
    # looser: any table header containing key words
    words = [w for w in re.split(r"\W+", title_substr.lower()) if len(w) > 3][:4]
    for m in re.finditer(
        r"(\| \| [^\n]+\|\n\|[-:| ]+\|(?:\n\|[^\n]+\|)+)", body
    ):
        head = m.group(1).splitlines()[0].lower()
        if all(w in head for w in words[:2]):
            return m
    return None


def table_data_rows(table: str) -> list[str]:
    lines = table.strip().splitlines()
    return lines[2:]  # skip header + sep


def merge_tables(upper: str, lower: str) -> str:
    u_lines = upper.strip().splitlines()
    header, sep = u_lines[0], u_lines[1]
    rows = table_data_rows(upper) + table_data_rows(lower)
    # drop exact duplicate rows
    seen: set[str] = set()
    out_rows: list[str] = []
    for r in rows:
        key = re.sub(r"\s+", " ", r.strip())
        if key in seen:
            continue
        seen.add(key)
        out_rows.append(r)
    return "\n".join([header, sep] + out_rows)


def ensure_blank_before_tables(md: str) -> str:
    return re.sub(r"(-->)\n(\|)", r"\1\n\n\2", md)


def strip_matched_table(body: str, m: re.Match[str], start_page: int, label: str) -> str:
    """Remove the matched table (and optional ### title line immediately above)."""
    start, end = m.start(1) if m.lastindex else m.start(), m.end(1) if m.lastindex else m.end()
    # expand to optional ### title before table
    pre = body[:start]
    title_m = re.search(r"(?:\n|^)(### [^\n]+\n\n)$", pre)
    if title_m:
        start = title_m.start(1) if title_m.start(1) > 0 else title_m.start(1)
        # correct: remove from title start
        start = len(pre) - len(title_m.group(1))
    note = (
        f"\n<!-- table-continuity: full multipage table lives on page {start_page} "
        f"({label}); mid-page slice removed to keep single db:id for grep -->\n"
    )
    new_body = body[:start] + note + body[end:]
    # remove empty el wrappers left behind
    new_body = re.sub(
        r"\n*<!-- el:start type=artifact[^>]*-->\s*<!-- db:id=[^>]+-->\s*<!-- el:end[^>]*-->\n*",
        "\n",
        new_body,
    )
    new_body = re.sub(
        r"\n*<!-- el:start type=prose[^>]*table_restore[^>]*-->\s*"
        r"(?:<!--[^>]*-->\s*)*"
        r"(?:<!-- table-continuity:[^>]*-->\s*)*"
        r"<!-- el:end[^>]*-->\n*",
        "\n<!-- table-continuity retained -->\n",
        new_body,
        flags=re.I,
    )
    new_body = re.sub(r"\n{3,}", "\n\n", new_body)
    return new_body


def update_db_pages(body: str, title_substr: str, start: int, end: int) -> str:
    """Set pages=start-end on nearby db:id for this scale."""

    def repl_db(m: re.Match[str]) -> str:
        block = m.group(0)
        if re.search(re.escape(title_substr[:25]), block, re.I) or True:
            block = re.sub(r"pages=\d+(?:-\d+)?", f"pages={start}-{end}", block)
        return block

    # update db:id lines within ~500 chars before the scale title/table
    return re.sub(
        rf"(<!-- db:id=[^>]*{re.escape(title_substr[:20].lower().replace(' ', '_'))}[^>]*-->)",
        lambda m: re.sub(r"pages=\d+(?:-\d+)?", f"pages={start}-{end}", m.group(1), flags=re.I),
        body,
        flags=re.I,
    )


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    report: list[str] = []

    # 1) Merge complementary halves
    for start, end, label in MERGE_SPANS:
        b0 = page_body(md, start)
        b1 = page_body(md, end)
        m0 = find_scale_table(b0, label)
        m1 = find_scale_table(b1, label)
        if not m0 or not m1:
            report.append(f"MERGE FAIL {start}-{end} ({label}): found start={bool(m0)} end={bool(m1)}")
            continue
        t0 = m0.group(1) if m0.lastindex else m0.group(0)
        t1 = m1.group(1) if m1.lastindex else m1.group(0)
        merged = merge_tables(t0, t1)
        # replace on start
        s0, e0 = (m0.start(1), m0.end(1)) if m0.lastindex else (m0.start(), m0.end())
        new_b0 = b0[:s0] + merged + b0[e0:]
        # ensure db:id pages span if present near table
        new_b0 = re.sub(
            r"(<!-- db:id=[^>]*pages=)\d+(?:-\d+)?",
            rf"\g<1>{start}-{end}",
            new_b0,
            count=3,
        )
        # if end page has the only db:id, transplant a note on start
        if "db:id=" not in b0 and "db:id=" in b1:
            db = re.search(r"<!-- db:id=[^>]+-->", b1)
            title_line = re.search(
                rf"### [^\n]*{re.escape(label[:30])}[^\n]*", b1, re.I
            )
            inject = ""
            if db:
                dbt = re.sub(r"pages=\d+(?:-\d+)?", f"pages={start}-{end}", db.group(0))
                inject += dbt + "\n"
            if title_line and f"### " not in new_b0[max(0, s0 - 80) : s0 + 20]:
                inject += title_line.group(0) + "\n\n"
            if inject:
                new_b0 = new_b0[:s0] + inject + new_b0[s0:]
                # re-find not needed; write as-is
        md = replace_page(md, start, new_b0)

        # strip mid table; keep prose
        b1 = page_body(md, end)  # re-read after start write (unchanged end)
        m1 = find_scale_table(b1, label)
        if m1:
            new_b1 = strip_matched_table(b1, m1, start, label)
            # if end page only had this table + chrome, keep prose after
            md = replace_page(md, end, new_b1)
            report.append(f"MERGED {start}-{end} ({label}); mid table stripped from p{end}")
        else:
            report.append(f"MERGED {start}-{end} ({label}); mid already gone")

    # 2) Strip pure duplicate mid slices
    for start, mid, label in STRIP_DUP_MIDS:
        b = page_body(md, mid)
        m = find_scale_table(b, label)
        if m:
            new_b = strip_matched_table(b, m, start, label)
            md = replace_page(md, mid, new_b)
            report.append(f"STRIPPED dup mid p{mid} ({label}) → full on p{start}")
        else:
            report.append(f"OK no mid table p{mid} ({label})")

    # 3) Re-strip already-handled mids if a pipe table reappeared without db:id
    for p in ALREADY_STRIPPED_MIDS:
        b = page_body(md, p)
        if re.search(r"^\|.+\|\n\|[-:| ]+\|", b, re.M) and "db:id=" not in b:
            # only strip if continuity note or short table-looking page
            if "table-continuity" in b or len(re.findall(r"^\|", b, re.M)) < 20:
                new_b = re.sub(
                    r"\n*\|[^\n]*\|\n\|[-:| ]+\|(?:\n\|[^\n]*\|)+\n*",
                    "\n\n",
                    b,
                )
                new_b = re.sub(r"\n{3,}", "\n\n", new_b)
                md = replace_page(md, p, new_b)
                report.append(f"RE-STRIPPED residual table on continuity page p{p}")

    md = ensure_blank_before_tables(md)
    MD.write_text(md, encoding="utf-8")

    for line in report:
        print(line)
    print("---")
    print("APPX5_NEEDS_USER (not auto-merged; domain rows differ per page):")
    for a, b, lab in APPX5_NEEDS_USER:
        print(f"  pages {a}-{b}: {lab}")
    print("EXCEPTION: p.16 country tables left as user-provided multipage (explicit).")
    print("NOTE: turntaking p88 vs p139 are separate full tables (not a span).")


if __name__ == "__main__":
    main()
