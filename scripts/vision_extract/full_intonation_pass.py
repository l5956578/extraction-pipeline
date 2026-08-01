#!/usr/bin/env python3
"""High-precision intonation multipass for Threshold (+ Waystage when text layer exists).

Strategy (Threshold Paper Capture PDF):
  PDF text-layer mark characters → Unicode van Ek inventory
  Patch product MD by letter-skeleton match on example-like lines
  Patch page_overrides the same way
  Write native gold dump + word catalog stats

Does NOT freehand invent marks. Vision still required for Waystage image PDF.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]

# Full primary + secondary bands from INTONATION_PAGE_INDEX + scan
THR_LEAVES = (
    list(range(34, 65))  # Ch5–6
    + list(range(66, 91))  # Ch7–8
    + list(range(104, 113))  # socio + compensation
    + list(range(124, 131))  # App A
    + list(range(134, 137))  # grammar appendix samples
    + [14, 19, 95, 115]  # isolated hits (verify)
)

WAY_LEAVES = (
    list(range(22, 36))
    + list(range(38, 48))
    + list(range(56, 66))
    + list(range(77, 81))
    + list(range(82, 85))
    + list(range(87, 101))
)


def convert_marks(s: str) -> str:
    """PDF Paper-Capture mark glyphs → Unicode inventory."""
    s = s.replace("\u00a0", " ")
    s = s.replace("\u2018", "'").replace("\u2019", "'")  # ‘ ’
    s = s.replace("\u201c", '"').replace("\u201d", '"')  # “ ”
    # OCR $ as low fall
    s = re.sub(r"\$+(?=[A-Za-z])", "ˎ", s)
    # Fall-rise " before letter (token start)
    s = re.sub(r'(^|[\s(|/>])["”„]+[ ]*(?=[A-Za-z])', r"\1ˇ", s)
    # High ' before letter at token start (not inside don't — mid ' stays)
    s = re.sub(r"(^|[\s(|/>])['`´]+(?=[A-Za-z])", r"\1ˈ", s)
    # Low fall comma before letter at token start
    s = re.sub(r"(^|[\s(|/>]),(?=[A-Za-z])", r"\1ˎ", s)
    # Mid-word comma low fall: ad,dress fif,teen din,ner
    s = re.sub(r"(?<=[A-Za-z]),(?=[A-Za-z])", "ˎ", s)
    # Mid-dot period before letter at token start
    s = re.sub(r"(^|[\s(|/>])\.(?=[A-Za-z])", r"\1·", s)
    # Mid-word period secondary: Va.letta down.stairs
    s = re.sub(r"(?<=[A-Za-z])\.(?=[A-Za-z])", "·", s)
    # slash-bound mid marks: man/.woman
    s = s.replace("/.", "/·")
    # tone group I as bar
    s = re.sub(r"\s+I\s+", " | ", s)
    s = re.sub(r"\s+\|\s+", " | ", s)
    # leftover double-quote FR if any remain attached
    s = re.sub(r'(?<=[\s(|])"+(?=[A-Za-z])', "ˇ", s)
    s = re.sub(r" {2,}", " ", s)
    return s.strip()


def strip_marks_for_match(s: str) -> str:
    try:
        from gold_intonation_locks import strip_skel

        return strip_skel(s)
    except ImportError:
        s = s.replace("\u2019", "'").replace("\u2018", "'")
        s = re.sub(r"[ˈˎˋˏˊˇ·ˌ'`´,.\"|\$]+", "", s)
        s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
        return re.sub(r"\s+", " ", s)


def has_pdf_tone_encoding(line: str) -> bool:
    if re.search(r"['`,\.\"][A-Za-z]|[A-Za-z]['\"]|[A-Za-z],[A-Za-z]|[A-Za-z]\.[A-Za-z]", line):
        return True
    if '"' in line and re.search(r"[A-Za-z]", line):
        return True
    if re.search(r"\$[A-Za-z]", line):
        return True
    return False


def collect_gold(pdf_path: Path, leaves: list[int]) -> dict[int, list[str]]:
    doc = fitz.open(pdf_path)
    by_leaf: dict[int, list[str]] = {}
    for leaf in leaves:
        if leaf < 1 or leaf > doc.page_count:
            continue
        exs = []
        for raw in doc[leaf - 1].get_text("text").splitlines():
            line = raw.strip()
            if not line or len(line) < 3 or len(line) > 140:
                continue
            if re.match(r"^\d+(\.\d+)*\s*$", line):
                continue
            if not has_pdf_tone_encoding(line):
                continue
            g = convert_marks(line)
            if re.search(r"[ˈˎˋˏˊˇ·]", g) and re.search(r"[A-Za-z]{2,}", g):
                # skip pure section headers like "1.1.3 Asking for information"
                if re.match(r"^\d+(\.\d+)+\s+[A-Za-z]", g) and not re.search(
                    r"[ˈˎˋˏˊˇ·].*[A-Za-z]{3,}", g
                ):
                    continue
                exs.append(g)
        # unique by skeleton
        seen = set()
        uniq = []
        for e in exs:
            k = strip_marks_for_match(e)
            if k in seen or len(k) < 4:
                continue
            seen.add(k)
            uniq.append(e)
        by_leaf[leaf] = uniq
    doc.close()
    return by_leaf


def gold_map(by_leaf: dict[int, list[str]]) -> dict[str, str]:
    m: dict[str, str] = {}
    for exs in by_leaf.values():
        for e in exs:
            k = strip_marks_for_match(e)
            # prefer longer / more marked if collision
            if k not in m or e.count("ˈ") + e.count("ˎ") + e.count("ˇ") > m[k].count(
                "ˈ"
            ) + m[k].count("ˎ") + m[k].count("ˇ"):
                m[k] = e
    return m


SYSTEMATIC = [
    (r"\bthe ·owner\b", "the ˎowner"),
    (r"\bmy ·dog\b", "my ˎdog"),
    (r"is my ·dog\b", "is my ˎdog"),
    (r"ˈNo it ˋisn(['’]?t)", r"ˈNo it ˇisn\1"),
    (r"No it ˋisn(['’]?t)", r"No it ˇisn\1"),
    (r"ˈYes you ˋdid\b", "ˈYes you ˇdid"),
    (r"Yes you ˋdid\b", "Yes you ˇdid"),
    (r"The \" animal", "The ˇanimal"),
    (r'The " animal', "The ˇanimal"),
    # wrong low-fall as IPA secondary
    (r"(?<=\s)ˌ(?=[A-Za-z])", "ˎ"),
    # ASCII apostrophe as standalone tone before capital (common residual)
    (r"(^|[\s>|])'(?=[A-Z])", r"\1ˈ"),
]


# Multi-form skeletons — never collapse via letter match (PNG section locks only)
_PROTECTED_SKEL = {
    strip_marks_for_match(s)
    for s in [
        "This is the bedroom",
        "The train has left",
        "No it isnt",
        "Yes you did",
        "Did you see him",
        "You saw him",
        "They lost the match didnt they",
        "Please can you tell me the way to the station",
        "The animal over there is my dog",
        "He is the owner of the restaurant",
    ]
}


def patch_text(text: str, gmap: dict[str, str]) -> tuple[str, int, int]:
    n_bq = 0
    n_sys = 0

    def repl_line(m: re.Match) -> str:
        nonlocal n_bq
        prefix, body = m.group(1), m.group(2)
        # preserve trailing spaces/punctuation only in body strip carefully
        core = body.strip()
        # strip outer markdown emphasis
        bare = re.sub(r"^\*+|\*+$", "", core).strip()
        key = strip_marks_for_match(bare)
        if key in _PROTECTED_SKEL:
            return m.group(0)
        if key in gmap:
            g = gmap[key]
            if g != bare and re.search(r"[ˈˎˋˏˊˇ·]", g):
                n_bq += 1
                # keep * wrappers if present
                if core.startswith("*") and core.endswith("*"):
                    return f"{prefix}*{g}*"
                return f"{prefix}{g}"
        return m.group(0)

    # blockquotes and plain lines that look like marked examples
    text = re.sub(r"^(>\s*)(.+)$", repl_line, text, flags=re.M)
    # also bare example lines starting with tone mark
    text = re.sub(
        r"^([ \t]*)([ˈˎˋˏˊˇ·'`,.\"][^\n]{3,120})$",
        repl_line,
        text,
        flags=re.M,
    )

    for a, b in SYSTEMATIC:
        text, c = re.subn(a, b, text)
        n_sys += c
    return text, n_bq, n_sys


def force_contrastive_fixes(text: str) -> tuple[str, int]:
    """1.3.1 contrastive + section locks via gold_intonation_locks (PNG wins)."""
    try:
        from gold_intonation_locks import apply_section_locks

        fixed, ops = apply_section_locks(text)
        return fixed, len(ops)
    except ImportError:
        pass
    # Fallback if module unavailable: **1.3.1** bold form (product MD style)
    n = 0
    m = re.search(
        r"(\*\*1\.3\.1\*\*[\s\S]*?)(\*\*1\.3\.2\*\*|\*\*1\.3\.5\*\*|####\s*1\.4\b)",
        text,
    )
    if m:
        block = m.group(1)
        fixed = block
        fixed = re.sub(
            r">\s*[ˈˋ]This is the ˎbedroom\.",
            "> ˋThis is the ·bedroom.",
            fixed,
        )
        fixed = re.sub(
            r">\s*[ˈˋ]This is the ·bedroom\.",
            "> ˋThis is the ·bedroom.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ˈtrain has ˎleft\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        fixed = re.sub(
            r">\s*The ·train ˈhas ·left\.",
            "> The ·train ˋhas ·left.",
            fixed,
        )
        if fixed != block:
            text = text[: m.start(1)] + fixed + text[m.end(1) :]
            n += 1
    return text, n


def patch_overrides(ov_dir: Path, by_leaf: dict[int, list[str]], gmap: dict[str, str]) -> int:
    n_files = 0
    for leaf, exs in by_leaf.items():
        path = ov_dir / f"page_{leaf:03d}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        text, n1, n2 = patch_text(text, gmap)
        text, n3 = force_contrastive_fixes(text)
        # catalog comments
        catalog = "\n".join(f"<!-- cat: {e} -->" for e in exs[:80])
        text = re.sub(r"<!-- cat:.*?-->\n?", "", text)
        if "<!-- vision:" in text:
            text = re.sub(
                r"(<!-- vision:[^\n]*-->\n)",
                lambda m: m.group(1) + catalog + "\n",
                text,
                count=1,
            )
        else:
            text = f"<!-- native-intonation leaf {leaf} -->\n" + catalog + "\n" + text
        # gold block
        gold_block = "\n".join(
            f"> {e}" for e in exs if len(e) < 120 and not e.startswith("(")
        )
        if gold_block:
            if "<!-- NATIVE-GOLD-EXAMPLES -->" in text:
                text = re.sub(
                    r"<!-- NATIVE-GOLD-EXAMPLES -->.*?((?=\n<!--)|\Z)",
                    f"<!-- NATIVE-GOLD-EXAMPLES -->\n{gold_block}\n",
                    text,
                    count=1,
                    flags=re.S,
                )
            else:
                text += (
                    f"\n\n<!-- NATIVE-GOLD-EXAMPLES leaf {leaf} -->\n{gold_block}\n"
                )
        path.write_text(text, encoding="utf-8")
        n_files += 1
        if n1 or n2 or n3:
            print(f"  override leaf {leaf}: bq={n1} sys={n2} contrast={n3}")
    return n_files


def write_dump(path: Path, by_leaf: dict[int, list[str]], title: str) -> None:
    lines = [
        f"# {title}",
        "",
        "Generated by `full_intonation_pass.py`. PDF text-layer → Unicode.",
        "",
    ]
    total = 0
    for leaf, exs in sorted(by_leaf.items()):
        if not exs:
            continue
        total += len(exs)
        lines.append(f"## PDF leaf {leaf} (doc p. {leaf - 6})")
        lines.append("")
        for e in exs:
            lines.append(f"- `{e}`")
        lines.append("")
    lines.insert(3, f"**Total unique marked lines:** {total}")
    lines.insert(4, "")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {path} total_lines={total}")


def verify_threshold(md: str) -> None:
    checks = [
        ("ˈThis is the ˎbedroom", "1.1.3 LF bedroom"),
        ("ˋThis is the ·bedroom", "1.3.1 contrastive HF This + mid bedroom"),
        ("The ˈtrain has ˎleft", "1.2.1 train LF"),
        ("The ·train ˋhas ·left", "1.3.1 train HF has + mid"),
        ("the ˎowner", "1.1.4 owner LF"),
        ("the ·owner", "BAD owner mid"),
        ("my ˎdog", "dog LF"),
        ("my ·dog", "BAD dog mid"),
        ("ˈNo it ˇisn", "1.3.2 FR isn"),
        ("ˈNo it ˋisn", "BAD HF isn"),
        ("The ·train ˋhas", "1.3.1 train HF has"),
        ("The ·train ˈhas", "BAD train head has"),
        ("The ˇanimal", "animal FR"),
        ("ˊDid you ˎsee him", "1.4.1.1 high rise Did"),
        ("ˈDid you ˎsee him", "BAD head Did"),
        ("ˈPlease can you", "1.4.2.2 head Please"),
        ("ˊPlease can you", "BAD high-rise Please"),
        ("ˎdidn’t they", "1.4.1.3 tag LF"),
        ("ˏdidn’t they", "BAD tag LR invent"),
    ]
    print("--- verify ---")
    for s, label in checks:
        print(f"  {label}: count={md.count(s)}")


def process_threshold() -> int:
    """Returns 0 on residual PASS, 1 on residual FAIL."""
    pdf = ROOT / "input/cefr-threshold-1990/source.pdf"
    md_path = ROOT / "output/cefr-threshold-1990/Threshold_1990.md"
    ov = ROOT / "work/cefr-threshold-1990/page_overrides"
    print("=== THRESHOLD native full pass ===")
    by_leaf = collect_gold(pdf, THR_LEAVES)
    leaves_with = sum(1 for v in by_leaf.values() if v)
    n_ex = sum(len(v) for v in by_leaf.values())
    print(f"leaves_with_marks={leaves_with} examples={n_ex}")
    gmap = gold_map(by_leaf)
    # Multi-form skeletons must not live in gmap (section locks only)
    try:
        from gold_intonation_locks import MULTIFORM_EXACT_SKELETONS, strip_skel

        for k in list(gmap.keys()):
            if k in MULTIFORM_EXACT_SKELETONS:
                del gmap[k]
    except ImportError:
        pass
    print(f"gold_map size={len(gmap)}")

    md = md_path.read_text(encoding="utf-8")
    md, n1, n2 = patch_text(md, gmap)
    md, n3 = force_contrastive_fixes(md)
    # Hard gold lock pass so native fuzzy map cannot re-break 1.1.3 / 1.3.1
    fails: list[str] | None = None
    try:
        from gold_intonation_locks import apply_section_locks, residual_assertions

        md, lock_ops = apply_section_locks(md)
        print(f"gold locks: {lock_ops}")
        fails = residual_assertions(md)
    except ImportError:
        residual_assertions = None  # type: ignore
    md_path.write_text(md, encoding="utf-8")
    print(f"product MD: blockquote/line={n1} systematic={n2} contrastive={n3}")
    verify_threshold(md)
    if fails is not None:
        print("residual assertions:", "PASS" if not fails else fails)

    n_ov = patch_overrides(ov, by_leaf, gmap)
    print(f"overrides patched: {n_ov}")

    dump = ROOT / "docs/vision_extract/INTONATION_NATIVE_DUMP_THRESHOLD.md"
    write_dump(dump, by_leaf, "Native PDF-layer intonation — Threshold 1990 (full primary)")

    # samples dump for hires work dir
    samples = ROOT / "work/cefr-threshold-1990/intonation_hires/native_full_pass.txt"
    samples.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for leaf, exs in sorted(by_leaf.items()):
        if not exs:
            continue
        lines.append(f"===== leaf {leaf} doc {leaf-6} ({len(exs)}) =====")
        lines.extend(exs)
        lines.append("")
    samples.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {samples}")
    return 0 if not fails else 1


def process_waystage_text_if_any() -> None:
    pdf = ROOT / "input/cefr-waystage-1990/source.pdf"
    print("=== WAYSTAGE text-layer probe ===")
    doc = fitz.open(pdf)
    total_chars = 0
    markish = 0
    for leaf in WAY_LEAVES:
        if leaf > doc.page_count:
            continue
        t = doc[leaf - 1].get_text("text")
        total_chars += len(t.strip())
        if has_pdf_tone_encoding(t):
            markish += 1
    print(f"waystage primary leaves text_chars={total_chars} markish_leaves={markish}")
    if total_chars < 500:
        print("Waystage is image PDF — native convert N/A; use Vision overrides.")
        doc.close()
        return
    by_leaf = collect_gold(pdf, WAY_LEAVES)
    gmap = gold_map(by_leaf)
    md_path = ROOT / "output/cefr-waystage-1990/Waystage_1990.md"
    if md_path.exists() and gmap:
        md = md_path.read_text(encoding="utf-8")
        md, n1, n2 = patch_text(md, gmap)
        md_path.write_text(md, encoding="utf-8")
        print(f"waystage product: bq={n1} sys={n2}")
    ov = ROOT / "work/cefr-waystage-1990/page_overrides"
    if ov.exists():
        patch_overrides(ov, by_leaf, gmap)
    dump = ROOT / "docs/vision_extract/INTONATION_NATIVE_DUMP_WAYSTAGE.md"
    write_dump(dump, by_leaf, "Native PDF-layer intonation — Waystage 1990")
    doc.close()


def main() -> None:
    import sys

    rc = process_threshold()
    process_waystage_text_if_any()
    if rc != 0:
        print("DONE full_intonation_pass with RESIDUAL FAIL", file=sys.stderr)
        sys.exit(rc)
    print("DONE full_intonation_pass")


if __name__ == "__main__":
    main()
