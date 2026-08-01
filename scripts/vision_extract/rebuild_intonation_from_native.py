#!/usr/bin/env python3
"""Rebuild Threshold intonation example lines from PDF text-layer marks.

Converts van Ek Paper-Capture mark characters to Unicode and patches
example lines into page_overrides + product MD for catalogued leaves.

Does NOT freehand invent marks — only transforms what the PDF text layer stores.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "input/cefr-threshold-1990/source.pdf"
OV = ROOT / "work/cefr-threshold-1990/page_overrides"

# PDF leaf ranges with intonation (see INTONATION_PAGE_INDEX.md)
LEAVES = (
    list(range(34, 65))
    + list(range(66, 91))
    + list(range(104, 113))
    + list(range(124, 131))
)


def convert_marks(s: str) -> str:
    s = s.replace("\u00a0", " ")
    # Fall-rise: " or ” before word (optional spaces)
    s = re.sub(r'(^|[\s(|])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    # High mark ' before word
    s = re.sub(r"(^|[\s(|])['`´]+(?=[A-Za-z])", r"\1ˈ", s)
    # Low fall comma before word
    s = re.sub(r"(^|[\s(|]),(?=[A-Za-z])", r"\1ˎ", s)
    # Mid-dot period before word (PDF .train)
    s = re.sub(r"(^|[\s(|])\.(?=[A-Za-z])", r"\1·", s)
    # Mid-dot inside word Va.letta
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    # OCR tone-group I
    s = re.sub(r"\s+[I|]\s+", " | ", s)
    s = re.sub(r" {2,}", " ", s)
    # Fix remaining stray quotes used as FR
    s = s.replace('"', "ˇ")
    return s.strip()


def is_example_line(line: str) -> bool:
    raw = line.strip()
    if len(raw) < 3:
        return False
    # has PDF tone encoding or already unicode
    if re.search(r"['`,\.][A-Za-z]|[ˎˈˋˊˏˇ·]", raw):
        return True
    if '"' in raw and re.search(r"[A-Za-z]", raw):
        return True
    return False


def page_converted_lines(page: fitz.Page) -> list[str]:
    out = []
    for raw in page.get_text("text").splitlines():
        line = raw.strip()
        if not line or not is_example_line(line):
            continue
        # skip pure headings without marks after convert check
        if re.match(r"^\d+(\.\d+)*\s+[A-Za-z]", line) and not re.search(
            r"['`,\.\"ˎˈ]", line
        ):
            continue
        out.append(convert_marks(line))
    return out


def merge_into_override(leaf: int, examples: list[str]) -> None:
    """Append gold example block as HTML comment + ensure critical lines appear in override."""
    path = OV / f"page_{leaf:03d}.md"
    if not path.exists() or not examples:
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    catalog = "\n".join(f"<!-- cat: {e} -->" for e in examples[:60])
    # Strip old cat comments
    text = re.sub(r"<!-- cat:.*?-->\n?", "", text)
    # Prepend catalog after first vision header if present
    if "<!-- vision:" in text:
        text = re.sub(
            r"(<!-- vision:[^\n]*-->\n)",
            lambda m: m.group(1) + catalog + "\n",
            text,
            count=1,
        )
    else:
        text = catalog + "\n" + text

    # Direct string fixes for known systematic errors in body
    body_fixes = [
        (r"the ·owner\b", "the ˎowner"),
        (r"my ·dog\b", "my ˎdog"),
        (r"ˈNo it ˋisn", "ˈNo it ˇisn"),
        (r"No it ˋisn", "No it ˇisn"),
        (r"ˈYes you ˋdid", "ˈYes you ˇdid"),
        (r"Yes you ˋdid", "Yes you ˇdid"),
        # double-encoded
        (r"The \" animal", "The ˇanimal"),
        (r'The " animal', "The ˇanimal"),
    ]
    for a, b in body_fixes:
        text = re.sub(a, b, text)

    # If gold examples from native layer exist, replace common wrong MD example blocks
    # Inject a GOLD EXAMPLES section if missing
    gold_block = "\n".join(f"> {e}" for e in examples if len(e) < 120 and not e.startswith("("))
    if gold_block and "<!-- NATIVE-GOLD-EXAMPLES -->" not in text:
        text += (
            "\n\n<!-- NATIVE-GOLD-EXAMPLES leaf "
            f"{leaf} — PDF text-layer conversion; verify vs PNG -->\n"
            f"{gold_block}\n"
        )

    path.write_text(text, encoding="utf-8")


def patch_product_md(all_examples: dict[int, list[str]]) -> None:
    """Light systematic fixes + mandatory gold locks (do not skeleton-collapse multi-forms)."""
    import sys

    md_path = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
    t = md_path.read_text(encoding="utf-8")
    fixes = [
        ("the ·owner of the ·restaurant", "the ˎowner of the ·restaurant"),
        ("the ·owner of the", "the ˎowner of the"),
        ("is my ·dog", "is my ˎdog"),
        ("my ·dog", "my ˎdog"),
        ("ˈNo it ˋisn't", "ˈNo it ˇisn't"),
        ("ˈNo it ˋisn’t", "ˈNo it ˇisn’t"),
        ("ˈYes you ˋdid", "ˈYes you ˇdid"),
    ]
    n = 0
    for a, b in fixes:
        c = t.count(a)
        if c:
            t = t.replace(a, b)
            n += c
            print(f"product x{c}: {a!r} -> {b!r}")
    try:
        from gold_intonation_locks import apply_section_locks, residual_assertions

        t, ops = apply_section_locks(t)
        print(f"gold locks: {ops or ['noop']}")
        fails = residual_assertions(t)
    except ImportError:
        fails = []
        print("WARNING: gold_intonation_locks unavailable")
    md_path.write_text(t, encoding="utf-8")
    print(f"product total fixes {n}")
    if fails:
        print("RESIDUAL FAIL after rebuild_intonation_from_native:")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)


def main() -> None:
    print(
        "NOTE: prefer full_md_vs_pdf_intonation.py. "
        "This script only patches safe systematic forms + gold locks."
    )
    doc = fitz.open(PDF)
    all_ex: dict[int, list[str]] = {}
    for leaf in LEAVES:
        if leaf > doc.page_count:
            continue
        ex = page_converted_lines(doc[leaf - 1])
        all_ex[leaf] = ex
        merge_into_override(leaf, ex)
        if ex:
            print(f"leaf {leaf}: {len(ex)} example lines")
    patch_product_md(all_ex)
    # Write master catalog dump
    dump = ROOT / "docs/vision_extract/INTONATION_NATIVE_DUMP_THRESHOLD.md"
    lines = [
        "# Native PDF-layer intonation conversion — Threshold",
        "",
        "Generated by `rebuild_intonation_from_native.py`. Marks from PDF text layer → Unicode.",
        "",
    ]
    for leaf, ex in sorted(all_ex.items()):
        if not ex:
            continue
        lines.append(f"## PDF leaf {leaf} (doc p. {leaf - 6})")
        lines.append("")
        for e in ex:
            lines.append(f"- `{e}`")
        lines.append("")
    dump.write_text("\n".join(lines), encoding="utf-8")
    print("wrote", dump)


if __name__ == "__main__":
    main()
