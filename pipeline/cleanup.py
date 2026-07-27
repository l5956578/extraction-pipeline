"""Rule-based OCR cleanup (LLM-ready structure preserved)."""

from __future__ import annotations

import re
from pathlib import Path

import pipeline.config as cfg
from pipeline.prose_format import normalize_prose
from pipeline.utils import is_gibberish

def _fix_broken_words(text: str) -> str:
    # Hyphenation across line breaks
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    # Common OCR ligature artifacts
    replacements = {
        "–­": "–",
        "\xad": "",
        "ﬁ": "fi",
        "ﬂ": "fl",
        "  ": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def _fix_reversed_fragments(text: str) -> str:
    from pipeline.extractors.rotated import _reverse_line
    from pipeline.utils import english_word_score, is_gibberish

    lines = []
    for line in text.splitlines():
        if not (line.strip().startswith("|") and line.count("|") >= 3):
            lines.append(line)
            continue
        cells = line.split("|")
        fixed = []
        for cell in cells:
            if len(cell.split()) >= 4 and is_gibberish(cell):
                rev = _reverse_line(cell)
                if english_word_score(rev) > english_word_score(cell):
                    fixed.append(rev)
                else:
                    fixed.append(cell)
            else:
                fixed.append(cell)
        lines.append("|".join(fixed))
    return "\n".join(lines)

def cleanup_text(text: str) -> tuple[str, list[str]]:
    fixes = []
    original = text

    text = _fix_broken_words(text)
    if text != original:
        fixes.append("fixed hyphenation/ligatures")

    text2 = _fix_reversed_fragments(text)
    if text2 != text:
        fixes.append("fixed reversed fragments")
        text = text2

    # Remove repeated consecutive lines
    lines = text.splitlines()
    deduped = []
    for line in lines:
        if deduped and line == deduped[-1] and line.strip():
            fixes.append("removed duplicate line")
            continue
        deduped.append(line)
    text = "\n".join(deduped)

    text_pages, page_fix = _dedupe_page_markers(text)
    if page_fix:
        fixes.append(page_fix)
        text = text_pages

    text3, prose_fixes = normalize_prose(text)
    if text3 != text:
        fixes.extend(prose_fixes)
        text = text3

    return text, fixes

_PAGE_COMMENT = re.compile(r"^<!-- page:(\d+) -->\s*$")
_PAGE_ITALIC = re.compile(r"^\*.*\b[Pp]age\b.*\*$")

def _dedupe_page_markers(text: str) -> tuple[str, str | None]:
    """Collapse consecutive duplicate <!-- page:N --> blocks (and optional italic caption)."""
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    removed = 0
    last_page: str | None = None
    while i < len(lines):
        m = _PAGE_COMMENT.match(lines[i].strip())
        if not m:
            out.append(lines[i])
            i += 1
            continue
        page = m.group(1)
        block = [lines[i]]
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines) and (
            _PAGE_ITALIC.match(lines[j].strip()) or lines[j].strip().startswith("*")
        ):
            block.append(lines[j])
            j += 1
        if page == last_page:
            removed += 1
            i = j
            continue
        last_page = page
        out.extend(block)
        i = j
    if not removed:
        return text, None
    return "\n".join(out), f"removed {removed} duplicate page marker(s)"

def cleanup_file(src: Path, dest: Path) -> dict:
    text = src.read_text(encoding="utf-8")
    cleaned, fixes = cleanup_text(text)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(cleaned, encoding="utf-8")
    return {"source": str(src), "dest": str(dest), "fixes": fixes}

def cleanup_all() -> list[dict]:
    reports = []
    for src in sorted(cfg.RAW_DIR.glob("chunk_*.md")):
        dest = cfg.CLEANED_DIR / src.name
        reports.append(cleanup_file(src, dest))
        print(f"Cleaned {dest.name}")
    return reports

if __name__ == "__main__":
    from pipeline.bootstrap import parse_and_load_job

    parse_and_load_job(description="Cleanup raw extraction chunks")
    cleanup_all()