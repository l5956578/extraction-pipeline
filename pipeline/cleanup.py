"""Rule-based OCR cleanup (LLM-ready structure preserved)."""

from __future__ import annotations

import re
from pathlib import Path

from pipeline.config import CLEANED_DIR, RAW_DIR
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

    text3, prose_fixes = normalize_prose(text)
    if text3 != text:
        fixes.extend(prose_fixes)
        text = text3

    return text, fixes


def cleanup_file(src: Path, dest: Path) -> dict:
    text = src.read_text(encoding="utf-8")
    cleaned, fixes = cleanup_text(text)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(cleaned, encoding="utf-8")
    return {"source": str(src), "dest": str(dest), "fixes": fixes}


def cleanup_all() -> list[dict]:
    reports = []
    for src in sorted(RAW_DIR.glob("chunk_*.md")):
        dest = CLEANED_DIR / src.name
        reports.append(cleanup_file(src, dest))
        print(f"Cleaned {dest.name}")
    return reports


if __name__ == "__main__":
    cleanup_all()