#!/usr/bin/env python3
"""Merge intonation example lines from page_overrides into product MD.

Safer than whole-page restitch: only replaces lines whose letter-skeleton
matches and that carry tone marks in the override. Preserves product density.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TONES = re.compile(r"[ˈˎˋˏˊˇ·]")


def strip_marks(s: str) -> str:
    # Prefer shared strip_skel (normalizes curly ’ → ' before strip)
    try:
        from gold_intonation_locks import strip_skel

        return strip_skel(s)
    except ImportError:
        s = s.replace("\u2019", "'").replace("\u2018", "'")
        s = re.sub(r"[ˈˎˋˏˊˇ·ˌ'`´,.\"|\$]+", "", s)
        s = re.sub(r"[^A-Za-z0-9]+", " ", s).lower().strip()
        return re.sub(r"\s+", " ", s)


def clean_override_line(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("<!--"):
        return None
    # strip blockquote / bullets / bold wrappers for matching body
    body = re.sub(r"^>\s*", "", s)
    body = re.sub(r"^\*+|\*+$", "", body).strip()
    if not TONES.search(body):
        return None
    if len(body) < 4 or len(body) > 160:
        return None
    return body


def collect_override_golds(ov_dir: Path, leaves: list[int]) -> dict[str, str]:
    gmap: dict[str, str] = {}
    for leaf in leaves:
        path = ov_dir / f"page_{leaf:03d}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        # prefer body lines over <!-- cat: --> which can be truncated
        for line in text.splitlines():
            if line.strip().startswith("<!-- cat:"):
                m = re.match(r"<!-- cat:\s*(.*?)\s*-->", line.strip())
                if m and TONES.search(m.group(1)):
                    body = m.group(1).strip()
                    if len(body) < 120:
                        k = strip_marks(body)
                        if len(k) >= 5:
                            # cat is secondary; don't overwrite body golds
                            gmap.setdefault(k, body)
                continue
            body = clean_override_line(line)
            if not body:
                continue
            k = strip_marks(body)
            if len(k) < 5:
                continue
            # body wins over cat
            gmap[k] = body
    return gmap


# Skeletons that have multiple legitimate markings (LF vs contrastive, etc.)
# Letter-skeleton merge MUST NOT collapse these — section-aware restore only.
# Import shared set when available; keep local fallback for standalone import.
try:
    from gold_intonation_locks import PROTECTED_SKELETONS as _SHARED_PROT

    PROTECTED_SKELETONS = set(_SHARED_PROT)
except ImportError:
    PROTECTED_SKELETONS = {
        strip_marks(s)
        for s in [
            "This is the bedroom",
            "The train has left",
            "No it isnt",
            "No it isn't",
            "Yes you did",
            "Did you see him",
            "You saw him",
            "They lost the match didnt they",
            "Please can you tell me the way to the station",
            "The animal over there is my dog",
            "He is the owner of the restaurant",
        ]
    }


def merge_into_md(md: str, gmap: dict[str, str]) -> tuple[str, int]:
    n = 0

    def repl(m: re.Match) -> str:
        nonlocal n
        prefix, body = m.group(1), m.group(2).strip()
        bare = re.sub(r"^\*+|\*+$", "", body).strip()
        key = strip_marks(bare)
        if key in PROTECTED_SKELETONS:
            return m.group(0)
        if key in gmap:
            g = gmap[key]
            if g != bare and TONES.search(g):
                n += 1
                if body.startswith("*") and body.endswith("*"):
                    return f"{prefix}*{g}*"
                return f"{prefix}{g}"
        return m.group(0)

    # blockquotes
    md = re.sub(r"^(>\s*)(.+)$", repl, md, flags=re.M)
    # bare tone-leading lines
    md = re.sub(
        r"^([ \t]*)([ˈˎˋˏˊˇ·].+)$",
        repl,
        md,
        flags=re.M,
    )
    # inline "as in: …" fragments that are full lines
    md = re.sub(
        r"^([ \t]*)((?:as in:\s*)?.{0,20}[ˈˎˋˏˊˇ·].+)$",
        repl,
        md,
        flags=re.M,
    )
    return md, n


def parse_leaves(s: str) -> list[int]:
    out: list[int] = []
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--job", default="cefr-threshold-1990")
    ap.add_argument("--out", default="Threshold_1990.md")
    ap.add_argument("--leaves", required=True)
    args = ap.parse_args()
    leaves = parse_leaves(args.leaves)
    ov = ROOT / "work" / args.job / "page_overrides"
    md_path = ROOT / "output" / args.job / args.out
    gmap = collect_override_golds(ov, leaves)
    print(f"gold map from overrides: {len(gmap)} lines, leaves={leaves[0]}-{leaves[-1]}")
    md = md_path.read_text(encoding="utf-8")
    md2, n = merge_into_md(md, gmap)
    # Always re-apply section-aware gold locks so merge cannot re-break 1.1.3/1.3.1
    try:
        from gold_intonation_locks import apply_section_locks, residual_assertions

        md2, lock_ops = apply_section_locks(md2)
        print(f"gold locks after merge: {lock_ops or ['noop']}")
    except ImportError:
        residual_assertions = None  # type: ignore
        print("gold_intonation_locks unavailable — merge only")
    md_path.write_text(md2, encoding="utf-8")
    print(f"merged replacements: {n}")
    # sample needles for ch7-8
    for s in [
        "ˈHave you ·got a ˎtelephone",
        "The ˇbedrooms",
        "In ˇour ·part",
        "for ˇthat ·job",
        "ˈ6ˎ8",
        "ˈThis is the ˎbedroom",
        "ˋThis is the ·bedroom",
        "The ·train ˋhas ·left",
        "The ˈtrain has ˎleft",
        "The ·train ˈhas ·left",
        "ˇisn",
    ]:
        print(f"  {s!r}: {md2.count(s)}")
    if residual_assertions:
        fails = residual_assertions(md2)
        print("residual:", "PASS" if not fails else fails)


if __name__ == "__main__":
    main()
