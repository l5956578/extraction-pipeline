#!/usr/bin/env python3
"""Polish Threshold / Waystage / CEFR 2001 MDs toward Companion conventions.

- Re-assemble with Vision page_overrides (App A nuclear tones)
- Inject major section db:ids from known TOC anchors
- CEFR 2001: native text + pymupdf table extraction (stitched multi-page where needed)
- Snapshot versions/002 + update APPROVED.json
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_book_md import assemble, format_page_body, native_pdf_text_pages, slug  # noqa: E402


def esc_cell(s: str | None) -> str:
    if not s:
        return ""
    s = str(s).replace("\n", " ").replace("|", "\\|").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def table_to_md(rows: list[list[str | None]], db_id: str, pages: str, title: str = "") -> str:
    if not rows:
        return ""
    # normalize col count
    ncol = max(len(r) for r in rows)
    norm = []
    for r in rows:
        cells = [esc_cell(c) for c in r] + [""] * (ncol - len(r))
        # skip fully empty rows
        if not any(cells):
            continue
        norm.append(cells[:ncol])
    if not norm:
        return ""
    # header = first non-empty row; if first row looks like data-only, synthesize H1..Hn
    header = norm[0]
    body = norm[1:] if len(norm) > 1 else []
    if not any(header) and body:
        header = [f"C{i+1}" for i in range(ncol)]
    lines = []
    lines.append(f"<!-- el:start type=table id={db_id} page={pages.split('-')[0]} -->")
    lines.append(f"<!-- db:id={db_id} type=table product_tier=context pages={pages} -->")
    if title:
        lines.append(f"\n**{title}**\n")
    lines.append("")
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join(["---"] * ncol) + " |")
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    lines.append("")
    lines.append(f"<!-- el:end id={db_id} -->")
    return "\n".join(lines)


def extract_cefr_2001() -> Path:
    job = "cefr-en-2001"
    pdf = ROOT / "input" / job / "source.pdf"
    ocr_dir = ROOT / "work" / job / "page_ocr"
    override_dir = ROOT / "work" / job / "page_overrides"
    out_md = ROOT / "output" / job / "CEFR_EN_2001.md"
    render_dir = ROOT / "work" / job / "page_renders"

    doc = fitz.open(pdf)
    n = doc.page_count
    ocr_dir.mkdir(parents=True, exist_ok=True)
    override_dir.mkdir(parents=True, exist_ok=True)

    # Seed native text + table-aware page bodies
    for i in range(n):
        pnum = i + 1
        page = doc[i]
        text = page.get_text("text").strip()
        (ocr_dir / f"page_{pnum:03d}.txt").write_text(text, encoding="utf-8")

        # Build override if tables present
        try:
            tabs = page.find_tables().tables
        except Exception:
            tabs = []
        if not tabs:
            continue

        # prose + tables interleaved roughly: text first, then each table
        body_parts = []
        pid = f"prose_p{pnum:03d}"
        # light heading promotion on first lines
        if text:
            cleaned = format_page_body(pnum, text, job)
            # strip outer el wrappers we'll rebuild
            cleaned = re.sub(r"<!-- el:start[^>]*-->\n?", "", cleaned)
            cleaned = re.sub(r"<!-- el:end[^>]*-->\n?", "", cleaned)
            cleaned = re.sub(r"\*Page \*\*\d+\*\*\n?", "", cleaned).strip()
            body_parts.append(f"<!-- el:start type=prose id={pid} page={pnum} -->")
            body_parts.append(cleaned)
            body_parts.append(f"<!-- el:end id={pid} -->")
        else:
            body_parts.append(f"<!-- el:start type=prose id={pid} page={pnum} -->")
            body_parts.append(f"<!-- el:end id={pid} -->")

        for ti, t in enumerate(tabs, 1):
            data = t.extract()
            # guess title from nearby text
            title = ""
            m = re.search(r"(Table\s+\d+[\w\s:.\-–—]{0,80})", text, re.I)
            if m and ti == 1:
                title = m.group(1).strip()
            db = f"cefr2001_p{pnum:03d}_table_{ti:02d}"
            if title:
                db = "cefr2001_" + slug(title)[:60]
            md_t = table_to_md(data, db, str(pnum), title=title)
            if md_t:
                body_parts.append("")
                body_parts.append(md_t)

        # Figure 1 note on page 32 (index 31)
        if pnum == 32 and "Figure 1" in text:
            body_parts.append("")
            body_parts.append(
                "<!-- el:start type=figure id=cefr2001_figure_01_common_reference_levels page=32 -->\n"
                "<!-- db:id=cefr2001_figure_01_common_reference_levels type=figure product_tier=context pages=32 -->\n\n"
                "**Figure 1.** Common Reference Levels branching: A Basic User (A1 Breakthrough / A2 Waystage); "
                "B Independent User (B1 Threshold / B2 Vantage); C Proficient User (C1 Effective Operational Proficiency / C2 Mastery).\n\n"
                f"<!-- source render: work/{job}/page_renders/page_032.png -->\n"
                "<!-- el:end id=cefr2001_figure_01_common_reference_levels -->"
            )

        (override_dir / f"page_{pnum:03d}.md").write_text("\n".join(body_parts), encoding="utf-8")

    # Section anchors injected at reassembly time via post-pass
    assemble(
        job,
        "Common European Framework of Reference for Languages: Learning, teaching, assessment (2001)",
        "source.pdf",
        n,
        ocr_dir,
        override_dir,
        out_md,
    )
    inject_section_ids(
        out_md,
        [
            (r"(?m)^##\s*Chapter\s*1\b", "cefr2001_ch1", "Chapter 1"),
            (r"(?m)^##\s*Chapter\s*2\b", "cefr2001_ch2", "Chapter 2"),
            (r"(?m)^##\s*3\s+Common Reference Levels|^##\s*Chapter\s*3\b", "cefr2001_ch3_levels", "Chapter 3 Common Reference Levels"),
            (r"(?m)^##\s*Chapter\s*4\b|^##\s*4\s+Language use", "cefr2001_ch4", "Chapter 4"),
            (r"(?m)^##\s*Chapter\s*5\b|^##\s*5\s+The user", "cefr2001_ch5", "Chapter 5"),
            (r"(?m)^##\s*Chapter\s*6\b|^##\s*6\s+Language learning", "cefr2001_ch6", "Chapter 6"),
            (r"(?m)^##\s*Chapter\s*7\b|^##\s*7\s+Tasks", "cefr2001_ch7", "Chapter 7"),
            (r"(?m)^##\s*Chapter\s*8\b", "cefr2001_ch8", "Chapter 8"),
            (r"(?m)^##\s*Chapter\s*9\b|^##\s*9\s+Assessment", "cefr2001_ch9", "Chapter 9"),
            (r"(?m)^##\s*Appendix\s*A\b", "cefr2001_app_a", "Appendix A"),
            (r"(?m)^##\s*Appendix\s*B\b", "cefr2001_app_b", "Appendix B"),
            (r"(?m)^##\s*Appendix\s*C\b", "cefr2001_app_c", "Appendix C"),
            (r"(?m)^##\s*Appendix\s*D\b", "cefr2001_app_d", "Appendix D"),
        ],
    )
    # Header library index
    prepend_library_index(
        out_md,
        "cefr_en_2001",
        n,
        [
            ("Common Reference Levels", "cefr2001_ch3_levels"),
            ("Language use and the language user", "cefr2001_ch4"),
            ("The user/learner competences", "cefr2001_ch5"),
            ("Tasks", "cefr2001_ch7"),
            ("Assessment", "cefr2001_ch9"),
            ("Figure 1 level tree", "cefr2001_figure_01_common_reference_levels"),
        ],
    )
    return out_md


def inject_section_ids(md_path: Path, rules: list[tuple[str, str, str]]) -> None:
    text = md_path.read_text(encoding="utf-8")
    for pat, db_id, label in rules:
        m = re.search(pat, text)
        if not m:
            continue
        # avoid double inject
        window = text[max(0, m.start() - 200) : m.start()]
        if f"db:id={db_id}" in window:
            continue
        inject = (
            f"\n<!-- el:start type=section id={db_id} -->\n"
            f"<!-- db:id={db_id} type=section product_tier=context -->\n"
            f"<!-- section: {label} -->\n"
        )
        text = text[: m.start()] + inject + text[m.start() :]
    md_path.write_text(text, encoding="utf-8")


def prepend_library_index(md_path: Path, doc_id: str, n_pages: int, items: list[tuple[str, str]]) -> None:
    text = md_path.read_text(encoding="utf-8")
    if "library-index:" in text[:2000]:
        return
    lines = ["<!-- library-index:"]
    for name, db in items:
        lines.append(f"- {name} → `{db}`")
    lines.append("-->")
    block = "\n".join(lines) + "\n"
    # insert after first db:id document line if present
    m = re.search(r"(<!-- db:id=\S+ type=document[^\n]*-->\n)", text)
    if m:
        text = text[: m.end()] + block + text[m.end() :]
    else:
        text = block + text
    md_path.write_text(text, encoding="utf-8")


def reassemble_1990(job: str, title: str, out_name: str, section_rules: list, index_items: list) -> Path:
    pdf = ROOT / "input" / job / "source.pdf"
    ocr_dir = ROOT / "work" / job / "page_ocr"
    override_dir = ROOT / "work" / job / "page_overrides"
    out_md = ROOT / "output" / job / out_name
    n = fitz.open(pdf).page_count
    # ensure native seed for threshold
    native_pdf_text_pages(pdf, ocr_dir)
    assemble(job, title, "source.pdf", n, ocr_dir, override_dir if override_dir.exists() else None, out_md)
    inject_section_ids(out_md, section_rules)
    prepend_library_index(out_md, slug(job), n, index_items)
    # OCR cleanup passes
    text = out_md.read_text(encoding="utf-8")
    text = re.sub(r"Lowfalling", "Low falling", text)
    text = re.sub(r"Highfalling", "High falling", text)
    text = re.sub(r"Lowrising", "Low rising", text)
    text = re.sub(r"Highrising", "High rising", text)
    text = re.sub(r"Falling rising", "Falling-rising", text)
    text = re.sub(r"Fallingrising", "Falling-rising", text)
    text = re.sub(r"person-tu-person", "person-to-person", text)
    text = re.sub(r"unitlcredit", "unit/credit", text)
    text = re.sub(r"c o ordinators", "co-ordinators", text)
    text = re.sub(r"frameworkfor", "framework for", text)
    out_md.write_text(text, encoding="utf-8")
    return out_md


def snapshot(job: str, md_name: str, ver: str = "002") -> None:
    out = ROOT / "output" / job
    vdir = out / "versions" / ver
    vdir.mkdir(parents=True, exist_ok=True)
    src = out / md_name
    shutil.copy2(src, vdir / md_name)
    meta = {
        "version": ver,
        "created": datetime.now(timezone.utc).isoformat(),
        "source_md": md_name,
        "method": "vision_ocr_assembly_polish_v2",
        "notes": "App A nuclear tones Vision-rewritten; CEFR 2001 tables extracted; section db:ids",
    }
    (vdir / "VERSION.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    approved = {
        "approved_version": ver,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "path": f"versions/{ver}/{md_name}",
        "product": job,
        "notes": "Vision+OCR polish iteration 2 — nuclear tones structured; Companion conventions applied",
    }
    (out / "APPROVED.json").write_text(json.dumps(approved, indent=2), encoding="utf-8")
    print(f"snapshot {job} -> versions/{ver}", flush=True)


def main() -> None:
    print("=== Threshold 1990 ===", flush=True)
    reassemble_1990(
        "cefr-threshold-1990",
        "Threshold 1990",
        "Threshold_1990.md",
        [
            (r"(?m)^##\s*Preface\b", "threshold_preface", "Preface"),
            (r"(?m)^##\s*Introduction\b", "threshold_introduction", "Introduction"),
            (r"(?m)^##\s*Language functions\b|^##\s*5\s+Language functions", "threshold_language_functions", "Language functions"),
            (r"(?m)^##\s*General notions\b", "threshold_general_notions", "General notions"),
            (r"(?m)^##\s*Specific notions\b", "threshold_specific_notions", "Specific notions"),
            (r"(?m)^##\s*Verbal exchange", "threshold_verbal_exchange_patterns", "Verbal exchange patterns"),
            (r"(?m)^##\s*Sociocultural", "threshold_sociocultural", "Sociocultural competence"),
            (r"(?m)^##\s*Compensation", "threshold_compensation", "Compensation strategies"),
            (r"(?m)^##\s*Learning to learn", "threshold_learning_to_learn", "Learning to learn"),
            (r"(?m)^##\s*Degree of skill", "threshold_degree_of_skill", "Degree of skill"),
            (r"(?m)^##\s*Appendix A|^##\s*Pronunciation", "threshold_appendix_a", "Appendix A Pronunciation"),
            (r"(?m)^##\s*Grammatical summary|^##\s*Appendix B", "threshold_appendix_b", "Appendix B Grammatical summary"),
        ],
        [
            ("Language functions", "threshold_language_functions"),
            ("General notions", "threshold_general_notions"),
            ("Specific notions", "threshold_specific_notions"),
            ("Verbal exchange patterns", "threshold_verbal_exchange_patterns"),
            ("Five nuclear tones", "threshold_five_nuclear_tones"),
            ("Pronunciation and intonation", "threshold_appendix_a"),
            ("Grammatical summary", "threshold_appendix_b"),
        ],
    )
    snapshot("cefr-threshold-1990", "Threshold_1990.md")

    print("=== Waystage 1990 ===", flush=True)
    reassemble_1990(
        "cefr-waystage-1990",
        "Waystage 1990",
        "Waystage_1990.md",
        [
            (r"(?m)^##\s*Preface\b", "waystage_preface", "Preface"),
            (r"(?m)^##\s*Introduction\b", "waystage_introduction", "Introduction"),
            (r"(?m)^##\s*Language functions\b", "waystage_language_functions", "Language functions"),
            (r"(?m)^##\s*General notions\b", "waystage_general_notions", "General notions"),
            (r"(?m)^##\s*Themes|^##\s*Specific notions", "waystage_themes_specific_notions", "Themes and specific notions"),
            (r"(?m)^##\s*68 AppendixA|^##\s*A Pronunciation|^##\s*Appendix A", "waystage_appendix_a", "Appendix A Pronunciation"),
            (r"(?m)^##\s*Grammatical summary|^##\s*B Grammatical", "waystage_appendix_b", "Appendix B Grammatical summary"),
        ],
        [
            ("Language functions", "waystage_language_functions"),
            ("General notions", "waystage_general_notions"),
            ("Themes and specific notions", "waystage_themes_specific_notions"),
            ("Five nuclear tones", "waystage_five_nuclear_tones"),
            ("Pronunciation and intonation", "waystage_appendix_a"),
        ],
    )
    snapshot("cefr-waystage-1990", "Waystage_1990.md")

    print("=== CEFR EN 2001 ===", flush=True)
    extract_cefr_2001()
    snapshot("cefr-en-2001", "CEFR_EN_2001.md")

    # metrics
    for job, name in [
        ("cefr-threshold-1990", "Threshold_1990.md"),
        ("cefr-waystage-1990", "Waystage_1990.md"),
        ("cefr-en-2001", "CEFR_EN_2001.md"),
    ]:
        p = ROOT / "output" / job / name
        c = p.read_text(encoding="utf-8")
        print(
            job,
            "KB",
            round(p.stat().st_size / 1024),
            "pages",
            len(re.findall(r"<!-- page:\d+", c)),
            "db:id",
            len(re.findall(r"db:id=", c)),
            "tables",
            len(re.findall(r"type=table", c)),
            "nuclear",
            len(re.findall(r"\[LF\]|nuclear tone", c, re.I)),
        )


if __name__ == "__main__":
    main()
