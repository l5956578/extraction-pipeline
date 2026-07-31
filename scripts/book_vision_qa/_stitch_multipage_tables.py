#!/usr/bin/env python3
"""Re-stitch multipage descriptor tables: one db:id body on start page; remove mid-page dups.

Keeps unique prose, footnotes, and page chrome on mid/end pages.
Does NOT rewrite appendix 5 domain-example series (flagged separately).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"

# (start, end, optional human label) — clear single-scale multipage spans
# Mid pages should not keep table slices once start has full levels.
STITCH_SPANS: list[tuple[int, int, str]] = [
    (24, 25, "table_02 / summary descriptor changes"),
    (50, 51, "live audience"),
    (85, 86, "online conversation"),
    (91, 92, "overall mediation"),
    (94, 95, "relaying specific information"),
    (99, 101, "processing text"),
    (103, 104, "translating written text"),
    (106, 107, "personal response creative texts"),
    (110, 111, "collaborating in a group"),
    (114, 115, "facilitating pluricultural space"),
    (119, 120, "strategies explain new concept"),
    (126, 127, "plurilingual comprehension"),
    (130, 131, "general linguistic range"),
    # 132-133 grammar+vocab already split; vocab control may still slice
    (134, 135, "phonological control"),
    (146, 148, "sign language repertoire"),
    (150, 152, "diagrammatical accuracy"),
    (154, 156, "sociolinguistic appropriateness"),
    (158, 160, "sign text structure"),
    (162, 163, "setting and perspectives"),
    (164, 165, "language awareness"),
    (166, 167, "presence and effect"),
    (168, 169, "signing fluency"),
    (177, 181, "self-assessment grid"),
    (183, 185, "phonology qualitative"),
    (187, 189, "argument written assessment"),
]

# Appendix 5 domain example multipage scales — DO NOT auto-drop mid pages
# (different domain rows per page; user can decide). Listed for log only.
APPX5_NEEDS_REVIEW = [
    (191, 197, "online interaction domain examples"),
    (198, 224, "mediating a text domain examples"),
    (225, 234, "mediating concepts domain examples"),
    (235, 241, "mediating communication domain examples"),
]


def page_regions(md: str) -> list[tuple[int, int, int]]:
    """List of (page_num, body_start, body_end) where body is before <!-- page:N -->."""
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    out = []
    for i, m in enumerate(markers):
        page = int(m.group(1))
        start = markers[i - 1].end() if i else 0
        out.append((page, start, m.start()))
    return out


def replace_page(md: str, page: int, new_body: str) -> str:
    marker = f"<!-- page:{page} -->"
    idx = md.find(marker)
    prev = list(re.finditer(r"<!-- page:\d+ -->", md[:idx]))
    start = prev[-1].end() if prev else 0
    return md[:start] + "\n" + new_body.strip() + "\n\n" + md[idx:]


def page_body(md: str, n: int) -> str:
    markers = list(re.finditer(r"<!-- page:(\d+) -->", md))
    for i, m in enumerate(markers):
        if int(m.group(1)) == n:
            start = markers[i - 1].end() if i else 0
            return md[start : m.start()]
    return ""


def strip_markdown_tables(body: str) -> str:
    """Remove pipe tables (including optional title lines immediately above)."""
    # Remove book-qa restore comments that only introduce tables
    body = re.sub(
        r"\n*<!-- book-qa[^>]*?(?:page-slice|continuation|multipage|table restore|restored from rotated)[^>]*-->\n*",
        "\n",
        body,
        flags=re.I,
    )
    # Remove ### Title | id lines only when followed by a table
    body = re.sub(
        r"\n### [^\n]+\n\n(?=\|)",
        "\n",
        body,
    )
    # Remove contiguous markdown table blocks
    body = re.sub(
        r"\n*\|[^\n]*\|\n\|[-:| ]+\|(?:\n\|[^\n]*\|)+\n*",
        "\n\n",
        body,
    )
    # Remove orphan el:start/end artifact blocks that became empty
    body = re.sub(
        r"\n*<!-- el:start type=artifact[^>]*-->\s*<!-- db:id=[^>]+-->\s*<!-- el:end[^>]*-->\n*",
        "\n",
        body,
    )
    body = re.sub(
        r"\n*<!-- el:start type=artifact[^>]*-->\s*<!-- el:end[^>]*-->\n*",
        "\n",
        body,
    )
    # Collapse excess blank lines
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


def ensure_blank_before_tables(md: str) -> str:
    return re.sub(r"(-->)\n(\|)", r"\1\n\n\2", md)


def has_fullish_levels(body: str) -> bool:
    levels = set(re.findall(r"\| (C2|C1|B2\+?|B1\+?|A2\+?|A1|Pre-A1) \|", body))
    # full if has high and low
    return ("C2" in levels or "C1" in levels) and (
        "A1" in levels or "Pre-A1" in levels or "A2" in levels
    )


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    report: list[str] = []
    for start, end, label in STITCH_SPANS:
        b0 = page_body(md, start)
        if not has_fullish_levels(b0) and start != 177:
            # self-assessment is multi-section; still strip mid pages if start has substantial table
            if start != 177:
                report.append(
                    f"SKIP stitch {start}-{end} ({label}): start page lacks full level span"
                )
                # still strip obvious mid slices that are book-qa page-slices
        for p in range(start + 1, end + 1):
            b = page_body(md, p)
            if not b.strip():
                continue
            # Only strip if page looks like a table continuation / slice
            is_slice = bool(
                re.search(
                    r"page-slice|multipage continuation|table restore|restored from rotated_from_grok",
                    b,
                    re.I,
                )
            )
            has_table = bool(re.search(r"^\|.+\|\n\|[-:| ]+\|", b, re.M))
            # For mid pages with tables but little unique prose, strip tables
            prose = re.sub(r"\|[^\n]*\|\n?", "", b)
            prose = re.sub(r"<!--.*?-->", "", prose, flags=re.S)
            prose = re.sub(r"\*[^\n]*Page[^\n]*\*", "", prose)
            prose = re.sub(r"#{1,6} .+\n", "", prose)
            prose_len = len(re.sub(r"\s+", " ", prose).strip())
            if has_table and (is_slice or prose_len < 200 or start == 177):
                new_b = strip_markdown_tables(b)
                # Ensure a note for grep continuity
                if "table continuity" not in new_b:
                    note = (
                        f"\n<!-- table-continuity: full multipage table lives on page {start} "
                        f"({label}); mid-page slice removed to keep single db:id for grep -->\n"
                    )
                    # insert after first el:start if present
                    if "<!-- el:start" in new_b:
                        new_b = re.sub(
                            r"(<!-- el:start[^>]*-->)",
                            r"\1" + note,
                            new_b,
                            count=1,
                        )
                    else:
                        new_b = note + new_b
                md = replace_page(md, p, new_b)
                report.append(
                    f"STRIPPED table slice p{p} (span {start}-{end}: {label}); prose_len={prose_len}"
                )
            else:
                report.append(
                    f"KEEP p{p} (span {start}-{end}: {label}); table={has_table} prose_len={prose_len} slice={is_slice}"
                )

    md = ensure_blank_before_tables(md)
    MD.write_text(md, encoding="utf-8")
    for line in report:
        print(line)
    print("---")
    print("APPX5_NEEDS_REVIEW (not auto-stitched):")
    for a, b, lab in APPX5_NEEDS_REVIEW:
        print(f"  pages {a}-{b}: {lab}")


if __name__ == "__main__":
    main()
