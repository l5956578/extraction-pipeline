#!/usr/bin/env python3
"""Convert Threshold/Waystage native PDF mark characters to Unicode tone inventory.

PDF text layer (Paper Capture) often encodes van Ek marks as:
  '  → high mark above (head / high prominence) → ˈ
  ,  → low fall below (before syllable) → ˎ
  .  → mid-height secondary stress → ·
  \"  → fall-rise v-mark above → ˇ
  | or I as bar → tone group boundary |

This is more reliable than freehand Vision for books with a text layer.
Still Vision-verify samples; do not use ASCII ' as final tone glyph.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]

# Map leading mark + rest of token
# Patterns like: 'This  ,bedroom  .there  "animal  "isn't


def convert_line(line: str) -> str:
    s = line
    # Normalize weird spaces
    s = s.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")
    # Fall-rise often as " before word (including after space)
    s = re.sub(r'(^|[\s(|])"+(?=[A-Za-z])', r"\1ˇ", s)
    # High mark ' before letter (not contraction mid-word: n't handled separately)
    # Apply only at start or after space/paren — not inside don't
    s = re.sub(r"(^|[\s(|])'(?=[A-Za-z])", r"\1ˈ", s)
    # Mid-word high (pre'fer) — not contractions n't 's 'll 're 've 'd 'm 'clock
    def _mw(m: re.Match) -> str:
        if m.group(2).lower() in {"t", "s", "ll", "re", "ve", "d", "m", "clock"}:
            return m.group(0)
        return m.group(1) + "ˈ" + m.group(2)

    s = re.sub(r"([A-Za-z])'([A-Za-z])", _mw, s)
    # Low fall comma before letter
    s = re.sub(r"(^|[\s(|]),(?=[A-Za-z])", r"\1ˎ", s)
    # Mid-word comma low fall: ad,dress
    s = re.sub(r"(?<=[A-Za-z]),(?=[A-Za-z])", "ˎ", s)
    # Mid-dot: period before letter (careful: end of sentence . Word)
    # Only . immediately before letter with no space (PDF style .train)
    s = re.sub(r"(^|[\s(|])\.(?=[A-Za-z])", r"\1·", s)
    # Hyphenated Va.letta style already mid inside word: Va.letta → Va·letta
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    # Tone group I used as bar in OCR
    s = re.sub(r"\s+I\s+", " | ", s)
    # Clean double spaces
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


def extract_page_examples(page: fitz.Page) -> list[str]:
    """Return lines that look like exponent examples (have PDF tone marks)."""
    text = page.get_text("text")
    out = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.search(r"['\",\.][A-Za-z]|[A-Za-z]['\"]", line) or '"' in line:
            # skip pure section numbers
            if re.match(r"^\d+(\.\d+)*\s*$", line):
                continue
            out.append(convert_line(line))
    return out


def process_threshold_leaves(leaves: range) -> dict[int, list[str]]:
    pdf = ROOT / "input/cefr-threshold-1990/source.pdf"
    doc = fitz.open(pdf)
    result = {}
    for i in leaves:
        if i < 1 or i > doc.page_count:
            continue
        result[i] = extract_page_examples(doc[i - 1])
    return result


def main() -> None:
    # Dump-only: does NOT write product MD. For product writes use
    # full_md_vs_pdf_intonation.py (multi-iter residual gate).
    print(
        "native_intonation_convert: sample dump only (no product MD write). "
        "PDF ' / , are hints — PNG glyph wins for final marks."
    )
    # Core intonation chapters
    leaves = list(range(34, 65)) + list(range(66, 91)) + list(range(104, 113)) + list(range(124, 131))
    data = process_threshold_leaves(leaves)
    out = ROOT / "work/cefr-threshold-1990/intonation_hires/native_converted_samples.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for leaf, exs in sorted(data.items()):
        if not exs:
            continue
        lines.append(f"===== PDF leaf {leaf} doc {leaf - 6} ({len(exs)} marked lines) =====")
        for e in exs[:40]:
            lines.append(e)
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} leaves_with_marks={sum(1 for v in data.values() if v)}")
    # show leaf 34 gold check
    print("--- leaf 34 sample ---")
    for e in data.get(34, [])[:20]:
        print(e)


if __name__ == "__main__":
    main()
