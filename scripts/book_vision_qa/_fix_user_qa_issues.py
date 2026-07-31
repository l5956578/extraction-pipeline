#!/usr/bin/env python3
"""Resolve user-found Obsidian table + figure leaf-soup issues.

1. Insert blank line between HTML comment and markdown table (Obsidian).
2. Strip dual-emit leaf soup before Figure 16 (and similar figure dumps).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "output/cefr-companion-2020/CEFR_Companion_Volume.md"
BOOK_QA = ROOT / "work/cefr-companion-2020/metadata/book_qa"


def fix_comment_table_gap(md: str) -> tuple[str, int]:
    """Ensure HTML comments are not immediately followed by a table row."""
    md2, n = re.subn(r"(-->)\n(\|)", r"\1\n\n\2", md)
    return md2, n


def strip_fig16_leaf_soup(md: str) -> tuple[str, int]:
    """Remove dual-emit tree dump before Figure 16 fence."""
    # From dual bold title through bare leaf list, keep real figure block
    pat = re.compile(
        r"\n\*\*Sociolinguistic Linguistic competence competence\*\*\n"
        r"[\s\S]*?"
        r"(?=<!-- db:id=figure_16_communicative_language_competences)",
        re.M,
    )
    md2, n = pat.subn("\n\n", md, count=1)
    return md2, n


def strip_similar_pre_figure_soup(md: str) -> tuple[str, list[str]]:
    """Remove dual-emit **A B competence competence** + bare leaf lists before figure db:id.

    Pattern learned from user find on p.129: dual-word bold title then short leaf lines
    that restate the following ```text tree, sitting outside the fence.
    """
    removed: list[str] = []
    # Dual-title bold: two words then repeated 'competence' (or similar)
    dual = re.compile(
        r"\n\*\*"
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)"  # e.g. Sociolinguistic
        r"\s+"
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)"  # e.g. Linguistic
        r"\s+competence\s+competence\*\*\n"
        r"(?:"
        r"(?:[A-Za-z][A-Za-z /()\-]{2,80}\n)+"  # bare leaf lines
        r")?"
        r"(?=\n*<!-- db:id=figure_)",
        re.M,
    )
    md2, n1 = dual.subn("\n\n", md)
    if n1:
        removed.append(f"dual_competence_title x{n1}")

    # Broader: before figure db:id, a block of short non-markdown lines that look like
    # tree leaves (no pipes, no #, no <!--) and include known leaf soup markers.
    # Only if immediately before figure db:id and after blank line, and contains
    # both a dual-ish title and several short leaf lines.
    # Conservative: only blocks that include 'competence competence' already handled.

    # Also strip known leaf-list dumps: consecutive short lines matching figure leaves
    # between prose end and ```text when they reappear outside fence.
    # Handled per-figure for known cases.
    return md2, removed


def scan_pre_fence_leaf_soup(md: str) -> list[tuple[int, str]]:
    """Report remaining pre-fence dual dumps (for storage / verification)."""
    findings: list[tuple[int, str]] = []
    for m in re.finditer(
        r"\n(\*\*[^\n]+competence[^\n]*\*\*\n(?:[A-Za-z][^\n]{0,80}\n){3,20})"
        r"(?=```text|<!-- db:id=figure_)",
        md,
    ):
        pos = m.start()
        page = None
        for mm in re.finditer(r"<!-- page:(\d+) -->", md):
            if mm.start() > pos:
                page = int(mm.group(1))
                break
        snippet = m.group(1)[:120].replace("\n", " | ")
        findings.append((page or -1, snippet))
    return findings


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    md, n_gap = fix_comment_table_gap(md)
    print("comment_table_blank_lines", n_gap)
    md, n_fig16 = strip_fig16_leaf_soup(md)
    print("fig16_soup_removed", n_fig16)
    md, extra = strip_similar_pre_figure_soup(md)
    print("similar_soup", extra)
    findings = scan_pre_fence_leaf_soup(md)
    print("remaining_pre_fence_soup", findings)

    # Also remove dual-emit if pattern is bare leaves without dual title but
    # contains 'General linguistic range' then 'Vocabulary range' etc. before fig16
    # already removed with fig16 strip.

    # Pattern: **X competence** then leaf list of known CEFR competence leaves
    # without dual title (normal **Pragmatic competence** alone is OK if inside
    # a proper structure - only remove if it's a bare list before figure db:id
    # that was part of the dual dump - already handled).

    MD.write_text(md, encoding="utf-8")

    # Verify
    md2 = MD.read_text(encoding="utf-8")
    print(
        "comment-then-table left",
        len(re.findall(r"-->\n\|", md2)),
    )
    print(
        "Sociolinguistic Linguistic trash left",
        "Sociolinguistic Linguistic competence competence" in md2,
    )
    print("figure_16 present", "figure_16_communicative" in md2)
    print("Flexibility in fence", "Flexibility" in md2)


if __name__ == "__main__":
    main()
