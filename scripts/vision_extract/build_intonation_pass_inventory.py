#!/usr/bin/env python3
"""Build docs/vision_extract/INTONATION_PASS_INVENTORY.md for Threshold + Waystage."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/vision_extract/INTONATION_PASS_INVENTORY.md"


def thr_chapter(leaf: int) -> str:
    if 33 <= leaf <= 53:
        return "5 Language functions"
    if 54 <= leaf <= 64:
        return "6 General notions"
    if 65 <= leaf <= 87:
        return "7 Specific notions"
    if 88 <= leaf <= 93:
        return "8 Verbal exchange"
    if 100 <= leaf <= 108:
        return "11 Sociocultural"
    if 109 <= leaf <= 112:
        return "12 Compensation"
    if 121 <= leaf <= 130:
        return "Appendix A"
    if leaf in (14, 19):
        return "front/intro (hit)"
    if leaf == 95:
        return "misc hit"
    if leaf == 115:
        return "misc hit"
    if 134 <= leaf <= 162:
        return "grammar appendix (secondary)"
    return "other"


def way_chapter(leaf: int) -> str:
    if 21 <= leaf <= 27:
        return "3 Language functions"
    if 28 <= leaf <= 35:
        return "4 General notions"
    if 36 <= leaf <= 47:
        return "5 Themes / specific notions"
    if 52 <= leaf <= 55:
        return "8 Sociocultural"
    if 56 <= leaf <= 61:
        return "9 Verbal exchange"
    if 62 <= leaf <= 65:
        return "10 Compensation"
    if 74 <= leaf <= 80:
        return "Appendix A"
    if 82 <= leaf <= 100:
        return "grammar appendix (secondary)"
    return "other"


def thr_passes(leaf: int) -> tuple[list[tuple[str, int]], int, str]:
    ov = ROOT / f"work/cefr-threshold-1990/page_overrides/page_{leaf:03d}.md"
    if not ov.exists():
        return [("none", 0)], 0, "no override"
    t = ov.read_text(encoding="utf-8", errors="replace")
    head = t[:1000]

    passes: list[tuple[str, int]] = []
    passes.append(("full-book Vision (v004)", 1))

    primary = set(
        list(range(34, 65))
        + list(range(66, 91))
        + list(range(104, 113))
        + list(range(124, 131))
    )
    secondary = {14, 19, 95, 115} | set(range(134, 163))
    if leaf in primary or leaf in secondary:
        passes.append(("native PDF mark convert", 1))

    labels: list[str] = []
    if 34 <= leaf <= 45:
        labels += ["Vision MP: gold 34–45", "Vision MP: ch5–6 34–64"]
    elif 46 <= leaf <= 56:
        labels += ["Vision MP: gold 46–56", "Vision MP: ch5–6 34–64"]
    elif 57 <= leaf <= 64:
        labels += ["Vision MP: gold 57–75", "Vision MP: ch5–6 34–64"]
    elif leaf == 65:
        labels += ["Vision MP: gold 57–75 (scan)"]
    elif 66 <= leaf <= 75:
        labels += ["Vision MP: gold 57–75", "Vision MP: ch7–8 66–90"]
    elif 76 <= leaf <= 90:
        labels += ["Vision MP: ch7–8 66–90"]
    elif leaf in set(range(104, 113)) | set(range(124, 131)):
        labels += ["Vision MP: socio+AppA 104–130"]

    if leaf == 34:
        labels.append("Vision MP: leaf-34 gold catalog/restore")
        passes.append(("gold force-restore product MD", 1))

    for lab in labels:
        passes.append((lab, 1))

    if leaf in primary or leaf in secondary or "multipass" in head.lower():
        passes.append(("product MD tone merge/OCR convert", 1))

    total = sum(c for _, c in passes)
    if leaf == 34:
        note = "GOLD template page"
    elif "multipass" in head.lower() or "word-catalog" in head.lower():
        note = "multipass"
    else:
        note = "full-book / secondary"
    return passes, total, note


def way_passes(leaf: int) -> tuple[list[tuple[str, int]], int, str]:
    ov = ROOT / f"work/cefr-waystage-1990/page_overrides/page_{leaf:03d}.md"
    if not ov.exists():
        return [("none", 0)], 0, "no override"
    t = ov.read_text(encoding="utf-8", errors="replace")

    passes: list[tuple[str, int]] = []
    passes.append(("full-book Vision (v004)", 1))

    primary = set(
        list(range(22, 36))
        + list(range(38, 48))
        + list(range(56, 66))
        + list(range(77, 81))
    )
    secondary = set(list(range(52, 56)) + list(range(82, 101)) + list(range(64, 69)))

    if leaf in primary:
        passes.append(("Vision MP: Waystage primary bands", 1))
        cat = (
            ROOT
            / f"work/cefr-waystage-1990/intonation_hires/catalogs/leaf_{leaf:03d}_catalog.md"
        )
        if cat.exists():
            passes.append(("word-catalog file written", 1))
        passes.append(("hi-res crop multipass (4x/bands)", 1))
        passes.append(("product MD OCR mark convert + gold fix", 1))
        note = "primary multipass"
    elif leaf in secondary or re.search(r"[ˈˎˋˏˊˇ·]", t):
        passes.append(("product MD OCR mark convert (residual)", 1))
        note = "secondary/residual"
    else:
        note = "full-book only"

    if leaf == 22:
        passes.append(("gold force-restore contrastive bedroom", 1))

    total = sum(c for _, c in passes)
    return passes, total, note


def product_tone_pages(job: str, mdname: str) -> dict[int, int]:
    """Count Unicode tone marks in the body that ends at each <!-- page:N -->."""
    md = (ROOT / f"output/{job}/{mdname}").read_text(encoding="utf-8")
    pages: dict[int, int] = {}
    for m in re.finditer(r"<!-- page:(\d+) -->", md):
        doc = int(m.group(1))
        prev = list(
            re.finditer(r"<!-- page:(\d+|front-[^\s]+) -->", md[: m.start()])
        )
        start = prev[-1].end() if prev else 0
        body = md[start : m.start()]
        pages[doc] = len(re.findall(r"[ˈˎˋˏˊˇ·]", body))
    return pages


def fmt_breakdown(passes: list[tuple[str, int]]) -> str:
    parts = []
    for name, n in passes:
        if n == 0:
            continue
        parts.append(f"{n}× {name}" if n != 1 else name)
    return "; ".join(parts)


def main() -> None:
    thr_tones = product_tone_pages("cefr-threshold-1990", "Threshold_1990.md")
    way_tones = product_tone_pages("cefr-waystage-1990", "Waystage_1990.md")

    thr_leaves = set(
        list(range(34, 65))
        + list(range(66, 91))
        + list(range(104, 113))
        + list(range(124, 131))
        + [14, 19, 95, 115]
        + list(range(134, 163))
    )
    for p in (ROOT / "work/cefr-threshold-1990/page_overrides").glob("page_*.md"):
        leaf = int(p.stem.split("_")[1])
        head = p.read_text(encoding="utf-8", errors="replace")[:500]
        if "multipass" in head.lower() or "word-catalog" in head.lower():
            thr_leaves.add(leaf)
    thr_leaves = sorted(thr_leaves)

    way_leaves = set(
        list(range(22, 36))
        + list(range(38, 48))
        + list(range(56, 66))
        + list(range(77, 81))
        + list(range(52, 56))
        + list(range(82, 101))
    )
    for p in (ROOT / "work/cefr-waystage-1990/page_overrides").glob("page_*.md"):
        leaf = int(p.stem.split("_")[1])
        head = p.read_text(encoding="utf-8", errors="replace")[:500]
        if "multipass" in head.lower() or "word-catalog" in head.lower():
            way_leaves.add(leaf)
    way_leaves = sorted(way_leaves)

    lines: list[str] = []
    lines += [
        "# Intonation pass inventory — Threshold & Waystage 1990",
        "",
        "**Generated:** 2026-07-31  ",
        "**Purpose:** Per-page list of quality passes applied for intonation (and full-book Vision baseline).  ",
        "**Related:** `INTONATION_PAGE_INDEX.md`, `VISION_PASS_LOG.md`, `EXTRACTION_STATUS_1990_2001.md`  ",
        "",
        "## What counts as a “pass”",
        "",
        "| Pass type | Meaning |",
        "|-----------|---------|",
        "| **full-book Vision (v004)** | Initial Vision page_override for every PDF leaf |",
        "| **native PDF mark convert** | Threshold Paper-Capture text layer → Unicode tones (mechanical) |",
        "| **Vision MP: …** | Dedicated high-precision intonation multipass (zoom/word-catalog rewrite) |",
        "| **word-catalog file** | Per-leaf catalog under `intonation_hires/catalogs/` |",
        "| **hi-res crop multipass** | 4× full + L/R + bands prepared for Vision |",
        "| **product MD tone merge/OCR convert** | Product MD mark repair (not freehand invent) |",
        "| **gold force-restore** | Section-aware lock for 1.1.3–1.3.4 (LF vs contrastive) |",
        "",
        "**Note:** Parallel agents rewrote some leaves more than once. Counts include **distinct documented campaigns** that targeted that leaf (not every intermediate crop tool call). Re-Vision *within* a campaign is folded into that campaign’s single Vision MP line.",
        "",
        "**Document page formula:** `doc = PDF leaf − 6` (Arabic p.1 = leaf 7).",
        "",
        "---",
        "",
        "## Threshold 1990",
        "",
        "**Product:** `output/cefr-threshold-1990/Threshold_1990.md` (APPROVED v006)  ",
        "**Overrides:** `work/cefr-threshold-1990/page_overrides/`",
        "",
        "### Summary by band",
        "",
        "| Band | PDF leaves | Doc pages | Typical passes/page |",
        "|------|------------|-----------|---------------------:|",
        "| Ch.5 Language functions | 34–53 | 28–47 | 5–6 |",
        "| Ch.6 General notions | 54–64 | 48–58 | 5–6 |",
        "| Ch.7 Specific notions | 66–87 | 60–81 | 4–5 |",
        "| Ch.8 Verbal exchange | 88–90 | 82–84 | 4 |",
        "| Ch.11 Sociocultural | 104–108 | 98–102 | 4 |",
        "| Ch.12 Compensation | 109–112 | 103–106 | 4 |",
        "| Appendix A | 124–130 | 118–124 | 4 |",
        "| Grammar appendix (secondary) | 134–162 | 128–156 | 2–3 |",
        "| Full book (non-intonation pages) | other | — | 1 (full-book Vision only) |",
        "",
        "### Per-page detail (intonation-targeted leaves)",
        "",
        "| PDF leaf | Doc p. | Chapter / band | Passes (total) | Pass breakdown | Unicode tones (product page) | Class |",
        "|---------:|-------:|----------------|---------------:|----------------|-----------------------------:|-------|",
    ]

    thr_rows: list[tuple] = []
    for leaf in thr_leaves:
        doc = leaf - 6 if leaf >= 7 else None
        ch = thr_chapter(leaf)
        passes, total, note = thr_passes(leaf)
        breakdown = fmt_breakdown(passes)
        pt = thr_tones.get(doc, 0) if doc else 0
        thr_rows.append((leaf, doc, ch, total, breakdown, pt, note))
        lines.append(
            f"| {leaf} | {doc if doc is not None else '—'} | {ch} | **{total}** | {breakdown} | {pt} | {note} |"
        )

    lines += [
        "",
        f"**Threshold intonation-targeted leaves listed:** {len(thr_rows)}  ",
        f"**Sum of pass-counts (listed leaves):** {sum(r[3] for r in thr_rows)}  ",
        "**Full book also has 1× full-book Vision on remaining leaves** (192 total overrides).",
        "",
        "---",
        "",
        "## Waystage 1990",
        "",
        "**Product:** `output/cefr-waystage-1990/Waystage_1990.md` (APPROVED v006)  ",
        "**Overrides:** `work/cefr-waystage-1990/page_overrides/`  ",
        "**Note:** Image PDF (no text layer) — no native PDF convert pass.",
        "",
        "### Summary by band",
        "",
        "| Band | PDF leaves | Doc pages | Typical passes/page |",
        "|------|------------|-----------|---------------------:|",
        "| Ch.3 Language functions | 22–27 | 16–21 | 5–6 |",
        "| Ch.4 General notions | 28–35 | 22–29 | 5 |",
        "| Ch.5 Themes / specific notions | 38–47 | 32–41 | 5 |",
        "| Ch.9 Verbal exchange | 56–61 | 50–55 | 5 |",
        "| Ch.10 Compensation | 62–65 | 56–59 | 5 |",
        "| Appendix A | 77–80 | 71–74 | 5 |",
        "| Grammar appendix (secondary) | 82–100 | 76–94 | 2 |",
        "| Full book (other pages) | other | — | 1 (full-book Vision only) |",
        "",
        "### Per-page detail (intonation-targeted leaves)",
        "",
        "| PDF leaf | Doc p. | Chapter / band | Passes (total) | Pass breakdown | Unicode tones (product page) | Class |",
        "|---------:|-------:|----------------|---------------:|----------------|-----------------------------:|-------|",
    ]

    way_rows: list[tuple] = []
    for leaf in way_leaves:
        doc = leaf - 6 if leaf >= 7 else None
        ch = way_chapter(leaf)
        passes, total, note = way_passes(leaf)
        breakdown = fmt_breakdown(passes)
        pt = way_tones.get(doc, 0) if doc else 0
        way_rows.append((leaf, doc, ch, total, breakdown, pt, note))
        lines.append(
            f"| {leaf} | {doc if doc is not None else '—'} | {ch} | **{total}** | {breakdown} | {pt} | {note} |"
        )

    lines += [
        "",
        f"**Waystage intonation-targeted leaves listed:** {len(way_rows)}  ",
        f"**Sum of pass-counts (listed leaves):** {sum(r[3] for r in way_rows)}  ",
        "**Full book also has 1× full-book Vision on remaining leaves** (120 total overrides).",
        "",
        "---",
        "",
        "## Pass-count histogram (listed leaves only)",
        "",
        "### Threshold",
    ]
    for k, n in sorted(Counter(r[3] for r in thr_rows).items()):
        lines.append(f"- **{k} passes:** {n} pages")
    lines += ["", "### Waystage"]
    for k, n in sorted(Counter(r[3] for r in way_rows).items()):
        lines.append(f"- **{k} passes:** {n} pages")

    lines += ["", "## Highest-effort pages (by pass total)", "", "### Threshold (top)"]
    for r in sorted(thr_rows, key=lambda x: (-x[3], x[0]))[:15]:
        lines.append(f"- leaf **{r[0]}** (doc p.{r[1]}): **{r[3]}** passes — {r[2]}")
    lines += ["", "### Waystage (top)"]
    for r in sorted(way_rows, key=lambda x: (-x[3], x[0]))[:15]:
        lines.append(f"- leaf **{r[0]}** (doc p.{r[1]}): **{r[3]}** passes — {r[2]}")

    lines += [
        "",
        "---",
        "",
        "## Campaign map (source of Vision MP lines)",
        "",
        "| Campaign | Book | Leaves | Agent / method |",
        "|----------|------|--------|----------------|",
        "| Full-book Vision v004 | both | all | prior full-book override generation |",
        "| Native PDF convert | Threshold | primary+secondary | `full_intonation_pass.py` |",
        "| Gold multipass 34–45 | Threshold | 34–45 | subagent gold Vision |",
        "| Gold multipass 46–56 | Threshold | 46–56 | subagent gold Vision |",
        "| Gold multipass 57–75 | Threshold | 57–75 | subagent gold Vision |",
        "| Ch5–6 multipass 34–64 | Threshold | 34–64 | subagent Vision |",
        "| Ch7–8 multipass 66–90 | Threshold | 66–90 | subagent Vision |",
        "| Socio+AppA 104–130 | Threshold | 104–112, 124–130 | subagent Vision |",
        "| Leaf-34 gold catalog | Threshold | 34 | `INTONATION_WORD_CATALOG_LEAF034.md` + restore |",
        "| Waystage primary multipass | Waystage | 22–35, 38–47, 56–65, 77–80 | subagent Vision (38 pages) |",
        "| OCR→Unicode product | Waystage (+THR residual) | product MD | `convert_md_ocr_marks.py` |",
        "",
        "*End of inventory.*",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"THR pages={len(thr_rows)} pass_sum={sum(r[3] for r in thr_rows)}")
    print(f"WAY pages={len(way_rows)} pass_sum={sum(r[3] for r in way_rows)}")


if __name__ == "__main__":
    main()
